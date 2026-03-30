import cv2
import mediapipe as mp
import pyautogui
import time
import math

# Setup
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(model_complexity=0)
mp_draw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("❌ Camera not detected")
    exit()

game_started = False
last_action_time = 0
cooldown = 0.7


def distance(p1, p2):
    return math.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2)


# 👉 JOIN HANDS TO START
def detect_start(landmarks):
    lw = landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value]
    rw = landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value]

    return distance(lw, rw) < 0.05


# 👉 BODY GESTURES
def detect_gesture(landmarks):
    global last_action_time

    if time.time() - last_action_time < cooldown:
        return None

    lw = landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value]
    rw = landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value]
    ls = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
    rs = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
    nose = landmarks[mp_pose.PoseLandmark.NOSE.value]

    # Jump (both hands up)
    if lw.y < ls.y and rw.y < rs.y:
        last_action_time = time.time()
        return "UP"

    # Move left
    elif lw.y < ls.y:
        last_action_time = time.time()
        return "LEFT"

    # Move right
    elif rw.y < rs.y:
        last_action_time = time.time()
        return "RIGHT"

    # Slide (bend down)
    elif nose.y > ls.y and nose.y > rs.y:
        last_action_time = time.time()
        return "DOWN"

    return None


# 👉 PERFORM ACTION (KEYBOARD SIMULATION)
def perform_action(action):
    if action == "UP":
        pyautogui.press("up")
    elif action == "LEFT":
        pyautogui.press("left")
    elif action == "RIGHT":
        pyautogui.press("right")
    elif action == "DOWN":
        pyautogui.press("down")


# 👉 MAIN LOOP
while True:
    success, frame = cap.read()

    if not success:
        print("❌ Frame not captured")
        continue

    frame = cv2.flip(frame, 1)
    frame = cv2.resize(frame, (640, 480))

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    try:
        result = pose.process(rgb)
    except:
        continue

    if result.pose_landmarks:
        mp_draw.draw_landmarks(frame, result.pose_landmarks, mp_pose.POSE_CONNECTIONS)
        landmarks = result.pose_landmarks.landmark

        # Start detection
        if not game_started:
            if detect_start(landmarks):
                game_started = True
                print("GAME STARTED")

                # Click to focus Chrome window
                pyautogui.click()
                time.sleep(1)

        else:
            action = detect_gesture(landmarks)

            if action:
                print("Action:", action)
                perform_action(action)

    # UI text
    if not game_started:
        cv2.putText(frame, "JOIN HANDS TO START", (30, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    else:
        cv2.putText(frame, "GAME RUNNING", (30, 100),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    cv2.imshow("Pose Controller", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

    time.sleep(0.03)

cap.release()
cv2.destroyAllWindows()