import cv2
import mediapipe as mp
import subprocess
import time

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

SCROLL_THRESHOLD = 30  
COOLDOWN_TIME = 0.5  

cap = cv2.VideoCapture(0)
prev_y = None
last_scroll_time = 0

def is_finger_extended(hand_landmarks, finger_tip, finger_pip):
    return hand_landmarks.landmark[finger_tip].y < hand_landmarks.landmark[finger_pip].y

with mp_hands.Hands(
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7) as hands:

    while cap.isOpened():
        success, image = cap.read()
        if not success:
            continue

        image = cv2.flip(image, 1)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = hands.process(image_rgb)

        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]
            mp_drawing.draw_landmarks(image, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            # Check if index and middle fingers are extended
            index_extended = is_finger_extended(hand_landmarks, 8, 6)
            middle_extended = is_finger_extended(hand_landmarks, 12, 10)

            if index_extended and middle_extended:
                index_y = hand_landmarks.landmark[8].y * image.shape[0]
                middle_y = hand_landmarks.landmark[12].y * image.shape[0]

                avg_y = (index_y + middle_y) / 2

                if prev_y is not None:
                    dy = avg_y - prev_y
                    current_time = time.time()

                    if current_time - last_scroll_time > COOLDOWN_TIME:
                        if dy > SCROLL_THRESHOLD:
                            print("Scrolling down")
                            subprocess.run(["adb", "shell", "input", "swipe", "500", "1000", "500", "500"])
                            last_scroll_time = current_time
                        elif dy < -SCROLL_THRESHOLD:
                            print("Scrolling up")
                            subprocess.run(["adb", "shell", "input", "swipe", "500", "500", "500", "1000"])
                            last_scroll_time = current_time

                prev_y = avg_y
            else:
                prev_y = None  # Reset when gesture is not active

        cv2.imshow('Hand Gesture Control', image)
        if cv2.waitKey(5) & 0xFF == 27:
            break

cap.release()
cv2.destroyAllWindows()
