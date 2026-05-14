"""
Command Executor Module - Converts voice commands to system actions
Handles mouse control, keyboard input, and OS interactions
"""

import pyautogui
import time
from typing import Tuple, Optional
import platform
import subprocess


class CommandExecutor:
    """
    Executes system commands based on gaze position and voice input.
    Implements the "Point & Command" execution model.
    """
    
    MOUSE_SPEED = 0.1  # Seconds for smooth mouse movement
    DRAG_SPEED = 0.05
    
    def __init__(self):
        """Initialize command executor."""
        self.dragging = False
        self.drag_start = None
        self.last_action_time = None
        self.action_delay = 0.05  # Minimum delay between actions
        
        # Fail-safe: enable pyautogui's built-in safety (move to corner to abort)
        pyautogui.FAILSAFE = True
        
        # Get screen dimensions
        self.screen_width, self.screen_height = pyautogui.size()
        
        print(f"✓ Command executor initialized")
        print(f"  Screen: {self.screen_width}x{self.screen_height}")
        print(f"  Failsafe: enabled (move mouse to corner to abort)")

    def _rate_limit(self):
        """Prevent command flooding by enforcing minimum delay between actions."""
        if self.last_action_time:
            elapsed = time.time() - self.last_action_time
            if elapsed < self.action_delay:
                time.sleep(self.action_delay - elapsed)
        self.last_action_time = time.time()

    def _clamp_coords(self, pos: Tuple[int, int]) -> Tuple[int, int]:
        """
        Clamp coordinates to screen bounds.
        
        Args:
            pos: Position tuple (x, y)
            
        Returns:
            Clamped position within screen bounds
        """
        x = max(0, min(pos[0], self.screen_width - 1))
        y = max(0, min(pos[1], self.screen_height - 1))
        return (x, y)

    def move_mouse(self, pos: Tuple[int, int], duration: float = None):
        """
        Move mouse cursor to position with smooth movement.
        
        Args:
            pos: Target position (x, y)
            duration: Movement duration in seconds (None for instant)
        """
        pos = self._clamp_coords(pos)
        
        if duration is None:
            pyautogui.moveTo(pos[0], pos[1], duration=0)
        else:
            pyautogui.moveTo(pos[0], pos[1], duration=duration)

    def left_click(self, pos: Tuple[int, int], double: bool = False):
        """
        Perform left mouse click at position.
        
        Args:
            pos: Click position (x, y)
            double: If True, perform double-click
        """
        self._rate_limit()
        pos = self._clamp_coords(pos)
        
        self.move_mouse(pos, duration=self.MOUSE_SPEED)
        
        if double:
            pyautogui.doubleClick(pos[0], pos[1], interval=0.1)
        else:
            pyautogui.click(pos[0], pos[1])
        
        time.sleep(0.1)

    def double_click(self, pos: Tuple[int, int]):
        """
        Perform double-click (used for opening files/folders).
        
        Args:
            pos: Click position (x, y)
        """
        self._rate_limit()
        self.left_click(pos, double=True)

    def right_click(self, pos: Tuple[int, int]):
        """
        Perform right-click to open context menu.
        
        Args:
            pos: Click position (x, y)
        """
        self._rate_limit()
        pos = self._clamp_coords(pos)
        
        self.move_mouse(pos, duration=self.MOUSE_SPEED)
        pyautogui.rightClick(pos[0], pos[1])
        
        time.sleep(0.1)

    def start_drag(self, start_pos: Tuple[int, int]):
        """
        Start dragging from position.
        
        Args:
            start_pos: Starting position (x, y)
        """
        self._rate_limit()
        start_pos = self._clamp_coords(start_pos)
        
        self.dragging = True
        self.drag_start = start_pos
        
        self.move_mouse(start_pos, duration=self.MOUSE_SPEED)
        pyautogui.mouseDown(start_pos[0], start_pos[1])
        
        print(f"🎯 Drag started at {start_pos}")

    def drag_to(self, end_pos: Tuple[int, int]):
        """
        Continue dragging to position (while button held down).
        
        Args:
            end_pos: Target position (x, y)
        """
        if not self.dragging:
            return
        
        end_pos = self._clamp_coords(end_pos)
        self.move_mouse(end_pos, duration=self.DRAG_SPEED)

    def release_drag(self, end_pos: Tuple[int, int]):
        """
        Release drag operation.
        
        Args:
            end_pos: Final position (x, y)
        """
        if not self.dragging:
            return
        
        self._rate_limit()
        end_pos = self._clamp_coords(end_pos)
        
        self.move_mouse(end_pos, duration=self.DRAG_SPEED)
        pyautogui.mouseUp(end_pos[0], end_pos[1])
        
        self.dragging = False
        print(f"✋ Drag released at {end_pos}")

    def scroll(self, pos: Tuple[int, int], direction: int = 1, amount: int = 3):
        """
        Scroll at position.
        
        Args:
            pos: Scroll position (x, y)
            direction: 1 for down, -1 for up
            amount: Number of scroll events
        """
        self._rate_limit()
        pos = self._clamp_coords(pos)
        
        self.move_mouse(pos, duration=self.MOUSE_SPEED)
        
        # scroll() uses wheel clicks: positive=up, negative=down
        scroll_amount = direction * amount
        pyautogui.scroll(scroll_amount)
        
        time.sleep(0.2)

    def type_text(self, text: str, interval: float = 0.05):
        """
        Type text using keyboard.
        
        Args:
            text: Text to type
            interval: Delay between keystrokes in seconds
        """
        self._rate_limit()
        pyautogui.typewrite(text, interval=interval)
        time.sleep(0.1)

    def press_key(self, key: str, count: int = 1):
        """
        Press a keyboard key.
        
        Args:
            key: Key name (e.g., 'enter', 'space', 'backspace')
            count: Number of times to press
        """
        self._rate_limit()
        for _ in range(count):
            pyautogui.press(key)
            time.sleep(0.05)

    def key_combination(self, *keys):
        """
        Press multiple keys simultaneously (e.g., Ctrl+C).
        
        Args:
            *keys: Key names to press together
        """
        self._rate_limit()
        pyautogui.hotkey(*keys)
        time.sleep(0.1)

    def copy_to_clipboard(self):
        """Copy selection to clipboard."""
        self.key_combination('ctrl', 'c')

    def paste_from_clipboard(self):
        """Paste from clipboard."""
        self.key_combination('ctrl', 'v')

    def select_all(self):
        """Select all (Ctrl+A)."""
        self.key_combination('ctrl', 'a')

    def undo(self):
        """Undo last action (Ctrl+Z)."""
        self.key_combination('ctrl', 'z')

    def redo(self):
        """Redo last action (Ctrl+Y)."""
        self.key_combination('ctrl', 'y')

    def take_screenshot(self, filename: str = "screenshot.png") -> bool:
        """
        Take a screenshot.
        
        Args:
            filename: Output filename
            
        Returns:
            True if successful
        """
        try:
            screenshot = pyautogui.screenshot()
            screenshot.save(filename)
            print(f"📸 Screenshot saved: {filename}")
            return True
        except Exception as e:
            print(f"❌ Screenshot failed: {e}")
            return False

    def open_application(self, app_name: str) -> bool:
        """
        Open an application by name.
        
        Args:
            app_name: Application name (e.g., 'notepad', 'firefox')
            
        Returns:
            True if launch successful
        """
        try:
            system = platform.system()
            
            if system == "Windows":
                subprocess.Popen(app_name)
            elif system == "Darwin":  # macOS
                subprocess.Popen(['open', '-a', app_name])
            elif system == "Linux":
                subprocess.Popen(app_name)
            
            print(f"✓ Opened application: {app_name}")
            time.sleep(1)  # Wait for app to start
            return True
        
        except Exception as e:
            print(f"❌ Failed to open {app_name}: {e}")
            return False

    def activate_window(self, window_title: str) -> bool:
        """
        Activate window by title (platform-specific).
        
        Args:
            window_title: Window title to search for
            
        Returns:
            True if window found and activated
        """
        try:
            system = platform.system()
            
            if system == "Windows":
                import pygetwindow as gw
                windows = gw.getWindowsWithTitle(window_title)
                if windows:
                    windows[0].activate()
                    return True
            
            # Note: macOS and Linux require different approaches
            # This is a simplified version
            
            return False
        
        except Exception as e:
            print(f"⚠️  Window activation error: {e}")
            return False


class SmartExecutor(CommandExecutor):
    """
    Enhanced executor with predictive features:
    - Command history and learning
    - Gesture recognition
    - Contextual command adaptation
    """
    
    def __init__(self):
        """Initialize smart executor."""
        super().__init__()
        self.command_history = []
        self.max_history = 50
        self.gesture_buffer = []
        self.last_position = (0, 0)
    
    def record_command(self, command: str, position: Tuple[int, int]):
        """
        Record command for learning and prediction.
        
        Args:
            command: Command name
            position: Screen position where command was executed
        """
        entry = {
            'command': command,
            'position': position,
            'timestamp': time.time()
        }
        self.command_history.append(entry)
        
        if len(self.command_history) > self.max_history:
            self.command_history.pop(0)
    
    def detect_gesture(self, positions: list) -> Optional[str]:
        """
        Detect gesture pattern from sequence of positions.
        
        Args:
            positions: List of (x, y) positions
            
        Returns:
            Detected gesture name or None
        """
        if len(positions) < 3:
            return None
        
        # Simple gesture detection
        x_movement = positions[-1][0] - positions[0][0]
        y_movement = positions[-1][1] - positions[0][1]
        
        if abs(x_movement) > abs(y_movement):
            if x_movement > 100:
                return "SWIPE_RIGHT"
            elif x_movement < -100:
                return "SWIPE_LEFT"
        else:
            if y_movement > 100:
                return "SWIPE_DOWN"
            elif y_movement < -100:
                return "SWIPE_UP"
        
        return None
    
    def predict_next_command(self) -> Optional[str]:
        """
        Predict likely next command based on history.
        
        Returns:
            Predicted command or None
        """
        if len(self.command_history) < 3:
            return None
        
        # Simple frequency analysis
        recent = self.command_history[-5:]
        commands = [entry['command'] for entry in recent]
        
        # Return most frequent command in recent history
        return max(set(commands), key=commands.count) if commands else None
