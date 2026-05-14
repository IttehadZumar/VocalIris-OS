"""
VocalIris OS - Installation and Setup Guide
A hands-free multimodal control system combining eye-tracking with voice commands
"""

# ============================================================================
# INSTALLATION GUIDE
# ============================================================================

INSTALLATION_INSTRUCTIONS = """

╔═══════════════════════════════════════════════════════════════════════════╗
║                   VOCALiris OS - SETUP INSTRUCTIONS                      ║
║             Hands-Free Control: Eye Tracking + Voice Commands             ║
╚═══════════════════════════════════════════════════════════════════════════╝

## SYSTEM REQUIREMENTS

### Hardware
  • Computer: Windows 10+, macOS 10.14+, or Linux (Ubuntu 18.04+)
  • Webcam: 720p or higher resolution (USB 2.0 or better)
  • Microphone: USB or built-in (noise-canceling recommended)
  • RAM: 4GB minimum (8GB recommended)
  • CPU: Quad-core recommended for real-time processing

### Software Prerequisites
  • Python 3.7+ (Python 3.9+ recommended)
  • pip package manager
  • cmake (for dlib compilation)

## STEP 1: INSTALL PYTHON DEPENDENCIES

### Option A: Standard Installation (Recommended)
```bash
# Create virtual environment
python -m venv vocaliris_env
source vocaliris_env/bin/activate  # On Windows: vocaliris_env\\Scripts\\activate


# Install core dependencies
pip install --upgrade pip
pip install opencv-python
pip install dlib
pip install numpy
pip install pyautogui
pip install SpeechRecognition
pip install pydub
```

### Option B: Full Installation (With All Features)
```bash
# Create virtual environment
python -m venv vocaliris_env
source vocalirs_env/bin/activate

# Core packages
pip install opencv-python
pip install dlib
pip install numpy
pip install pyautogui

# Speech Recognition
pip install SpeechRecognition
pip install pydub
pip install vosk  # For offline speech recognition
pip install pyaudio

# Optional: Advanced Features
pip install noisereduce  # For noise filtering
pip install pyannote.audio  # For Voice Activity Detection (VAD)
pip install pygetwindow  # For Windows management (Windows only)
pip install pywin32  # For Windows-specific features (Windows only)
```

## STEP 2: DOWNLOAD DLIB FACIAL LANDMARK MODEL

The system requires a pre-trained facial landmark model:

```bash
# Create models directory
mkdir -p trained_models

# Download the model (68-point landmark predictor)
wget https://github.com/davisking/dlib-models/raw/master/shape_predictor_68_face_landmarks.dat.bz2

# Extract the model
bzip2 -d shape_predictor_68_face_landmarks.dat.bz2
mv shape_predictor_68_face_landmarks.dat trained_models/
```

**Alternative:** Download manually from:
https://github.com/davisking/dlib-models

## STEP 3: VERIFY INSTALLATION

```bash
# Test all imports
python test_installation.py
```

## STEP 4: MICROPHONE & CAMERA SETUP

### On Linux:
```bash
# Check audio devices
arecord -l

# Test camera
python -c "import cv2; print(cv2.__version__)"
```

### On macOS:
```bash
# Grant microphone permissions in System Preferences
# Security & Privacy > Microphone > Allow access

# Test audio input
python -c "import pyaudio; print(pyaudio.PyAudio())"
```

### On Windows:
```bash
# Check audio settings in Control Panel
# Sound Settings > Input > Microphone

# Ensure microphone is set as default device
```

## STEP 5: RUN VOCALiris OS

```bash
# Activate virtual environment
source vocalirs_env/bin/activate

# Run the main application
python vocal_iris_os.py

# The system will start with:
# 1. Calibration (look at screen corners)
# 2. Voice listener (ready for commands)
# 3. Real-time gaze tracking display
```

## KEYBOARD SHORTCUTS (During Operation)

  • Q or ESC      - Exit application
  • C             - Start calibration
  • Z             - Toggle zoom mode
  • S             - Toggle rest mode (pause eye tracking)

## VOICE COMMANDS

### Navigation & Interaction
  • "Click" / "Select" / "Activate"    - Left-click at gaze position
  • "Right Click" / "Options" / "Menu" - Open context menu
  • "Double Click" / "Open"            - Double-click at gaze position
  • "Scroll Up" / "Scroll Down"        - Scroll in direction

### Advanced Features
  • "Zoom" / "Magnify"       - Toggle zoom magnification
  • "Calibrate" / "Recal"    - Start recalibration
  • "Stop" / "Freeze" / "Pause"  - Rest mode (pause eye tracking)
  • "Wake" / "Resume"        - Exit rest mode
  • "Type [text]"            - Type text (e.g., "Type Hello")
  • "Drag"                   - Start dragging
  • "Drop"                   - Release drag

## TROUBLESHOOTING

### Issue: "No module named 'dlib'"
**Solution:**
```bash
# dlib requires C++ compiler and cmake
# Windows: Install Visual Studio Build Tools
# macOS: xcode-select --install
# Linux: sudo apt-get install build-essential cmake

pip install cmake
pip install dlib
```

### Issue: "Shape predictor model not found"
**Solution:**
- Ensure trained_models/shape_predictor_68_face_landmarks.dat exists
- Check file path and permissions

### Issue: "No microphone input"
**Solution:**
- Check system audio settings (microphone enabled & not muted)
- Test with: python -m speech_recognition

### Issue: "Camera not detected"
**Solution:**
- Verify webcam is connected
- Check permissions: sudo usermod -a -G video $USER (Linux)
- Test with: python -c "import cv2; cv2.VideoCapture(0).isOpened()"

### Issue: "Gaze tracking is jittery"
**Solution:**
- Improve lighting (avoid backlighting)
- Move closer to camera (30-60cm distance)
- Increase gaze smoothing window in vocal_iris_os.py:
  * Change `self.max_history = 5` to `self.max_history = 10`

### Issue: "High CPU usage"
**Solution:**
- Reduce camera resolution (set to 720p)
- Increase gaze smoothing
- Disable debug mode: `VocalIrisOS(debug_mode=False)`
- Close other applications

## PERFORMANCE TIPS

1. **Optimal Setup:**
   - Lighting: Well-lit room, no backlighting
   - Camera Distance: 30-60cm from face
   - Head Position: Facing camera directly
   - Screen: Calibrate before each session

2. **Accuracy Improvement:**
   - Wear glasses at consistent angle (if applicable)
   - Keep camera at eye level
   - Ensure steady lighting throughout session
   - Take short breaks (eye fatigue affects tracking)

3. **Speed Optimization:**
   - Reduce camera resolution (from 1080p to 720p)
   - Disable debug mode for 15-20% speed increase
   - Use GPU acceleration if available (RTX cards)
   - Increase gaze smoothing (reduces CPU, slight lag trade-off)

## ADVANCED CUSTOMIZATION

### Adjust Gaze Smoothing
In `vocal_iris_os.py`:
```python
self.max_history = 5  # Increase for smoother but slower gaze
```

### Adjust Sticky Target Sensitivity
```python
self.sticky_threshold = 30  # Pixels to snap to nearby UI elements
```

### Adjust Voice Command Sensitivity
In `voice_processor.py`:
```python
self.confidence_threshold = 0.5  # Lower = more sensitive but prone to false positives
```

### Adjust Mouse Speed
In `command_executor.py`:
```python
MOUSE_SPEED = 0.1  # Seconds to move mouse (lower = faster)
```

## UNINSTALL

```bash
# Deactivate virtual environment
deactivate

# Remove virtual environment
rm -rf vocalirs_env
```

## NEXT STEPS

1. **Run calibration** - Follow on-screen instructions
2. **Practice voice commands** - Speak clearly and naturally
3. **Adjust settings** - Fine-tune for your setup
4. **Read documentation** - Check docstrings in code files

## GETTING HELP

- GitHub: [VocalIris Project]
- Issues: Submit bugs and feature requests
- Discussions: Community support forum

## CITATIONS & ACKNOWLEDGMENTS

- dlib (face detection): http://dlib.net/
- OpenCV (computer vision): https://opencv.org/
- SpeechRecognition (voice input): https://github.com/Uberi/speech_recognition
- Inspired by Tobii eye-tracking technology

---

Created with ❤️ for accessibility and HCI innovation
"""

# ============================================================================
# TEST INSTALLATION SCRIPT
# ============================================================================

import sys

def test_installation():
    """Test all required dependencies."""
    
    print("\n" + "="*70)
    print("VocalIris OS - Dependency Check")
    print("="*70 + "\n")
    
    dependencies = {
        "cv2": "OpenCV",
        "numpy": "NumPy",
        "dlib": "dlib",
        "pyautogui": "PyAutoGUI",
        "speech_recognition": "SpeechRecognition",
    }
    
    optional_dependencies = {
        "vosk": "Vosk (offline speech)",
        "noisereduce": "Noise Reduction",
        "pyannote": "Voice Activity Detection",
    }
    
    failed = []
    optional_failed = []
    
    # Test required dependencies
    print("REQUIRED DEPENDENCIES:")
    print("-" * 70)
    for module, name in dependencies.items():
        try:
            __import__(module)
            print(f"✓ {name:<30} installed")
        except ImportError:
            print(f"✗ {name:<30} MISSING")
            failed.append(name)
    
    # Test optional dependencies
    print("\nOPTIONAL DEPENDENCIES:")
    print("-" * 70)
    for module, name in optional_dependencies.items():
        try:
            __import__(module)
            print(f"✓ {name:<30} installed")
        except ImportError:
            print(f"◇ {name:<30} not installed (optional)")
            optional_failed.append(name)
    
    # Check for trained model
    print("\nMODEL FILES:")
    print("-" * 70)
    from pathlib import Path
    model_path = Path("trained_models/shape_predictor_68_face_landmarks.dat")
    if model_path.exists():
        print(f"✓ Shape predictor model          found ({model_path.stat().st_size // (1024*1024)}MB)")
    else:
        print(f"✗ Shape predictor model          MISSING")
        print(f"  Download from: https://github.com/davisking/dlib-models")
        failed.append("Shape predictor model")
    
    # Summary
    print("\n" + "="*70)
    if not failed:
        print("✓ All required dependencies installed!")
        if optional_failed:
            print(f"  ({len(optional_failed)} optional packages not installed)")
        print("\nYou can now run: python vocal_iris_os.py")
    else:
        print(f"✗ Installation incomplete ({len(failed)} missing)")
        print("\nInstall missing packages with:")
        print(f"  pip install {' '.join([d.lower().replace(' ', '') for d in failed if d != 'Shape predictor model'])}")
    
    print("="*70 + "\n")
    
    return len(failed) == 0


if __name__ == "__main__":
    success = test_installation()
    sys.exit(0 if success else 1)
