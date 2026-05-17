import cv2
import time
import pyautogui
from hand_tracker import HandTracker
from gesture_controller import GestureController


def main():
    CAMERA_INDEX = 0
    FRAME_WIDTH = 640
    FRAME_HEIGHT = 480
    FRAME_MARGIN = 80
    SMOOTHING = 0.35
    CLICK_COOLDOWN = 0.4
    PINCH_THRESHOLD = 40
    SENSITIVITY = 1.0
    MAX_HANDS = 1
    SHOW_HUD = True

    screen_w, screen_h = pyautogui.size()
    print(f"[INFO] Screen resolution: {screen_w} x {screen_h}")

    cap = cv2.VideoCapture(CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

    if not cap.isOpened():
        print("[ERROR] Cannot open webcam. Check your camera connection.")
        return

    actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"[INFO] Webcam resolution: {actual_w} x {actual_h}")

    tracker = HandTracker(
        max_hands=MAX_HANDS,
        detection_conf=0.7,
        tracking_conf=0.7,
    )

    controller = GestureController(
        screen_w=screen_w,
        screen_h=screen_h,
        frame_w=actual_w,
        frame_h=actual_h,
        frame_margin=FRAME_MARGIN,
        smoothing=SMOOTHING,
        click_cooldown=CLICK_COOLDOWN,
        pinch_threshold=PINCH_THRESHOLD,
        sensitivity=SENSITIVITY,
    )

    prev_time = time.time()
    fps = 0

    print("[INFO] Hand2Cursor is running. Press 'q' to quit.")
    print("[INFO] Move your index finger to control the cursor.")
    print("[INFO] Pinch thumb+index = Left Click")
    print("[INFO] Double pinch (thumb+index + thumb+middle) = Right Click")

    while True:
        success, frame = cap.read()
        if not success:
            print("[WARNING] Failed to read frame from webcam.")
            break

        frame = cv2.flip(frame, 1)
        hands = tracker.detect(frame)
        tracker.draw_landmarks(frame)

        if hands:
            hand = hands[0]
            action = controller.update(hand, frame=frame)

            if SHOW_HUD:
                controller.draw_hud(frame, hand)

        curr_time = time.time()
        fps = 1.0 / (curr_time - prev_time) if (curr_time - prev_time) > 0 else 0
        prev_time = curr_time

        cv2.putText(frame, f"FPS: {int(fps)}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        cv2.imshow("Hand2Cursor", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("[INFO] Quitting...")
            break

    cap.release()
    cv2.destroyAllWindows()
    tracker.release()
    print("[INFO] Hand2Cursor stopped.")


if __name__ == "__main__":
    main()
