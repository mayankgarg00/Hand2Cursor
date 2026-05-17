import time
import numpy as np
import pyautogui
import cv2

from hand_tracker import HandTracker

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0


class GestureController:

    def __init__(self, screen_w, screen_h, frame_w=640, frame_h=480,
                 frame_margin=80, smoothing=0.35, click_cooldown=0.4,
                 pinch_threshold=40, sensitivity=1.0):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.frame_w = frame_w
        self.frame_h = frame_h

        self.margin = frame_margin
        self.x_min = self.margin
        self.x_max = self.frame_w - self.margin
        self.y_min = self.margin
        self.y_max = self.frame_h - self.margin

        self.smoothing = smoothing
        self._prev_x = 0.0
        self._prev_y = 0.0
        self._first_move = True

        self.click_cooldown = click_cooldown
        self._last_left_click = 0.0
        self._last_right_click = 0.0

        self.pinch_threshold = pinch_threshold
        self.sensitivity = sensitivity

        self._dragging = False

        self._click_anim_time = 0.0
        self._click_anim_pos = (0, 0)
        self._click_anim_type = None

    def _map_to_screen(self, x, y):
        x = np.clip(x, self.x_min, self.x_max)
        y = np.clip(y, self.y_min, self.y_max)
        norm_x = (x - self.x_min) / (self.x_max - self.x_min)
        norm_y = (y - self.y_min) / (self.y_max - self.y_min)
        sx = np.clip(norm_x * self.screen_w * self.sensitivity, 0, self.screen_w - 1)
        sy = np.clip(norm_y * self.screen_h * self.sensitivity, 0, self.screen_h - 1)
        return float(sx), float(sy)

    def _smooth(self, x, y):
        if self._first_move:
            self._prev_x, self._prev_y = x, y
            self._first_move = False
            return x, y
        sx = self._prev_x + self.smoothing * (x - self._prev_x)
        sy = self._prev_y + self.smoothing * (y - self._prev_y)
        self._prev_x, self._prev_y = sx, sy
        return sx, sy

    def _is_pinching(self, hand, id_a, id_b):
        pt_a = HandTracker.get_landmark(hand, id_a)
        pt_b = HandTracker.get_landmark(hand, id_b)
        if pt_a is None or pt_b is None:
            return False, float('inf'), (0, 0)
        dist = HandTracker.distance(pt_a, pt_b)
        mid = HandTracker.midpoint(pt_a, pt_b)
        return dist < self.pinch_threshold, dist, mid

    def update(self, hand, frame=None):
        action = 'idle'
        now = time.time()

        index_tip = HandTracker.get_landmark(hand, HandTracker.INDEX_TIP)
        if index_tip is None:
            return action

        pinch_ti, dist_ti, mid_ti = self._is_pinching(
            hand, HandTracker.THUMB_TIP, HandTracker.INDEX_TIP)
        pinch_tm, dist_tm, mid_tm = self._is_pinching(
            hand, HandTracker.THUMB_TIP, HandTracker.MIDDLE_TIP)

        if pinch_ti and pinch_tm:
            if now - self._last_right_click > self.click_cooldown:
                pyautogui.click(button='right')
                self._last_right_click = now
                action = 'right_click'
                self._click_anim_time = now
                self._click_anim_pos = mid_ti
                self._click_anim_type = 'right'

        elif pinch_ti:
            if now - self._last_left_click > self.click_cooldown:
                pyautogui.click(button='left')
                self._last_left_click = now
                action = 'left_click'
                self._click_anim_time = now
                self._click_anim_pos = mid_ti
                self._click_anim_type = 'left'

        else:
            sx, sy = self._map_to_screen(index_tip[1], index_tip[2])
            sx, sy = self._smooth(sx, sy)
            pyautogui.moveTo(int(sx), int(sy))
            action = 'move'

        if frame is not None:
            self._draw_feedback(frame, hand, action, now,
                                dist_ti, mid_ti, dist_tm, mid_tm)
        return action

    def handle_drag(self, hand, fist_threshold=30):
        tips = [HandTracker.INDEX_TIP, HandTracker.MIDDLE_TIP,
                HandTracker.RING_TIP, HandTracker.PINKY_TIP]
        mcps = [HandTracker.INDEX_MCP, HandTracker.MIDDLE_MCP,
                HandTracker.RING_MCP, HandTracker.PINKY_MCP]
        fist = True
        for t, m in zip(tips, mcps):
            pt = HandTracker.get_landmark(hand, t)
            pm = HandTracker.get_landmark(hand, m)
            if pt and pm and HandTracker.distance(pt, pm) > fist_threshold:
                fist = False
                break
        if fist and not self._dragging:
            pyautogui.mouseDown()
            self._dragging = True
            return 'drag_start'
        elif fist and self._dragging:
            return 'dragging'
        elif not fist and self._dragging:
            pyautogui.mouseUp()
            self._dragging = False
            return 'drag_end'
        return 'none'

    def _draw_feedback(self, frame, hand, action, now,
                       dist_ti, mid_ti, dist_tm, mid_tm):
        h, w = frame.shape[:2]

        cv2.rectangle(frame, (self.x_min, self.y_min),
                      (self.x_max, self.y_max), (255, 200, 0), 2)

        thumb = HandTracker.get_landmark(hand, HandTracker.THUMB_TIP)
        index = HandTracker.get_landmark(hand, HandTracker.INDEX_TIP)
        middle = HandTracker.get_landmark(hand, HandTracker.MIDDLE_TIP)

        if thumb and index:
            c = (0, 255, 0) if dist_ti < self.pinch_threshold else (0, 0, 255)
            cv2.line(frame, (thumb[1], thumb[2]), (index[1], index[2]), c, 2)
            cv2.circle(frame, mid_ti, 6, c, cv2.FILLED)

        if thumb and middle:
            c = (0, 255, 0) if dist_tm < self.pinch_threshold else (200, 100, 0)
            cv2.line(frame, (thumb[1], thumb[2]), (middle[1], middle[2]), c, 2)
            cv2.circle(frame, mid_tm, 6, c, cv2.FILLED)

        if index:
            cv2.circle(frame, (index[1], index[2]), 10, (255, 0, 255), cv2.FILLED)

        elapsed = now - self._click_anim_time
        if elapsed < 0.3 and self._click_anim_type:
            radius = int(10 + elapsed * 150)
            ring_c = (0, 255, 0) if self._click_anim_type == 'left' else (0, 200, 255)
            thick = max(1, int(3 * (1.0 - elapsed / 0.3)))
            cv2.circle(frame, self._click_anim_pos, radius, ring_c, thick)

        labels = {
            'move': ('Moving', (200, 255, 200)),
            'left_click': ('LEFT CLICK', (0, 255, 0)),
            'right_click': ('RIGHT CLICK', (0, 200, 255)),
            'idle': ('Idle', (180, 180, 180)),
        }
        label, color = labels.get(action, ('', (255, 255, 255)))
        cv2.putText(frame, label, (10, h - 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

    def draw_hud(self, frame, hand):
        thumb = HandTracker.get_landmark(hand, HandTracker.THUMB_TIP)
        index = HandTracker.get_landmark(hand, HandTracker.INDEX_TIP)
        middle = HandTracker.get_landmark(hand, HandTracker.MIDDLE_TIP)
        y = 60
        if thumb and index:
            d = HandTracker.distance(thumb, index)
            s = "PINCH" if d < self.pinch_threshold else "open"
            cv2.putText(frame, f"Thumb-Index: {d:.0f}px [{s}]",
                        (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            y += 25
        if thumb and middle:
            d = HandTracker.distance(thumb, middle)
            s = "PINCH" if d < self.pinch_threshold else "open"
            cv2.putText(frame, f"Thumb-Middle: {d:.0f}px [{s}]",
                        (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
