# import cv2
# import mediapipe as mp
# import subprocess
# import time
# def main():
#     # Initialize MediaPipe
#     mp_hands = mp.solutions.hands  
#     mp_drawing = mp.solutions.drawing_utils

#     # Configuration
#     BASE_SCROLL_THRESHOLD = 75  
#     BASE_SWIPE_THRESHOLD = 80
#     NEUTRAL_ZONE = 15  # Pixel buffer for neutral position
#     COOLDOWN = 0.5  # Seconds between commands

#     cap = cv2.VideoCapture(0)
#     prev_y = prev_x = None
#     last_command_time = 0

#     with mp_hands.Hands(
#             max_num_hands=1,
#             min_detection_confidence=0.6,
#             min_tracking_confidence=0.6) as hands:

#         while cap.isOpened():
#             success, image = cap.read()
#             if not success:
#                 continue
            
#             # Mirror and convert
#             image = cv2.flip(image, 1)
#             image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
#             results = hands.process(image_rgb)

#             if results.multi_hand_landmarks:
#                 hand_landmarks = results.multi_hand_landmarks[0]
#                 mp_drawing.draw_landmarks(image, hand_landmarks, mp_hands.HAND_CONNECTIONS)

#                 # Get current finger position
#                 index_finger_tip_y = hand_landmarks.landmark[8].y * image.shape[0]
#                 index_finger_tip_x = hand_landmarks.landmark[8].x * image.shape[1]

#                 # Dynamic threshold based on hand size (distance from camera)
#                 wrist_to_tip = abs(hand_landmarks.landmark[0].y - hand_landmarks.landmark[8].y)
#                 dynamic_scroll = BASE_SCROLL_THRESHOLD * (1 + wrist_to_tip)
#                 dynamic_swipe = BASE_SWIPE_THRESHOLD * (1 + wrist_to_tip)

#                 if prev_y is not None and prev_x is not None:
#                     dy = index_finger_tip_y - prev_y
#                     dx = index_finger_tip_x - prev_x

#                     current_time = time.time()
#                     if current_time - last_command_time > COOLDOWN:
#                         # Neutral position check
#                         if abs(dy) < NEUTRAL_ZONE and abs(dx) < NEUTRAL_ZONE:
#                             print("Neutral position - no action")
#                         else:
#                             if abs(dy) > abs(dx):  # Vertical movement
#                                 if dy > dynamic_scroll:
#                                     print("Scroll Down")
#                                     subprocess.run(["adb", "shell", "input", "swipe", "500", "1000", "500", "500"])
#                                     last_command_time = current_time
#                                 elif dy < -dynamic_scroll:
#                                     print("Scroll Up")
#                                     subprocess.run(["adb", "shell", "input", "swipe", "500", "500", "500", "1000"])
#                                     last_command_time = current_time
#                             else:  # Horizontal movement
#                                 if dx > dynamic_swipe:
#                                     print("Swipe Right")
#                                     subprocess.run(["adb", "shell", "input", "swipe", "200", "500", "800", "500"])
#                                     last_command_time = current_time
#                                 elif dx < -dynamic_swipe:
#                                     print("Swipe Left")
#                                     subprocess.run(["adb", "shell", "input", "swipe", "800", "500", "200", "500"])
#                                     last_command_time = current_time

#                 prev_y, prev_x = index_finger_tip_y, index_finger_tip_x

#             # Display dynamic threshold info
#             cv2.putText(image, f"Scroll: {int(dynamic_scroll)}px", (10, 30), 
#                     cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
#             cv2.putText(image, f"Swipe: {int(dynamic_swipe)}px", (10, 60), 
#                     cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

#             cv2.imshow('Gesture Control', image)
#             if cv2.waitKey(5) & 0xFF == 27:
#                 break

#     cap.release()
#     cv2.destroyAllWindows()

# if __name__ == '__main__':
#     main()

import cv2
import mediapipe as mp
import subprocess
import time

# Initialize MediaPipe
mp_hands = mp.solutions.hands  
mp_drawing = mp.solutions.drawing_utils

# Configuration
SCROLL_THRESHOLD = 85  # Minimum pixel movement for scroll
SWIPE_THRESHOLD = 85   # Minimum pixel movement for swipe
NEUTRAL_ZONE = 30      # Dead zone where no action occurs
COOLDOWN = 0.5         # Minimum time between actions (seconds)

cap = cv2.VideoCapture(0)
prev_y = prev_x = None
last_action_time = 0

with mp_hands.Hands(
        max_num_hands=1,
        min_detection_confidence=0.6,
        min_tracking_confidence=0.6) as hands:

    while cap.isOpened():
        success, image = cap.read()
        if not success:
            continue
        
        # Mirror and convert
        image = cv2.flip(image, 1)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = hands.process(image_rgb)

        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]
            mp_drawing.draw_landmarks(image, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            # Get current finger position (corrected x-coordinate)
            index_finger_tip_y = hand_landmarks.landmark[8].y * image.shape[0]
            index_finger_tip_x = hand_landmarks.landmark[8].x * image.shape[1]  # Fixed from previous version

            if prev_y is not None and prev_x is not None:
                current_time = time.time()
                dy = index_finger_tip_y - prev_y
                dx = index_finger_tip_x - prev_x

                # Only check for actions if cooldown has passed
                if current_time - last_action_time > COOLDOWN:
                    # Neutral position check - no action if movement is small
                    
                
                        if abs(dy) > abs(dx):  # Vertical movement dominant
                            if dy > SCROLL_THRESHOLD:
                                print("Scroll Down")
                                subprocess.run(["adb", "shell", "input", "swipe", "500", "1000", "500", "500"])
                                last_action_time = current_time
                            elif dy < -SCROLL_THRESHOLD:
                                print("Scroll Up")
                                subprocess.run(["adb", "shell", "input", "swipe", "500", "500", "500", "1000"])
                                last_action_time = current_time
                        else:  # Horizontal movement dominant
                            if dx > SWIPE_THRESHOLD:
                                print("Swipe Right")
                                subprocess.run(["adb", "shell", "input", "swipe", "200", "500", "800", "500"])
                                last_action_time = current_time
                            elif dx < -SWIPE_THRESHOLD:
                                print("Swipe Left")
                                subprocess.run(["adb", "shell", "input", "swipe", "800", "500", "200", "500"])
                                last_action_time = current_time

            prev_y = index_finger_tip_y
            prev_x = index_finger_tip_x

        # Display neutral zone info
      
        cv2.putText(image, f"Cooldown: {COOLDOWN}s", (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(image, "ESC to quit", (10, image.shape[0]-10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        cv2.imshow('Hand Gesture Control', image)
        if cv2.waitKey(5) & 0xFF == 27:
            break

cap.release()
cv2.destroyAllWindows()