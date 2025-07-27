import speech_recognition as sr             # for speech recognition
import subprocess                           # for running ADB commands   
import time                                 # for timing operations            
import threading                            # for running commands background
import sys                                  # for system operations
import wave                                 # for handling audio files
import os                                   # for file and directory operations
from datetime import datetime               # for timestamping audio files

''' main class '''
class AndroidVoiceController:

    def __init__(self):
        self.recognizer = sr.Recognizer()  # initialize speech recognizer 
        self.microphone = sr.Microphone()  # initialize microphone associated with device
        self.listening = False             # control for listining loop

        '''origin of pixels(0,0) starts from top-left corner of screen'''
        self.commands = {
            "scroll up": ["adb", "shell", "input", "swipe", "500", "1500", "500", "500"],       # y axis - from 1500p (bottom) to 500p (up) 
            "scroll down": ["adb", "shell", "input", "swipe", "500", "500", "500", "1500"],     # y axis - from 500p (up) to 1500p (bottom) 
            "swipe left": ["adb", "shell", "input", "swipe", "1000", "500", "200", "500"],      # x axis - from 200p (left) to 1000p (right) 
            "swipe right": ["adb", "shell", "input", "swipe", "200", "500", "1000", "500"],     # x axis - from 1000p (right) to 1500p (left) 
            "stop": None        # command for exit
        }

        '''improved accuracy of recognization'''
        self.recognizer.dynamic_energy_threshold = False    # use fixed threshold
        self.recognizer.energy_threshold = 400              # Default is 300, increased for better rejection
        self.recognizer.pause_threshold = 1.0               # Longer pause before considering speech ended
        self.recognizer.phrase_threshold = 0.3              # Minimum audio length to consider

        '''audio debugging and logging'''
        self.debug_audio = True                             # enable audio debugging
        self.audio_log_dir = "audio_logs"                   # directory to save audio logs
        os.makedirs(self.audio_log_dir, exist_ok=True)      # make directory if not exits

    '''Save audio data for debugging recognition issues'''
    def save_audio_debug(self, audio_data, prefix=""):
        
        if not self.debug_audio:    # if not detected
            return
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")          # save timestamp for logging
        filename = f"{self.audio_log_dir}/{prefix}{timestamp}.wav"    # file name with command and timestamp

        '''save file'''
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(1)             # mono audio 
            wf.setsampwidth(2)             # 2bytes per sample
            wf.setframerate(16000)         # 16kHz waves   
            wf.writeframes(audio_data.get_wav_data())

    '''Execute ADB command'''
    def run_adb(self, command):
        # run the command with timeout
        try:
            result = subprocess.run(command, 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=3)
            if result.returncode == 0:                        # if executed
                print(f" Executed: {' '.join(command)}")
                return True
            print(f"Command failed: {result.stderr.strip()}") # else why not executed
        except Exception as e:
            print(f"Error executing command: {str(e)}")       # other execptions
        return False

     '''voice command listener with multiple recognition strategies'''
    def listen_commands(self):

        # use associated microphone
        with self.microphone as source:
            print("\n Calibrating microphone... (Please stay silent)")        
            self.recognizer.adjust_for_ambient_noise(source, duration=3)        # adjust the recognizer for backgroung noise

            # instructions 
            print("Ready. Speak clearly 🔽")
            print("'scroll up', 'scroll down', 'swipe left', 'swipe right', or 'stop'\n")

            # loop for listening if true(till stop command) 
            while self.listening:
                try:
                    print("Listening..", end='\r')
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=3)   # timeout : raise waitTimeoutError if speech not start in 5 seconds
                                                                                             # phrase_time_limit : words pr listening of first 3 seconds will be counted
                    print("                                ", end='\r')  # Clear line
                    
                    # Save audio for debugging
                    self.save_audio_debug(audio, "command_")
                    
                    # Try multiple recognition methods
                    command = None
                    try:
                        command = self.recognizer.recognize_google(audio, language="en-US").lower()  # google(online) speech recognizer - higher accuracy 
                    except sr.UnknownValueError:                                                     # if fails or can't detect then 'UnknownValueError'
                        # Fallback to local recognizer if available
                        try:
                            command = self.recognizer.recognize_sphinx(audio).lower()                # CMU sphinx - local recognizer(offline)
                        except:
                            pass

                    # if not recognized 
                    if not command:
                        print(" No speech detected (try speaking louder/closer)")
                        continue

                    # if recognized then print                    
                    print(f"Heard: '{command}'")
                    
                    # Find best matching command 
                    best_match = None
                    best_score = 0
                    for cmd in self.commands:
                        score = self.command_similarity(cmd, command) # execute connamd_similarity function
                        if score > best_score and score > 0.6:  # Minimum 60% match
                            best_score = score
                            best_match = cmd

                    # if command matched (atleast 60%) then execute through adb
                    if best_match:
                        print(f"Matched command: '{best_match}'")
                        if self.commands[best_match]:
                            self.run_adb(self.commands[best_match])

                    # else show avaivable commands
                    else:
                        print("No matching command found")
                        print("Available commands:", ", ".join(self.commands.keys()))

                # after silent 5 sec , speech not detected for 5 seconds
                except sr.WaitTimeoutError:
                    continue

                # other execption
                except Exception as e:
                    print(f" Error: {str(e)}")
                    time.sleep(1)

     '''Calculate similarity between command and heard text using word matching'''
    def command_similarity(self, command, heard_text):
       
        command_words = set(command.split())                        # command words (defined in self.commands) eg.{'scroll','up'}
        heard_words = set(heard_text.split())                       # heard words eg.{'i','want','to','scroll','up'}
        intersection = command_words.intersection(heard_words)      # words that instesect {'scroll','up'}
        return len(intersection) / len(command_words)               # here len(intersection)=2 / len(command_words)=2 = 1 > 0.6 pass 

    def start(self):
        """Start the voice command listener with comprehensive checks"""
      
        try:
            result = subprocess.run(["adb", "devices"], 
                                   capture_output=True, 
                                   text=True, 
                                   timeout=3)
            if "device" not in result.stdout:
                print("\n❌ No Android device found. Please:")
                print("1. Enable USB Debugging in Developer Options")
                print("2. Connect your device via USB")
                print("3. Authorize the connection when prompted")
                print("4. Try 'adb devices' in terminal to verify")
                return False
            
            print("✅ ADB device connected")
            print("\n💡 Tips for better voice recognition:")
            print("- Speak clearly at normal volume")
            print("- Use full commands like 'scroll up'")
            print("- Reduce background noise")
            print("- Position microphone 6-12 inches from your mouth\n")
            
            self.listening = True
            self.thread = threading.Thread(target=self.listen_commands)
            self.thread.daemon = True
            self.thread.start()
            return True
            
        except Exception as e:
            print(f"\n❌ ADB setup error: {str(e)}")
            print("Please ensure ADB is installed and in your PATH")
            print("Download platform-tools from: https://developer.android.com/studio/releases/platform-tools")
            return False

    def stop(self):
        """Stop the voice command listener"""
        self.listening = False
        if hasattr(self, 'thread'):
            self.thread.join(timeout=1)
        print("\n🛑 Voice control stopped")

def main():
    controller = AndroidVoiceController()
    if not controller.start():
        sys.exit(1)
    
    try:
        while controller.listening:
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        controller.stop()

if __name__ == "__main__":
    # Clear console for better visibility
    os.system('cls' if os.name == 'nt' else 'clear')
    print("=== Android Voice Control ===")
    main()
