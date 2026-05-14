"""
VocalIris OS - Usage Examples & Demo Scenarios

This file demonstrates common usage patterns and workflows.
"""

# ============================================================================
# EXAMPLE 1: Basic Application Usage
# ============================================================================

def example_basic_usage():
    """
    Most common usage: run full application with all features.
    """
    from vocal_iris_os import VocalIrisOS
    
    # Initialize system
    system = VocalIrisOS(debug_mode=True)
    
    # Run calibration (user looks at screen corners)
    print("Starting calibration... look at screen corners")
    system.calibrate(duration_seconds=5)
    
    # Main loop: eye tracking + voice commands
    system.run()


# ============================================================================
# EXAMPLE 2: Custom Gaze Tracking Only (No Voice)
# ============================================================================

def example_gaze_tracking_only():
    """
    Use just the gaze tracking component for custom applications.
    Useful for custom gesture recognition, attention detection, etc.
    """
    import cv2
    from gaze_tracking import GazeTracking
    
    gaze = GazeTracking()
    cap = cv2.VideoCapture(0)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Track gaze
        gaze.refresh(frame)
        
        # Get gaze information
        if gaze.pupils_located:
            # Get gaze position
            left_pupil = gaze.pupil_left_coords()
            right_pupil = gaze.pupil_right_coords()
            
            # Get gaze direction
            h_ratio = gaze.horizontal_ratio()  # 0=right, 0.5=center, 1=left
            v_ratio = gaze.vertical_ratio()    # 0=top, 0.5=center, 1=bottom
            
            # Check gaze state
            is_looking_right = gaze.is_right()
            is_looking_left = gaze.is_left()
            is_looking_center = gaze.is_center()
            is_blinking = gaze.is_blinking()
            
            print(f"Gaze: ({h_ratio:.2f}, {v_ratio:.2f}) | "
                  f"Left: {is_looking_left} | Right: {is_looking_right} | "
                  f"Blink: {is_blinking}")
        
        # Display
        frame = gaze.annotated_frame()
        cv2.imshow("Gaze Tracking", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()


# ============================================================================
# EXAMPLE 3: Voice Commands Only (No Gaze)
# ============================================================================

def example_voice_commands_only():
    """
    Process voice commands without gaze tracking.
    Useful for testing voice system or hands-free audio control.
    """
    from voice_processor import VoiceProcessor, AdvancedVoiceProcessor
    
    # Option 1: Basic voice processor
    print("=== Voice Commands Demo ===")
    voice = VoiceProcessor(use_offline_mode=False)  # Use Google Speech API
    
    print("Listening for voice commands...")
    print("Try saying: 'click', 'right click', 'scroll down', etc.")
    
    for i in range(5):  # Listen for 5 commands
        command = voice.listen(timeout=5.0)
        
        if command:
            print(f"\nHeard: {command}")
            
            # Extract recognized command
            recognized = voice.extract_command(command)
            if recognized:
                print(f"Command: {recognized}")
            else:
                print("(Not a VocalIris command)")
    
    voice.cleanup()


# ============================================================================
# EXAMPLE 4: Advanced Voice with Features
# ============================================================================

def example_advanced_voice():
    """
    Use advanced voice processor with noise filtering and VAD.
    """
    from voice_processor import AdvancedVoiceProcessor
    
    voice = AdvancedVoiceProcessor(use_offline_mode=True)  # Offline mode
    
    # Add custom commands
    voice.add_custom_words(['open firefox', 'close window', 'go home'])
    
    # Enable Voice Activity Detection (optional)
    # voice.enable_voice_activity_detection()
    
    print("Advanced voice processor ready")
    print("Commands: 'click', 'right click', 'scroll', or custom words")
    
    # Listen in background
    voice.start_background_listening()
    
    import time
    for i in range(30):  # Listen for 30 seconds
        command = voice.get_command(blocking=False)
        
        if command:
            print(f"Recognized: {command}")
        
        time.sleep(1)
    
    voice.stop_background_listening()


# ============================================================================
# EXAMPLE 5: Custom Command Execution
# ============================================================================

def example_custom_commands():
    """
    Execute custom actions based on gaze + voice.
    """
    import cv2
    from gaze_tracking import GazeTracking
    from voice_processor import VoiceProcessor
    from command_executor import CommandExecutor
    
    gaze = GazeTracking()
    voice = VoiceProcessor()
    executor = CommandExecutor()
    
    cap = cv2.VideoCapture(0)
    
    print("Custom Command Demo")
    print("Commands available:")
    print("  'click' - Click at gaze position")
    print("  'type hello' - Type 'hello' at cursor")
    print("  'screenshot' - Take screenshot")
    print("  'open notepad' - Open notepad application")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Track gaze
        gaze.refresh(frame)
        gaze_pos = None
        
        if gaze.pupils_located:
            left = gaze.pupil_left_coords()
            right = gaze.pupil_right_coords()
            if left and right:
                gaze_pos = ((left[0] + right[0]) // 2, (left[1] + right[1]) // 2)
        
        # Listen for command
        command = voice.listen(timeout=1.0)
        
        if command and gaze_pos:
            print(f"\nHeard: {command}")
            
            # Custom command handling
            if 'click' in command.lower():
                executor.left_click(gaze_pos)
                print(f"✓ Clicked at {gaze_pos}")
            
            elif 'type ' in command.lower():
                text = command.lower().replace('type ', '')
                executor.type_text(text)
                print(f"✓ Typed: {text}")
            
            elif 'screenshot' in command.lower():
                if executor.take_screenshot('custom_screenshot.png'):
                    print("✓ Screenshot saved")
            
            elif 'open ' in command.lower():
                app = command.lower().replace('open ', '').strip()
                if executor.open_application(app):
                    print(f"✓ Opening {app}")
        
        # Display
        frame = gaze.annotated_frame()
        if gaze_pos:
            cv2.circle(frame, gaze_pos, 10, (0, 255, 0), 2)
        cv2.imshow("Custom Commands", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    voice.cleanup()


# ============================================================================
# EXAMPLE 6: Real-time Attention Detection
# ============================================================================

def example_attention_detection():
    """
    Detect where user is looking and log attention patterns.
    Useful for concentration tracking, interface heat maps, etc.
    """
    import cv2
    from gaze_tracking import GazeTracking
    from collections import defaultdict
    
    gaze = GazeTracking()
    cap = cv2.VideoCapture(0)
    
    # Heat map: track attention by region
    width, height = 1280, 720
    attention_map = defaultdict(int)
    region_size = 100  # 100x100 pixel regions
    
    print("Attention Detection Demo")
    print("Press 'Q' to exit and see heat map")
    
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        gaze.refresh(frame)
        frame_count += 1
        
        if gaze.pupils_located and frame_count % 5 == 0:  # Every 5 frames
            left = gaze.pupil_left_coords()
            right = gaze.pupil_right_coords()
            
            if left and right:
                gaze_x = (left[0] + right[0]) // 2
                gaze_y = (left[1] + right[1]) // 2
                
                # Quantize to region
                region_x = (gaze_x // region_size) * region_size
                region_y = (gaze_y // region_size) * region_size
                region_key = (region_x, region_y)
                
                attention_map[region_key] += 1
        
        frame = gaze.annotated_frame()
        
        # Display current stats
        cv2.putText(frame, f"Frames: {frame_count}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f"Regions tracked: {len(attention_map)}", (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        cv2.imshow("Attention Detection", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Print heat map
    print("\n=== Attention Heat Map ===")
    if attention_map:
        max_attention = max(attention_map.values())
        for (x, y), count in sorted(attention_map.items(), key=lambda p: -p[1])[:10]:
            bar = "█" * int(count / max_attention * 30)
            print(f"Region ({x:4d}, {y:4d}): {bar} {count}")
    
    cap.release()
    cv2.destroyAllWindows()


# ============================================================================
# EXAMPLE 7: Gesture Recognition (Advanced)
# ============================================================================

def example_gesture_recognition():
    """
    Recognize gaze gestures (swipes, circles) for enhanced interaction.
    """
    import cv2
    from gaze_tracking import GazeTracking
    
    gaze = GazeTracking()
    cap = cv2.VideoCapture(0)
    
    # Gesture tracking
    gaze_history = []
    max_history = 30  # Last 30 frames
    gesture_threshold = 100  # pixels to detect gesture
    
    print("Gaze Gesture Recognition Demo")
    print("Try these gestures:")
    print("  Swipe RIGHT: Look quickly to the right")
    print("  Swipe LEFT: Look quickly to the left")
    print("  Swipe DOWN: Look quickly downward")
    print("  BLINK: Close eyes briefly")
    
    def detect_gesture(history):
        if len(history) < 10:
            return None
        
        start = history[0]
        end = history[-1]
        
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        
        # Detect dominant direction
        if abs(dx) > abs(dy):
            if dx > gesture_threshold:
                return "SWIPE_RIGHT"
            elif dx < -gesture_threshold:
                return "SWIPE_LEFT"
        else:
            if dy > gesture_threshold:
                return "SWIPE_DOWN"
            elif dy < -gesture_threshold:
                return "SWIPE_UP"
        
        return None
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        gaze.refresh(frame)
        
        if gaze.pupils_located:
            left = gaze.pupil_left_coords()
            right = gaze.pupil_right_coords()
            
            if left and right:
                gaze_pos = ((left[0] + right[0]) // 2, (left[1] + right[1]) // 2)
                gaze_history.append(gaze_pos)
                
                if len(gaze_history) > max_history:
                    gaze_history.pop(0)
                
                # Detect gesture
                gesture = detect_gesture(gaze_history)
                if gesture:
                    print(f"Detected: {gesture}")
                    gaze_history.clear()
        
        # Blink detection
        if gaze.is_blinking():
            print("Blink detected!")
        
        frame = gaze.annotated_frame()
        
        # Draw gaze history
        if len(gaze_history) > 1:
            for i in range(len(gaze_history) - 1):
                cv2.line(frame, gaze_history[i], gaze_history[i+1], (255, 0, 0), 1)
        
        cv2.imshow("Gesture Recognition", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()


# ============================================================================
# EXAMPLE 8: Integration with External Applications
# ============================================================================

def example_application_control():
    """
    Control external applications (web browser, text editor, etc).
    """
    from command_executor import CommandExecutor, SmartExecutor
    import time
    
    executor = SmartExecutor()
    
    print("=== Application Control Demo ===\n")
    
    # Example 1: Open notepad and type
    print("1. Opening Notepad...")
    executor.open_application('notepad')
    time.sleep(2)
    
    print("2. Typing text...")
    executor.type_text('Hello from VocalIris OS!')
    time.sleep(1)
    
    # Example 2: Copy/Paste operations
    print("3. Copy/Paste...")
    executor.key_combination('ctrl', 'a')  # Select all
    executor.copy_to_clipboard()           # Copy
    time.sleep(1)
    executor.paste_from_clipboard()        # Paste
    time.sleep(1)
    
    # Example 3: Window management
    print("4. Window management...")
    executor.key_combination('alt', 'tab')  # Switch windows
    time.sleep(2)
    
    # Example 4: Browser navigation
    print("5. Browser control...")
    executor.press_key('f11')  # Fullscreen
    time.sleep(1)
    executor.key_combination('ctrl', 'w')  # Close tab
    
    print("\n✓ Application control demo complete")


# ============================================================================
# EXAMPLE 9: Real-time Performance Monitoring
# ============================================================================

def example_performance_monitoring():
    """
    Monitor and display real-time performance metrics.
    """
    import cv2
    import time
    from gaze_tracking import GazeTracking
    
    gaze = GazeTracking()
    cap = cv2.VideoCapture(0)
    
    # Performance tracking
    frame_times = []
    max_frames = 100
    
    print("Performance Monitoring Demo")
    
    while True:
        start_time = time.time()
        
        ret, frame = cap.read()
        if not ret:
            break
        
        # Process gaze
        gaze.refresh(frame)
        
        # Measure time
        elapsed = time.time() - start_time
        frame_times.append(elapsed)
        
        if len(frame_times) > max_frames:
            frame_times.pop(0)
        
        # Calculate metrics
        avg_time = sum(frame_times) / len(frame_times)
        fps = 1.0 / avg_time if avg_time > 0 else 0
        max_time = max(frame_times)
        min_time = min(frame_times)
        
        # Display on frame
        frame = gaze.annotated_frame()
        
        text_info = [
            f"FPS: {fps:.1f}",
            f"Avg Time: {avg_time*1000:.2f}ms",
            f"Max Time: {max_time*1000:.2f}ms",
            f"Min Time: {min_time*1000:.2f}ms",
        ]
        
        for i, text in enumerate(text_info):
            cv2.putText(frame, text, (10, 30 + i*25),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        cv2.imshow("Performance Monitoring", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    print(f"\nAverage FPS: {fps:.1f}")
    print(f"Average Frame Time: {avg_time*1000:.2f}ms")
    
    cap.release()
    cv2.destroyAllWindows()


# ============================================================================
# EXAMPLE 10: Customization & Configuration
# ============================================================================

def example_custom_configuration():
    """
    Show how to customize VocalIris OS behavior.
    """
    from vocal_iris_os import VocalIrisOS
    
    # Create system with custom settings
    system = VocalIrisOS(debug_mode=True)
    
    # Customize gaze tracking
    system.max_history = 10  # Increase smoothing
    system.sticky_threshold = 50  # Make sticky target more sensitive
    
    # Customize voice commands
    custom_commands = {
        'click': 'LEFT_CLICK',
        'open file': 'FILE_OPEN',
        'next page': 'PAGE_NEXT',
        'previous page': 'PAGE_PREV',
    }
    system.voice_processor.COMMAND_KEYWORDS.update(custom_commands)
    
    # Customize mouse speed
    system.command_executor.MOUSE_SPEED = 0.05  # Faster
    
    print("Custom configuration loaded")
    print("Modified settings:")
    print(f"  Gaze smoothing: {system.max_history} frames")
    print(f"  Sticky threshold: {system.sticky_threshold}px")
    print(f"  Mouse speed: {system.command_executor.MOUSE_SPEED}s")


# ============================================================================
# Main: Run Examples
# ============================================================================

if __name__ == "__main__":
    import sys
    
    examples = {
        '1': ('Basic Usage', example_basic_usage),
        '2': ('Gaze Tracking Only', example_gaze_tracking_only),
        '3': ('Voice Commands Only', example_voice_commands_only),
        '4': ('Advanced Voice', example_advanced_voice),
        '5': ('Custom Commands', example_custom_commands),
        '6': ('Attention Detection', example_attention_detection),
        '7': ('Gesture Recognition', example_gesture_recognition),
        '8': ('Application Control', example_application_control),
        '9': ('Performance Monitoring', example_performance_monitoring),
        '10': ('Custom Configuration', example_custom_configuration),
    }
    
    print("\n" + "="*70)
    print("VocalIris OS - Usage Examples")
    print("="*70 + "\n")
    
    print("Available examples:")
    for key, (name, _) in examples.items():
        print(f"  {key}. {name}")
    print("  0. Exit\n")
    
    choice = input("Select example (0-10): ").strip()
    
    if choice in examples:
        name, func = examples[choice]
        print(f"\n▶  Running: {name}\n")
        try:
            func()
        except KeyboardInterrupt:
            print("\n\n⚠  Interrupted by user")
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
    elif choice == '0':
        print("Exiting...")
    else:
        print("Invalid selection")
