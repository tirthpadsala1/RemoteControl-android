import cv2
import mediapipe as mp
import subprocess

'''for mediapipe hand traking solutoins'''
mp_hands = mp.solutions.hands  

'''drawings for landmarks here for hands'''
mp_drawing = mp.solutions.drawing_utils


'''minimun required pixel movement for scrolling'''
scroll = 85
swipes = 95

'''open webcam'''
cap = cv2.VideoCapture(0)

'''will store previous position of index finger (y-axis),(x-axis)'''
prev_y = None
prev_x = None


with mp_hands.Hands(
        max_num_hands=1, # use only one hand
        min_detection_confidence=0.6, # minimun detection of hand - 60 percent hand should be visible
        min_tracking_confidence=0.6) as hands: # minimun traking 

    '''loop till closed - close manually'''
    while cap.isOpened(): # while camera is opened

        success, image = cap.read() # read frames of camera

        '''if faliure skip to next frame'''
        if not success:
            continue
        
        '''horizontal flip'''
        image = cv2.flip(image, 1)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB) # convert BGR to RGB
        results = hands.process(image_rgb) # detect hands

        '''if hands are detected'''
        if results.multi_hand_landmarks:
            '''draw landmarks'''
            hand_landmarks = results.multi_hand_landmarks[0]
            mp_drawing.draw_landmarks(image, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            '''from normalized to pixel'''           
            index_finger_tip_y = hand_landmarks.landmark[8].y * image.shape[0]
            index_finger_tip_x = hand_landmarks.landmark[8].x * image.shape[0]

            '''if we have previous position'''
            if prev_y is not None and prev_x is not None :
                dy = index_finger_tip_y - prev_y # calculate verticle movement
                dx = index_finger_tip_x - prev_x

                if abs(dy) > abs(dx): # priortize verical movement first
                    if dy > scroll:
                        print("down")
                        subprocess.run(["adb", "shell", "input", "swipe", "500", "500", "500", "1500"])
                    elif dy < -scroll:
                        print("up")
                        subprocess.run(["adb", "shell", "input", "swipe", "500", "1500", "500", "500"]),
            
                else:
                    if dx > swipes:
                        print("left")
                        subprocess.run(["adb", "shell", "input", "swipe", "200", "500", "1000", "500"])

                    elif dx < -swipes:
                        print("right")
                        subprocess.run(["adb","shell","input","swipe","1000","500","200","500"])


                

            prev_y = index_finger_tip_y
            prev_x = index_finger_tip_x

        cv2.imshow('Hand Gesture Control', image)
        if cv2.waitKey(5) & 0xFF == 27:
            break

cap.release()
cv2.destroyAllWindows()


