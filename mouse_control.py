'''   import essential libraries and modules  '''

import cv2                 # for cam and vision
import mediapipe as mp     # for hand detection and traking
import pyautogui           # for mouse control on desktop
import time                # for time measurement 
import numpy as np         # for maths
import sys                 # system utilities 

'''  Initialize MediaPipe  '''

mp_hands = mp.solutions.hands               # mediapipe hand-traking model  
mp_drawing = mp.solutions.drawing_utils     # mediapipe drawing tools

''' config '''

MOUSE_SENSITIVITY = 3.5         # Pointer movement speed
CLICK_DISTANCE = 0.04           # Distance threshold for click detection (4% of frame width)
CLICK_COOLDOWN = 0.3            # Minimum time between clicks
MOVEMENT_SMOOTHING = 0.2        # Smoothing factor for mouse movements (0-1)

''' class for implementaion '''

class DesktopMouse:
    def __init__(self):
        self.screen_width, self.screen_height = pyautogui.size()  # gets your screen resolution (e.g - 1920 x 1080)
        self.prev_x = None                                        # previous mouse position on x axis
        self.prev_y = None                                        # previous mouse position on y axis
        self.last_click_time = 0                                  # timestamp for last click
        self.smoothed_x = None                                    # x position - smoothed (for stability)
        self.smoothed_y = None                                    # y position - smoothed (for stability)
        
        pyautogui.FAILSAFE = False                                # disabled fail safe (to prevent crashes)                              
        pyautogui.PAUSE = 0.01                                    # delay between pyautogui actions


    
    def handle_gestures(self, index_tip, thumb_tip):

        ''' Process all hand gestures for desktop control '''

        current_time = time.time()  # save current time in variable
        
        # Calculate distance between fingers (normalized 0-1)

        distance = np.sqrt((index_tip.x - thumb_tip.x)**2 + 
                         (index_tip.y - thumb_tip.y)**2)
        
        ''' Convert hand position to screen coordinates according resolution eg. if screen width is 1920....
        and index_tip.x = 0.2 then x_pos = 384 '''

        x_pos = int(index_tip.x * self.screen_width)
        y_pos = int(index_tip.y * self.screen_height)
        
        # Apply smoothing to mouse movements
        '''in else block : if we have last position of x and y then we will add value according hyper-parameter
         here, MOVEMENT_SMOOTHING = 2 so, 20% of new position + 80% of previous position'''

        if self.smoothed_x is None: 
            self.smoothed_x = x_pos      # for first movement 
            self.smoothed_y = y_pos
        else:
            self.smoothed_x = MOVEMENT_SMOOTHING * x_pos + (1 - MOVEMENT_SMOOTHING) * self.smoothed_x
            self.smoothed_y = MOVEMENT_SMOOTHING * y_pos + (1 - MOVEMENT_SMOOTHING) * self.smoothed_y
        
        # Move mouse pointer (with smoothing)

        pyautogui.moveTo(int(self.smoothed_x), int(self.smoothed_y), duration=0.01)
        
        # Click detection (finger touch)

        ''' if normlized distance of both finger tip is less then parameter CLICK_DISTANCE (4% of Screen)
        then we consider it as click , new click will only consider after given time in CLICK_COOLDOWN'''

        if distance < CLICK_DISTANCE and current_time - self.last_click_time > CLICK_COOLDOWN:
            pyautogui.click() 
            print(f"Click at ({int(self.smoothed_x)}, {int(self.smoothed_y)})")
            self.last_click_time = current_time 
            time.sleep(0.1)  # Small delay after click

def main():

    # Initialize webcam

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():                   # if not web came then exit           
        print("Error: Could not open webcam")
        sys.exit(1)
    
    # Set camera resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    
    # Initialize mouse controller
    mouse = DesktopMouse()
    
    with mp_hands.Hands(
            max_num_hands=1,               # you can onlu use one hand
            min_detection_confidence=0.7,  # 0-1  0 < 0.1 < traking and detection gets better and strict < 1
            min_tracking_confidence=0.7) as hands:
        
        '''while camera is opened (main loop for frames)'''
        while cap.isOpened():

            try:
                success, image = cap.read()                # read each frame
                if not success:                            # if not then move to next frame after 0.1s
                    print("Warning: Frame read failed") 
                    time.sleep(0.1)
                    continue
                
                # Mirror and convert colors (opencv detects in BGR , mediapipe works with RGB)
                image = cv2.flip(image, 1)
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                
                # Process hand landmarks
                results = hands.process(image_rgb)
                
                '''if hands are detected'''

                if results.multi_hand_landmarks:
                    hand_landmarks = results.multi_hand_landmarks[0]                            # get hand landmarks
                    mp_drawing.draw_landmarks(image, hand_landmarks, mp_hands.HAND_CONNECTIONS) # draw landmarks    
                    
                    # Get finger positions
                    index_tip = hand_landmarks.landmark[8]  # index finger 
                    thumb_tip = hand_landmarks.landmark[4]  # thumb 
                    
                    # Draw connection line between fingers
                    cv2.line(image, 
                            (int(index_tip.x * image.shape[1]), int(index_tip.y * image.shape[0])),  # from index tip cordinates
                            (int(thumb_tip.x * image.shape[1]), int(thumb_tip.y * image.shape[0])),  # to thumb cordinates                 
                            (0, 255, 0), 2)                                                          # green line
                    
                    # Handle gestures , contol the mouse through pyautogui's DesktopMouse class
                    mouse.handle_gestures(index_tip, thumb_tip, image.shape[1], image.shape[0])
                
                # Display status and instructions
                status_text = "Desktop Mouse Control"
                cv2.putText(image, status_text, (20, 40), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                help_text = "Touch thumb and index to click"
                cv2.putText(image, help_text, (20, 80),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                # Show click distance threshold
                cv2.putText(image, f"Click Threshold: {CLICK_DISTANCE*100:.1f}%", (20, 120),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                cv2.imshow('Desktop Mouse Control', image)
                if cv2.waitKey(5) & 0xFF == 27:
                    break
            
            except Exception as e:
                print(f"Error in main loop: {str(e)}")
                time.sleep(0.1)
                continue
    
    cap.release()
    cv2.destroyAllWindows()

'''execute main loop'''
if __name__ == "__main__":
    main()