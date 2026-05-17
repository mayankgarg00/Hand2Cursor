import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import math
import numpy as np


class HandTracker:

    WRIST = 0
    THUMB_CMC = 1
    THUMB_MCP = 2
    THUMB_IP = 3
    THUMB_TIP = 4
    INDEX_MCP = 5
    INDEX_PIP = 6
    INDEX_DIP = 7
    INDEX_TIP = 8
    MIDDLE_MCP = 9
    MIDDLE_PIP = 10
    MIDDLE_DIP = 11
    MIDDLE_TIP = 12
    RING_MCP = 13
    RING_PIP = 14
    RING_DIP = 15
    RING_TIP = 16
    PINKY_MCP = 17
    PINKY_PIP = 18
    PINKY_DIP = 19
    PINKY_TIP = 20

    HAND_CONNECTIONS = [
        (0, 1), (1, 2), (2, 3), (3, 4),
        (0, 5), (5, 6), (6, 7), (7, 8),
        (5, 9), (9, 10), (10, 11), (11, 12),
        (9, 13), (13, 14), (14, 15), (15, 16),
        (13, 17), (0, 17), (17, 18), (18, 19), (19, 20)
    ]

    def __init__(self, max_hands=1, detection_conf=0.7, tracking_conf=0.7):
        self.max_hands = max_hands
        self.detection_conf = detection_conf
        self.tracking_conf = tracking_conf

        base_options = python.BaseOptions(model_asset_path='hand_landmarker.task')

        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            num_hands=self.max_hands,
            min_hand_detection_confidence=self.detection_conf,
            min_hand_presence_confidence=self.tracking_conf,
            min_tracking_confidence=self.tracking_conf,
            running_mode=vision.RunningMode.IMAGE
        )

        self.detector = vision.HandLandmarker.create_from_options(options)
        self._results = None

    def detect(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        self._results = self.detector.detect(mp_image)

        all_hands = []

        if self._results and self._results.hand_landmarks:
            h, w, _ = frame.shape

            for hand_landmarks in self._results.hand_landmarks:
                hand = []
                for idx, lm in enumerate(hand_landmarks):
                    px, py = int(lm.x * w), int(lm.y * h)
                    hand.append((idx, px, py))
                all_hands.append(hand)

        return all_hands

    def draw_landmarks(self, frame, hand_index=None,
                       landmark_color=(0, 255, 255),
                       connection_color=(0, 200, 0),
                       thickness=2):
        if self._results and self._results.hand_landmarks:
            hands_to_draw = self._results.hand_landmarks

            if hand_index is not None:
                if hand_index < len(hands_to_draw):
                    hands_to_draw = [hands_to_draw[hand_index]]
                else:
                    return frame

            h, w, _ = frame.shape

            for hand_landmarks in hands_to_draw:
                px_landmarks = [(int(lm.x * w), int(lm.y * h)) for lm in hand_landmarks]

                for conn in self.HAND_CONNECTIONS:
                    pt1 = px_landmarks[conn[0]]
                    pt2 = px_landmarks[conn[1]]
                    cv2.line(frame, pt1, pt2, connection_color, thickness)

                for pt in px_landmarks:
                    cv2.circle(frame, pt, thickness + 2, landmark_color, cv2.FILLED)

        return frame

    @staticmethod
    def distance(point_a, point_b):
        return math.hypot(point_b[1] - point_a[1], point_b[2] - point_a[2])

    @staticmethod
    def midpoint(point_a, point_b):
        return ((point_a[1] + point_b[1]) // 2, (point_a[2] + point_b[2]) // 2)

    @staticmethod
    def get_landmark(hand, landmark_id):
        for lm in hand:
            if lm[0] == landmark_id:
                return lm
        return None

    def fingers_up(self, hand):
        fingers = []

        thumb_tip = self.get_landmark(hand, self.THUMB_TIP)
        thumb_ip = self.get_landmark(hand, self.THUMB_IP)
        if thumb_tip and thumb_ip:
            wrist = self.get_landmark(hand, self.WRIST)
            if wrist:
                fingers.append(abs(thumb_tip[1] - wrist[1]) > abs(thumb_ip[1] - wrist[1]))
            else:
                fingers.append(False)
        else:
            fingers.append(False)

        tip_ids = [self.INDEX_TIP, self.MIDDLE_TIP, self.RING_TIP, self.PINKY_TIP]
        pip_ids = [self.INDEX_PIP, self.MIDDLE_PIP, self.RING_PIP, self.PINKY_PIP]

        for tip_id, pip_id in zip(tip_ids, pip_ids):
            tip = self.get_landmark(hand, tip_id)
            pip = self.get_landmark(hand, pip_id)
            if tip and pip:
                fingers.append(tip[2] < pip[2])
            else:
                fingers.append(False)

        return fingers

    def release(self):
        self.detector.close()
