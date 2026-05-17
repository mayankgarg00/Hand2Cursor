import cv2
import time
import threading
import pyautogui
from flask import Flask, Response, jsonify, send_from_directory
from hand_tracker import HandTracker
from gesture_controller import GestureController

app = Flask(__name__, static_folder='website', static_url_path='')

tracking_active = False
tracking_lock = threading.Lock()
tracker = None
controller = None
cap = None
latest_frame = None
frame_lock = threading.Lock()
current_fps = 0
current_action = 'idle'
error_message = ''

CAMERA_INDEX = 0
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
FRAME_MARGIN = 80
SMOOTHING = 0.35
CLICK_COOLDOWN = 0.4
PINCH_THRESHOLD = 40
SENSITIVITY = 1.0
SHOW_HUD = True


def tracking_loop():
    global tracking_active, tracker, controller, cap, latest_frame, current_fps, current_action, error_message
    error_message = ''

    screen_w, screen_h = pyautogui.size()
    print(f"[INFO] Screen: {screen_w}x{screen_h}")

    cap = None
    for idx in [CAMERA_INDEX, 0, 1, 2]:
        print(f"[INFO] Trying camera index {idx} with DirectShow...")
        test_cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
        if test_cap.isOpened():
            cap = test_cap
            print(f"[INFO] Camera opened on index {idx}")
            break
        test_cap.release()
        print(f"[INFO] Trying camera index {idx} with default backend...")
        test_cap = cv2.VideoCapture(idx)
        if test_cap.isOpened():
            cap = test_cap
            print(f"[INFO] Camera opened on index {idx} (default backend)")
            break
        test_cap.release()

    if cap is None or not cap.isOpened():
        print("[ERROR] Could not open any camera. Check your webcam connection.")
        error_message = 'No camera detected. Check webcam connection and permissions.'
        with tracking_lock:
            tracking_active = False
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

    actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    tracker = HandTracker(max_hands=1, detection_conf=0.7, tracking_conf=0.7)
    controller = GestureController(
        screen_w=screen_w, screen_h=screen_h,
        frame_w=actual_w, frame_h=actual_h,
        frame_margin=FRAME_MARGIN, smoothing=SMOOTHING,
        click_cooldown=CLICK_COOLDOWN, pinch_threshold=PINCH_THRESHOLD,
        sensitivity=SENSITIVITY,
    )

    prev_time = time.time()

    while True:
        with tracking_lock:
            if not tracking_active:
                break

        success, frame = cap.read()
        if not success:
            break

        frame = cv2.flip(frame, 1)
        hands = tracker.detect(frame)
        tracker.draw_landmarks(frame)

        action = 'idle'
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

        current_fps = int(fps)
        current_action = action

        with frame_lock:
            latest_frame = frame.copy()

    cap.release()
    if tracker:
        tracker.release()
    cap = None
    tracker = None
    controller = None


def generate_frames():
    while True:
        with tracking_lock:
            if not tracking_active:
                break

        with frame_lock:
            if latest_frame is None:
                time.sleep(0.03)
                continue
            _, buffer = cv2.imencode('.jpg', latest_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        time.sleep(0.033)


@app.route('/')
def index():
    return send_from_directory('website', 'index.html')


@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/start', methods=['POST'])
def start_tracking():
    global tracking_active
    with tracking_lock:
        if tracking_active:
            return jsonify({'status': 'already_running'})
        tracking_active = True
    t = threading.Thread(target=tracking_loop, daemon=True)
    t.start()
    return jsonify({'status': 'started'})


@app.route('/stop', methods=['POST'])
def stop_tracking():
    global tracking_active
    with tracking_lock:
        tracking_active = False
    return jsonify({'status': 'stopped'})


@app.route('/status')
def status():
    with tracking_lock:
        active = tracking_active
    return jsonify({
        'active': active,
        'fps': current_fps,
        'action': current_action,
        'error': error_message,
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
