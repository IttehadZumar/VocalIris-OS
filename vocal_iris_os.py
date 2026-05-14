"""
VocalIris OS - Hands-free Multimodal Control System
Combines eye-tracking (gaze) with voice commands for accessibility
"""

import cv2
import threading
import queue
from datetime import datetime
from typing import Tuple, Optional
import pyautogui
import numpy as np

from gaze_tracking import GazeTracking
from voice_processor import VoiceProcessor
from command_executor import CommandExecutor
from ui_overlay import UIOverlay


class VocalIrisOS:
    """
    Main application class that orchestrates gaze tracking and voice control.
    Implements the "Point & Command" interaction model.
    """
    
    def __init__(self, debug_mode: bool = True):
        """
        Initialize VocalIris OS system.
        
        Args:
            debug_mode: Enable visual debugging overlays
        """
        self.debug_mode = debug_mode
        self.running = False
        self.paused = False
        
        # Core components
        self.gaze_tracker = GazeTracking()
        self.voice_processor = VoiceProcessor()
        self.command_executor = CommandExecutor()
        self.ui_overlay = UIOverlay(debug_mode=debug_mode)
        
        # Gaze tracking state
        self.current_gaze_pos = (0, 0)
        self.gaze_history = []
        self.max_history = 5
        self.sticky_target = None
        self.sticky_threshold = 30  # pixels
        
        # Thread safety
        self.command_queue = queue.Queue()
        self.gaze_lock = threading.Lock()
        
        # Camera setup
        self.cap = cv2.VideoCapture(0)
        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30
        self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # State tracking
        self.last_command = None
        self.last_command_time = None
        self.zoom_active = False
        self.rest_mode = False
        
        print(f"✓ VocalIris OS initialized")
        print(f"  Camera: {self.frame_width}x{self.frame_height} @ {self.fps} FPS")
        print(f"  Gaze smoothing: {self.max_history} frames")
        print(f"  Sticky target threshold: {self.sticky_threshold}px")

    def calibrate(self, duration_seconds: int = 30):
        """
        Calibration routine: user looks at screen corners for gaze calibration.
        
        Args:
            duration_seconds: Calibration time per point
        """
        print("\n🎯 Starting Calibration...")
        print(f"  Look at each corner for {duration_seconds} seconds")
        print("  Press SPACE to start, ESC to cancel")
        
        calibration_points = [
            ("Top-Left", (50, 50)),
            ("Top-Right", (self.frame_width - 50, 50)),
            ("Bottom-Left", (50, self.frame_height - 50)),
            ("Bottom-Right", (self.frame_width - 50, self.frame_height - 50)),
            ("Center", (self.frame_width // 2, self.frame_height // 2)),
        ]
        
        calibration_data = {}
        
        for point_name, point_coords in calibration_points:
            print(f"\n  → {point_name}: {point_coords}")
            calibration_data[point_name] = []
            
            start_time = datetime.now()
            frames_collected = 0
            
            while (datetime.now() - start_time).total_seconds() < duration_seconds:
                ret, frame = self.cap.read()
                if not ret:
                    break
                
                self.gaze_tracker.refresh(frame)
                frame_display = self.gaze_tracker.annotated_frame()
                
                # Draw calibration point
                cv2.circle(frame_display, point_coords, 15, (0, 255, 0), 2)
                cv2.putText(frame_display, point_name, 
                           (point_coords[0] + 20, point_coords[1]), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                if self.gaze_tracker.pupils_located:
                    gaze = self.gaze_tracker.pupil_left_coords()
                    if gaze:
                        calibration_data[point_name].append(gaze)
                        frames_collected += 1
                
                cv2.imshow("VocalIris - Calibration", frame_display)
                
                if cv2.waitKey(1) & 0xFF == 27:  # ESC
                    return False
            
            print(f"    ✓ Collected {frames_collected} frames")
        
        print("\n✓ Calibration complete!")
        return True

    def smooth_gaze(self, current_pos: Tuple[int, int]) -> Tuple[int, int]:
        """
        Apply temporal smoothing to gaze position to reduce jitter.
        Uses moving average of recent gaze positions.
        
        Args:
            current_pos: Current gaze position
            
        Returns:
            Smoothed gaze position
        """
        if not current_pos:
            return self.current_gaze_pos
        
        self.gaze_history.append(current_pos)
        if len(self.gaze_history) > self.max_history:
            self.gaze_history.pop(0)
        
        avg_x = sum(pos[0] for pos in self.gaze_history) / len(self.gaze_history)
        avg_y = sum(pos[1] for pos in self.gaze_history) / len(self.gaze_history)
        
        return (int(avg_x), int(avg_y))

    def apply_sticky_target(self, gaze_pos: Tuple[int, int], 
                           ui_elements: list) -> Tuple[int, int]:
        """
        Implement "Sticky Target" logic: snap cursor to nearby UI elements.
        This solves the "Midas Touch" problem by making targets easier to hit.
        
        Args:
            gaze_pos: Current gaze position
            ui_elements: List of (element_center, element_radius) tuples
            
        Returns:
            Snapped gaze position or original if no nearby element
        """
        for element_center, element_radius in ui_elements:
            distance = np.sqrt((gaze_pos[0] - element_center[0])**2 + 
                             (gaze_pos[1] - element_center[1])**2)
            
            if distance < self.sticky_threshold:
                return element_center
        
        return gaze_pos

    def process_gaze(self, frame):
        """
        Process frame to extract and track gaze position.
        
        Args:
            frame: Input video frame
            
        Returns:
            (gaze_position, frame_with_overlay)
        """
        self.gaze_tracker.refresh(frame)
        
        gaze_pos = None
        if self.gaze_tracker.pupils_located:
            # Use average of both eyes
            left = self.gaze_tracker.pupil_left_coords()
            right = self.gaze_tracker.pupil_right_coords()
            
            if left and right:
                gaze_pos = (
                    int((left[0] + right[0]) / 2),
                    int((left[1] + right[1]) / 2)
                )
        
        # Apply smoothing
        if gaze_pos:
            gaze_pos = self.smooth_gaze(gaze_pos)
        else:
            gaze_pos = self.current_gaze_pos
        
        with self.gaze_lock:
            self.current_gaze_pos = gaze_pos
        
        return gaze_pos, self.gaze_tracker.annotated_frame()

    def voice_listener_thread(self):
        """
        Separate thread for voice command processing (non-blocking).
        """
        while self.running:
            try:
                command = self.voice_processor.listen(timeout=1.0)
                if command:
                    self.command_queue.put(command)
            except Exception as e:
                print(f"Voice error: {e}")

    def process_command(self, command: str):
        """
        Execute command based on voice input and current gaze position.
        
        Args:
            command: Voice command string
        """
        command_lower = command.lower().strip()
        
        # System commands
        if command_lower in ["stop", "freeze"]:
            self.rest_mode = True
            self.ui_overlay.add_notification("🔒 Rest Mode ON - Eyes locked")
            print("🔒 Rest Mode: Eye tracking paused")
            return
        
        elif command_lower in ["wake", "wake up", "resume", "wake up iris"]:
            self.rest_mode = False
            self.gaze_history.clear()
            self.ui_overlay.add_notification("👁️ Rest Mode OFF")
            print("👁️ Eye tracking resumed")
            return
        
        elif command_lower == "zoom":
            self.zoom_active = not self.zoom_active
            status = "ON" if self.zoom_active else "OFF"
            self.ui_overlay.add_notification(f"🔍 Zoom Mode {status}")
            print(f"🔍 Zoom mode: {status}")
            return
        
        elif command_lower in ["calibrate", "recalibrate"]:
            self.calibrate(duration_seconds=15)
            return
        
        # Movement and interaction commands
        with self.gaze_lock:
            gaze_pos = self.current_gaze_pos
        
        # Execute action at gaze position
        if command_lower in ["click", "select", "activate"]:
            self.command_executor.left_click(gaze_pos)
            self.ui_overlay.add_notification(f"🖱️ Click @ {gaze_pos}")
            
        elif command_lower in ["right click", "options", "menu"]:
            self.command_executor.right_click(gaze_pos)
            self.ui_overlay.add_notification(f"⚙️ Menu @ {gaze_pos}")
            
        elif command_lower in ["double click", "double", "open"]:
            self.command_executor.double_click(gaze_pos)
            self.ui_overlay.add_notification(f"✨ Double-click @ {gaze_pos}")
            
        elif command_lower in ["scroll up", "scroll down"]:
            direction = 1 if "down" in command_lower else -1
            self.command_executor.scroll(gaze_pos, direction, amount=3)
            self.ui_overlay.add_notification(f"📜 Scroll {'down' if direction > 0 else 'up'}")
            
        elif command_lower.startswith("type "):
            text = command_lower[5:].strip()
            self.command_executor.type_text(text)
            self.ui_overlay.add_notification(f"⌨️ Typed: {text}")
            
        elif command_lower in ["drag", "move"]:
            # Drag from current position to next command position
            self.ui_overlay.add_notification("🎯 Drag mode - Look and say 'drop'")
            
        elif command_lower == "drop":
            self.command_executor.release_drag(gaze_pos)
            self.ui_overlay.add_notification("✋ Dropped")
        
        self.last_command = command
        self.last_command_time = datetime.now()

    def run(self):
        """
        Main application loop: capture video, process gaze, handle voice, render UI.
        """
        self.running = True
        
        # Start voice listener in background thread
        voice_thread = threading.Thread(target=self.voice_listener_thread, daemon=True)
        voice_thread.start()
        
        print("\n▶️  VocalIris OS Running")
        print("  Commands: CLICK, RIGHT CLICK, ZOOM, CALIBRATE, STOP, WAKE UP")
        print("  Press 'Q' or 'ESC' to exit\n")
        
        frame_count = 0
        
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                break
            
            frame_count += 1
            
            # Process gaze (unless in rest mode)
            if not self.rest_mode:
                gaze_pos, annotated_frame = self.process_gaze(frame)
            else:
                gaze_pos = self.current_gaze_pos
                annotated_frame = frame.copy()
            
            # Process any queued voice commands
            while not self.command_queue.empty():
                try:
                    command = self.command_queue.get_nowait()
                    print(f"🎤 Command: {command}")
                    self.process_command(command)
                except queue.Empty:
                    break
            
            # Render UI overlay
            display_frame = self.ui_overlay.render(
                annotated_frame,
                gaze_pos,
                self.rest_mode,
                self.zoom_active,
                self.last_command,
                frame_count
            )
            
            # Show frame
            cv2.imshow("VocalIris OS - Control System", display_frame)
            
            # Input handling
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:  # Q or ESC
                self.shutdown()
            elif key == ord('c'):
                self.calibrate(duration_seconds=10)
            elif key == ord('z'):
                self.zoom_active = not self.zoom_active
            elif key == ord('s'):
                self.rest_mode = not self.rest_mode

    def shutdown(self):
        """Clean shutdown of all systems."""
        print("\n🛑 Shutting down VocalIris OS...")
        self.running = False
        
        # Clean up resources
        self.cap.release()
        cv2.destroyAllWindows()
        self.voice_processor.cleanup()
        
        print("✓ VocalIris OS terminated")


def main():
    """Entry point for VocalIris OS."""
    try:
        system = VocalIrisOS(debug_mode=True)
        system.calibrate(duration_seconds=5)  # Quick calibration
        system.run()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
