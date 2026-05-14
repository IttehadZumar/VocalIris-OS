"""
UI Overlay Module - Visual feedback and debugging overlays
Renders gaze cursor, commands, notifications, and system status
"""

import cv2
import numpy as np
from typing import Tuple, List, Optional
from collections import deque
from datetime import datetime


class UIOverlay:
    """
    Renders real-time visual feedback for VocalIris OS.
    Shows gaze cursor, command history, notifications, and debug info.
    """
    
    # Color scheme (BGR format for OpenCV)
    COLOR_GAZE = (0, 255, 0)        # Green - gaze cursor
    COLOR_TEXT = (255, 255, 255)    # White - text
    COLOR_ACCENT = (0, 165, 255)    # Orange - accents
    COLOR_WARNING = (0, 0, 255)     # Red - warnings
    COLOR_SUCCESS = (0, 255, 0)     # Green - success
    COLOR_INFO = (255, 255, 0)      # Cyan - info
    
    def __init__(self, debug_mode: bool = True):
        """
        Initialize UI overlay renderer.
        
        Args:
            debug_mode: Show debug information
        """
        self.debug_mode = debug_mode
        self.notifications = deque(maxlen=5)
        self.notification_lifetime = 2.0  # seconds
        self.frame_count = 0
        
        # Gaze cursor animation
        self.gaze_ring_size = 0
        self.gaze_ring_max = 20
        
        # Text properties
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.font_scale = 0.5
        self.thickness = 1
        
    def add_notification(self, message: str, duration: float = None):
        """
        Add a notification message to display.
        
        Args:
            message: Text to display
            duration: Display duration in seconds
        """
        notification = {
            'message': message,
            'timestamp': datetime.now(),
            'duration': duration or self.notification_lifetime
        }
        self.notifications.append(notification)

    def render(self, frame: np.ndarray,
              gaze_pos: Tuple[int, int],
              rest_mode: bool = False,
              zoom_mode: bool = False,
              last_command: Optional[str] = None,
              frame_count: int = 0) -> np.ndarray:
        """
        Render complete UI overlay on frame.
        
        Args:
            frame: Input video frame
            gaze_pos: Current gaze position
            rest_mode: Whether in rest/pause mode
            zoom_mode: Whether zoom mode is active
            last_command: Last voice command executed
            frame_count: Current frame number for animation
            
        Returns:
            Frame with rendered overlays
        """
        self.frame_count = frame_count
        display = frame.copy()
        height, width = display.shape[:2]
        
        # 1. Render gaze cursor
        self._render_gaze_cursor(display, gaze_pos, rest_mode)
        
        # 2. Render status indicators
        self._render_status_bar(display, width, rest_mode, zoom_mode)
        
        # 3. Render command history
        self._render_last_command(display, last_command, width)
        
        # 4. Render notifications
        self._render_notifications(display, width, height)
        
        # 5. Debug information
        if self.debug_mode:
            self._render_debug_info(display, gaze_pos, frame_count)
        
        # 6. Render crosshair for calibration assistance
        self._render_crosshair(display, width, height)
        
        return display

    def _render_gaze_cursor(self, frame: np.ndarray,
                           gaze_pos: Tuple[int, int],
                           rest_mode: bool):
        """
        Render animated gaze cursor.
        
        Args:
            frame: Target frame
            gaze_pos: Gaze position
            rest_mode: Whether in rest mode
        """
        if not gaze_pos:
            return
        
        x, y = gaze_pos
        
        # Clamp to frame bounds
        height, width = frame.shape[:2]
        x = max(0, min(x, width - 1))
        y = max(0, min(y, height - 1))
        
        if rest_mode:
            # Rest mode: locked indicator
            color = self.COLOR_WARNING
            cv2.circle(frame, (x, y), 15, color, 2)
            cv2.circle(frame, (x, y), 8, color, 2)
            # Add lock icon
            cv2.line(frame, (x - 5, y - 8), (x + 5, y - 8), color, 2)
            cv2.rectangle(frame, (x - 5, y - 5), (x + 5, y + 8), color, 2)
        else:
            # Normal gaze cursor with animated ring
            self.gaze_ring_size = (self.frame_count % 20) * self.gaze_ring_max / 20
            
            # Main cursor circle
            cv2.circle(frame, (x, y), 10, self.COLOR_GAZE, 2)
            
            # Animated ring
            ring_size = int(self.gaze_ring_size)
            if ring_size > 0:
                cv2.circle(frame, (x, y), ring_size, self.COLOR_GAZE, 1)
            
            # Crosshair
            cv2.line(frame, (x - 5, y), (x + 5, y), self.COLOR_GAZE, 1)
            cv2.line(frame, (x, y - 5), (x, y + 5), self.COLOR_GAZE, 1)
            
            # Dot in center
            cv2.circle(frame, (x, y), 3, self.COLOR_GAZE, -1)

    def _render_status_bar(self, frame: np.ndarray,
                          width: int,
                          rest_mode: bool,
                          zoom_mode: bool):
        """
        Render top status bar with system indicators.
        
        Args:
            frame: Target frame
            width: Frame width
            rest_mode: Rest mode status
            zoom_mode: Zoom mode status
        """
        bar_height = 30
        
        # Semi-transparent background
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (width, bar_height), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)
        
        # Status text
        status_items = []
        
        if rest_mode:
            status_items.append(("🔒 REST", self.COLOR_WARNING))
        else:
            status_items.append(("👁️ ACTIVE", self.COLOR_SUCCESS))
        
        if zoom_mode:
            status_items.append(("🔍 ZOOM", self.COLOR_INFO))
        
        status_items.append((f"FPS: {self.frame_count}", self.COLOR_TEXT))
        
        # Draw status items
        x_offset = 10
        for status_text, color in status_items:
            cv2.putText(frame, status_text, (x_offset, 20),
                       self.font, self.font_scale, color, self.thickness)
            x_offset += len(status_text) * 30

    def _render_last_command(self, frame: np.ndarray,
                            last_command: Optional[str],
                            width: int):
        """
        Render last executed command.
        
        Args:
            frame: Target frame
            last_command: Last command string
            width: Frame width
        """
        if not last_command:
            return
        
        # Display at bottom center
        height = frame.shape[0]
        text = f"Last Command: {last_command}"
        text_size = cv2.getTextSize(text, self.font, self.font_scale, self.thickness)
        text_w = text_size[0][0]
        
        x = (width - text_w) // 2
        y = height - 10
        
        # Background box
        padding = 5
        cv2.rectangle(frame, (x - padding, y - 15 - padding),
                     (x + text_w + padding, y + padding),
                     (0, 0, 0), -1)
        cv2.addWeighted(frame, 0.7, frame, 0.3, 0, frame)
        
        # Text
        cv2.putText(frame, text, (x, y - 5),
                   self.font, self.font_scale, self.COLOR_SUCCESS, self.thickness)

    def _render_notifications(self, frame: np.ndarray,
                            width: int,
                            height: int):
        """
        Render floating notification messages.
        
        Args:
            frame: Target frame
            width: Frame width
            height: Frame height
        """
        current_time = datetime.now()
        y_offset = 50
        
        for notification in self.notifications:
            # Check if notification has expired
            elapsed = (current_time - notification['timestamp']).total_seconds()
            if elapsed > notification['duration']:
                continue
            
            message = notification['message']
            
            # Fade out effect
            alpha = max(0, 1 - (elapsed / notification['duration']))
            
            # Text size
            text_size = cv2.getTextSize(message, self.font, 0.6, self.thickness)
            text_w = text_size[0][0]
            text_h = text_size[0][1]
            
            x = (width - text_w) // 2
            y = y_offset
            
            # Semi-transparent background
            overlay = frame.copy()
            padding = 8
            cv2.rectangle(overlay, (x - padding, y - text_h - padding),
                         (x + text_w + padding, y + padding),
                         self.COLOR_ACCENT, -1)
            cv2.addWeighted(overlay, alpha * 0.7, frame, 1 - (alpha * 0.7), 0, frame)
            
            # Text
            text_color = tuple(int(c * alpha) for c in self.COLOR_TEXT)
            cv2.putText(frame, message, (x, y),
                       self.font, 0.6, text_color, self.thickness)
            
            y_offset += 30

    def _render_debug_info(self, frame: np.ndarray,
                          gaze_pos: Tuple[int, int],
                          frame_count: int):
        """
        Render debug information (position, metrics, etc).
        
        Args:
            frame: Target frame
            gaze_pos: Current gaze position
            frame_count: Frame number
        """
        height, width = frame.shape[:2]
        y_pos = 50
        
        debug_info = [
            f"Gaze: ({gaze_pos[0]}, {gaze_pos[1]})",
            f"Frame: {frame_count}",
            f"Res: {width}x{height}",
        ]
        
        # Semi-transparent background
        overlay = frame.copy()
        cv2.rectangle(overlay, (width - 200, 30), (width - 10, 30 + len(debug_info) * 20),
                     (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.4, frame, 0.6, 0, frame)
        
        # Debug text
        for i, info in enumerate(debug_info):
            cv2.putText(frame, info, (width - 195, y_pos + i * 18),
                       self.font, 0.4, self.COLOR_INFO, 1)

    def _render_crosshair(self, frame: np.ndarray,
                         width: int,
                         height: int):
        """
        Render center crosshair for screen reference.
        
        Args:
            frame: Target frame
            width: Frame width
            height: Frame height
        """
        center_x = width // 2
        center_y = height // 2
        
        # Faint crosshair
        cv2.line(frame, (center_x - 20, center_y), (center_x + 20, center_y),
                (50, 50, 50), 1)
        cv2.line(frame, (center_x, center_y - 20), (center_x, center_y + 20),
                (50, 50, 50), 1)
        cv2.circle(frame, (center_x, center_y), 3, (50, 50, 50), -1)

    def render_calibration_ui(self, frame: np.ndarray,
                             point_name: str,
                             point_pos: Tuple[int, int]) -> np.ndarray:
        """
        Render calibration UI with target point.
        
        Args:
            frame: Input frame
            point_name: Name of calibration point
            point_pos: Position of calibration point
            
        Returns:
            Frame with calibration UI
        """
        display = frame.copy()
        height, width = display.shape[:2]
        
        # Title
        title = "VOCAL IRIS CALIBRATION"
        text_size = cv2.getTextSize(title, self.font, 1.0, 2)
        title_x = (width - text_size[0][0]) // 2
        cv2.putText(display, title, (title_x, 40),
                   self.font, 1.0, self.COLOR_ACCENT, 2)
        
        # Instructions
        instructions = f"Look at {point_name} - Keep looking for 5 seconds"
        text_size = cv2.getTextSize(instructions, self.font, 0.7, 1)
        instr_x = (width - text_size[0][0]) // 2
        cv2.putText(display, instructions, (instr_x, 80),
                   self.font, 0.7, self.COLOR_TEXT, 1)
        
        # Target point with animation
        animation_frame = self.frame_count % 30
        ring_size = 20 + 10 * (animation_frame / 30)
        
        cv2.circle(display, point_pos, int(ring_size), self.COLOR_GAZE, 2)
        cv2.circle(display, point_pos, 20, self.COLOR_GAZE, 3)
        cv2.circle(display, point_pos, 8, self.COLOR_GAZE, -1)
        
        # Point label
        cv2.putText(display, point_name,
                   (point_pos[0] + 30, point_pos[1]),
                   self.font, 0.8, self.COLOR_ACCENT, 2)
        
        return display


class ZoomOverlay:
    """
    Magnified zoom window for accessing small UI elements.
    """
    
    def __init__(self, zoom_level: int = 3, window_size: int = 300):
        """
        Initialize zoom overlay.
        
        Args:
            zoom_level: Magnification factor
            window_size: Size of zoom window in pixels
        """
        self.zoom_level = zoom_level
        self.window_size = window_size
        self.active = False

    def render(self, frame: np.ndarray,
              gaze_pos: Tuple[int, int]) -> np.ndarray:
        """
        Render magnified zoom window at gaze position.
        
        Args:
            frame: Input frame
            gaze_pos: Center of zoom window
            
        Returns:
            Frame with zoom window
        """
        if not self.active or not gaze_pos:
            return frame
        
        display = frame.copy()
        height, width = display.shape[:2]
        
        # Calculate zoom region
        half_size = self.window_size // (2 * self.zoom_level)
        x1 = max(0, gaze_pos[0] - half_size)
        y1 = max(0, gaze_pos[1] - half_size)
        x2 = min(width, gaze_pos[0] + half_size)
        y2 = min(height, gaze_pos[1] + half_size)
        
        # Extract and magnify
        region = frame[y1:y2, x1:x2]
        zoomed = cv2.resize(region, (self.window_size, self.window_size))
        
        # Position window
        window_x = width - self.window_size - 20
        window_y = 60
        
        # Draw magnified content
        display[window_y:window_y + self.window_size,
               window_x:window_x + self.window_size] = zoomed
        
        # Draw border
        cv2.rectangle(display, (window_x, window_y),
                     (window_x + self.window_size, window_y + self.window_size),
                     (0, 255, 0), 3)
        
        # Draw center crosshair
        center_x = window_x + self.window_size // 2
        center_y = window_y + self.window_size // 2
        cv2.line(display, (center_x - 10, center_y), (center_x + 10, center_y),
                (0, 255, 0), 2)
        cv2.line(display, (center_x, center_y - 10), (center_x, center_y + 10),
                (0, 255, 0), 2)
        
        return display
