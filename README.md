# Hand2Cursor — Touchless Cursor Navigation

A revolutionary hands-free cursor controller that converts your standard webcam stream into precise mouse movements. Built on top of Python, it utilizes computer vision techniques to detect hand landmarks and translates them instantly to on-screen navigation.

## Overview

Hand2Cursor seamlessly captures video input, locates 21 unique points on the user's hand via a machine learning model, and decodes specific gestures into system-level mouse commands. By pointing the index finger, you drive the cursor; by pinching, you perform clicks; and by clenching a fist, you can trigger drag operations.

## Gesture Mapping

| Gesture | Action |
|---|---|
| Index finger pointing | Cursor movement |
| Thumb + index pinch | Left click |
| Thumb + index + middle pinch | Right click |
| Closed fist | Drag (experimental) |
| Press Q on keyboard | Exit application |

## Project Layout

```
Hand2Cursor/
├── main.py                 Entry point and main loop
├── hand_tracker.py          MediaPipe hand detection wrapper
├── gesture_controller.py    Gesture-to-action translation engine
├── hand_landmarker.task     Pre-trained MediaPipe model
├── requirements.txt         Python package dependencies
├── website/                 Project showcase website
│   ├── index.html
│   ├── style.css
│   ├── script.js
│   └── assets/
└── README.md
```

## Requirements

- Python 3.8+
- Functional webcam
- Windows, macOS, or Linux

## Setup

```bash
cd Hand2Cursor
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Download the `hand_landmarker.task` model from the [MediaPipe solutions page](https://developers.google.com/mediapipe/solutions/vision/hand_landmarker) and place it in the project root.

## Running

```bash
python main.py
```

## Tunable Parameters

These are defined at the top of `main.py`:

| Parameter | Default | Purpose |
|---|---|---|
| CAMERA_INDEX | 0 | Webcam device selector |
| FRAME_MARGIN | 80 | Active tracking region inset (px) |
| SMOOTHING | 0.35 | EMA filter strength (lower = smoother) |
| CLICK_COOLDOWN | 0.4 | Minimum gap between clicks (seconds) |
| PINCH_THRESHOLD | 40 | Finger distance to register pinch (px) |
| SENSITIVITY | 1.0 | Cursor movement multiplier |

## Processing Pipeline

1. **Frame Acquisition** — OpenCV reads and horizontally mirrors each webcam frame
2. **Landmark Extraction** — MediaPipe HandLandmarker identifies 21 points on the detected hand
3. **Gesture Classification** — Euclidean distances between fingertips determine the active gesture
4. **Coordinate Transformation** — Finger position within a virtual boundary maps to screen coordinates via normalization
5. **Smoothed Execution** — An EMA filter stabilizes the cursor, then PyAutoGUI executes the corresponding mouse event

## Dependencies

| Package | Role |
|---|---|
| opencv-python | Frame capture and image manipulation |
| mediapipe | ML-based hand landmark inference |
| pyautogui | Cross-platform mouse event dispatch |
| numpy | Array math and coordinate clamping |

## Troubleshooting

| Problem | Fix |
|---|---|
| Camera not detected | Try CAMERA_INDEX = 1 or 2 |
| Cursor shakes too much | Reduce SMOOTHING to 0.2 |
| Clicks repeat rapidly | Raise CLICK_COOLDOWN to 0.6 |
| Pinch not registering | Increase PINCH_THRESHOLD to 50 |
| Low frame rate | Lower resolution or close background apps |

## License

Released under the MIT License.
