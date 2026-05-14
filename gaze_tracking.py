"""
Gaze Tracking Module - Extracted from provided code with enhancements
Combines eye detection and pupil tracking
"""

from pathlib import Path
import cv2
import dlib
import numpy as np
from typing import Optional, Tuple


class Pupil:
    """
    Detects the iris/pupil and estimates pupil position.
    """
    
    def __init__(self, eye_frame, threshold):
        """
        Initialize pupil detector.
        
        Args:
            eye_frame: Frame containing isolated eye
            threshold: Binarization threshold value
        """
        self.iris_frame = None
        self.threshold = threshold
        self.x = None
        self.y = None
        self.detect_iris(eye_frame)

    @staticmethod
    def image_processing(eye_frame, threshold):
        """
        Process eye frame to isolate iris/pupil.
        
        Args:
            eye_frame: Frame containing an eye
            threshold: Threshold value for binarization
            
        Returns:
            Processed frame with isolated iris
        """
        kernel = np.ones((3, 3), np.uint8)
        new_frame = cv2.bilateralFilter(eye_frame, 10, 15, 15)
        new_frame = cv2.erode(new_frame, kernel, iterations=3)
        new_frame = cv2.threshold(new_frame, threshold, 255, cv2.THRESH_BINARY)[1]
        return new_frame

    def detect_iris(self, eye_frame):
        """
        Detect iris and calculate pupil centroid.
        
        Args:
            eye_frame: Frame containing an eye
        """
        self.iris_frame = self.image_processing(eye_frame, self.threshold)
        contours, _ = cv2.findContours(self.iris_frame, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)[-2:]
        contours = sorted(contours, key=cv2.contourArea)
        try:
            moments = cv2.moments(contours[-2])
            self.x = int(moments['m10'] / moments['m00'])
            self.y = int(moments['m01'] / moments['m00'])
        except (IndexError, ZeroDivisionError):
            pass


class Calibration:
    """
    Calibrates pupil detection by finding optimal threshold.
    """
    
    def __init__(self):
        """Initialize calibration."""
        self.nb_frames = 20
        self.thresholds_left = []
        self.thresholds_right = []

    def is_complete(self):
        """Check if calibration is complete."""
        return (len(self.thresholds_left) >= self.nb_frames and 
                len(self.thresholds_right) >= self.nb_frames)

    def threshold(self, side):
        """
        Get threshold for given eye.
        
        Args:
            side: 0 for left eye, 1 for right eye
            
        Returns:
            Threshold value
        """
        if side == 0:
            return int(sum(self.thresholds_left) / len(self.thresholds_left)) if self.thresholds_left else 50
        elif side == 1:
            return int(sum(self.thresholds_right) / len(self.thresholds_right)) if self.thresholds_right else 50

    @staticmethod
    def iris_size(frame):
        """
        Calculate iris size as percentage of eye frame.
        
        Args:
            frame: Binarized eye frame
            
        Returns:
            Iris size percentage
        """
        frame = frame[5:-5, 5:-5]
        height, width = frame.shape[:2]
        nb_pixels = height * width
        nb_blacks = nb_pixels - cv2.countNonZero(frame)
        return nb_blacks / nb_pixels

    @staticmethod
    def find_best_threshold(eye_frame):
        """
        Find optimal binarization threshold.
        
        Args:
            eye_frame: Eye frame to analyze
            
        Returns:
            Best threshold value
        """
        average_iris_size = 0.48
        trials = {}
        for threshold in range(5, 100, 5):
            iris_frame = Pupil.image_processing(eye_frame, threshold)
            trials[threshold] = Calibration.iris_size(iris_frame)
        best_threshold, iris_size = min(trials.items(), 
                                       key=lambda p: abs(p[1] - average_iris_size))
        return best_threshold

    def evaluate(self, eye_frame, side):
        """
        Improve calibration with new eye frame.
        
        Args:
            eye_frame: Eye frame to evaluate
            side: 0 for left eye, 1 for right eye
        """
        threshold = self.find_best_threshold(eye_frame)
        if side == 0:
            self.thresholds_left.append(threshold)
        elif side == 1:
            self.thresholds_right.append(threshold)


class Eye:
    """
    Isolates eye region and performs pupil detection.
    """
    
    LEFT_EYE_POINTS = [36, 37, 38, 39, 40, 41]
    RIGHT_EYE_POINTS = [42, 43, 44, 45, 46, 47]

    def __init__(self, original_frame, landmarks, side, calibration):
        """
        Initialize eye detector.
        
        Args:
            original_frame: Full face frame
            landmarks: Facial landmarks
            side: 0 for left eye, 1 for right eye
            calibration: Calibration object
        """
        self.frame = None
        self.origin = None
        self.center = None
        self.pupil = None
        self.landmark_points = None
        self.blinking = None

        self._analyze(original_frame, landmarks, side, calibration)

    @staticmethod
    def _middle_point(p1, p2):
        """Calculate midpoint between two points."""
        x = int((p1.x + p2.x) / 2)
        y = int((p1.y + p2.y) / 2)
        return (x, y)

    def _isolate(self, frame, landmarks, points):
        """Isolate eye region from face."""
        region = np.array([(landmarks.part(point).x, landmarks.part(point).y) 
                          for point in points])
        region = region.astype(np.int32)
        self.landmark_points = region

        height, width = frame.shape[:2]
        black_frame = np.zeros((height, width), np.uint8)
        mask = np.full((height, width), 255, np.uint8)
        cv2.fillPoly(mask, [region], (0, 0, 0))
        eye = cv2.bitwise_not(black_frame, frame.copy(), mask=mask)

        margin = 5
        min_x = np.min(region[:, 0]) - margin
        max_x = np.max(region[:, 0]) + margin
        min_y = np.min(region[:, 1]) - margin
        max_y = np.max(region[:, 1]) + margin

        self.frame = eye[min_y:max_y, min_x:max_x]
        self.origin = (min_x, min_y)

        height, width = self.frame.shape[:2]
        self.center = (width / 2, height / 2)

    def _blinking_ratio(self, landmarks, points):
        """Calculate eye openness ratio."""
        import math
        
        left = (landmarks.part(points[0]).x, landmarks.part(points[0]).y)
        right = (landmarks.part(points[3]).x, landmarks.part(points[3]).y)
        top = self._middle_point(landmarks.part(points[1]), landmarks.part(points[2]))
        bottom = self._middle_point(landmarks.part(points[5]), landmarks.part(points[4]))

        eye_width = math.hypot((left[0] - right[0]), (left[1] - right[1]))
        eye_height = math.hypot((top[0] - bottom[0]), (top[1] - bottom[1]))

        try:
            ratio = eye_width / eye_height
        except ZeroDivisionError:
            ratio = None

        return ratio

    def _analyze(self, original_frame, landmarks, side, calibration):
        """Analyze eye frame and detect pupil."""
        if side == 0:
            points = self.LEFT_EYE_POINTS
        elif side == 1:
            points = self.RIGHT_EYE_POINTS
        else:
            return

        self.blinking = self._blinking_ratio(landmarks, points)
        self._isolate(original_frame, landmarks, points)

        if not calibration.is_complete():
            calibration.evaluate(self.frame, side)

        threshold = calibration.threshold(side)
        self.pupil = Pupil(self.frame, threshold)


class GazeTracking:
    """
    Main gaze tracking class.
    Detects face, extracts eyes, and tracks pupil position.
    """

    def __init__(self):
        """Initialize gaze tracker."""
        self.frame = None
        self.eye_left = None
        self.eye_right = None
        self.calibration = Calibration()

        self._face_detector = dlib.get_frontal_face_detector()

        # Load facial landmarks model
        model_path = Path(__file__).parent / "trained_models" / "shape_predictor_68_face_landmarks.dat"
        
        # Fallback: look for model in common locations
        if not model_path.exists():
            import os
            possible_paths = [
                "./trained_models/shape_predictor_68_face_landmarks.dat",
                "../trained_models/shape_predictor_68_face_landmarks.dat",
                "/usr/local/lib/python3.8/site-packages/dlib_models/shape_predictor_68_face_landmarks.dat"
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    model_path = Path(path)
                    break
        
        try:
            self._predictor = dlib.shape_predictor(str(model_path))
        except RuntimeError as e:
            print(f"⚠️  Warning: Could not load shape predictor model")
            print(f"   Download from: https://github.com/davisking/dlib-models")
            print(f"   Place in: ./trained_models/shape_predictor_68_face_landmarks.dat")
            self._predictor = None

    @property
    def pupils_located(self):
        """Check if pupils are detected."""
        try:
            if self.eye_left and self.eye_left.pupil:
                int(self.eye_left.pupil.x)
                int(self.eye_left.pupil.y)
            if self.eye_right and self.eye_right.pupil:
                int(self.eye_right.pupil.x)
                int(self.eye_right.pupil.y)
            return self.eye_left is not None and self.eye_right is not None
        except (AttributeError, TypeError):
            return False

    def _analyze(self):
        """Detect face and initialize Eye objects."""
        frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
        faces = self._face_detector(frame)

        try:
            if self._predictor:
                landmarks = self._predictor(frame, faces[0])
                self.eye_left = Eye(frame, landmarks, 0, self.calibration)
                self.eye_right = Eye(frame, landmarks, 1, self.calibration)
        except IndexError:
            self.eye_left = None
            self.eye_right = None

    def refresh(self, frame):
        """
        Refresh with new frame and analyze.
        
        Args:
            frame: Input video frame
        """
        self.frame = frame
        self._analyze()

    def pupil_left_coords(self) -> Optional[Tuple[int, int]]:
        """Get left pupil coordinates."""
        if self.pupils_located:
            x = self.eye_left.origin[0] + self.eye_left.pupil.x
            y = self.eye_left.origin[1] + self.eye_left.pupil.y
            return (x, y)
        return None

    def pupil_right_coords(self) -> Optional[Tuple[int, int]]:
        """Get right pupil coordinates."""
        if self.pupils_located:
            x = self.eye_right.origin[0] + self.eye_right.pupil.x
            y = self.eye_right.origin[1] + self.eye_right.pupil.y
            return (x, y)
        return None

    def horizontal_ratio(self) -> Optional[float]:
        """
        Get horizontal gaze ratio (0.0=right, 0.5=center, 1.0=left).
        
        Returns:
            Ratio between 0 and 1 or None
        """
        if self.pupils_located:
            pupil_left = self.eye_left.pupil.x / (self.eye_left.center[0] * 2 - 10)
            pupil_right = self.eye_right.pupil.x / (self.eye_right.center[0] * 2 - 10)
            return (pupil_left + pupil_right) / 2
        return None

    def vertical_ratio(self) -> Optional[float]:
        """
        Get vertical gaze ratio (0.0=top, 0.5=center, 1.0=bottom).
        
        Returns:
            Ratio between 0 and 1 or None
        """
        if self.pupils_located:
            pupil_left = self.eye_left.pupil.y / (self.eye_left.center[1] * 2 - 10)
            pupil_right = self.eye_right.pupil.y / (self.eye_right.center[1] * 2 - 10)
            return (pupil_left + pupil_right) / 2
        return None

    def is_right(self) -> bool:
        """Check if looking right."""
        if self.pupils_located:
            return self.horizontal_ratio() <= 0.35
        return False

    def is_left(self) -> bool:
        """Check if looking left."""
        if self.pupils_located:
            return self.horizontal_ratio() >= 0.65
        return False

    def is_center(self) -> bool:
        """Check if looking at center."""
        if self.pupils_located:
            return not self.is_right() and not self.is_left()
        return False

    def is_blinking(self) -> bool:
        """Check if eyes are blinking/closed."""
        if self.pupils_located:
            blinking_ratio = (self.eye_left.blinking + self.eye_right.blinking) / 2
            return blinking_ratio > 3.8
        return False

    def annotated_frame(self) -> np.ndarray:
        """
        Get frame with pupils marked.
        
        Returns:
            Frame with gaze cursor overlay
        """
        frame = self.frame.copy()

        if self.pupils_located:
            color = (0, 255, 0)
            x_left, y_left = self.pupil_left_coords()
            x_right, y_right = self.pupil_right_coords()
            
            # Draw crosshairs at pupils
            cv2.line(frame, (x_left - 5, y_left), (x_left + 5, y_left), color)
            cv2.line(frame, (x_left, y_left - 5), (x_left, y_left + 5), color)
            cv2.line(frame, (x_right - 5, y_right), (x_right + 5, y_right), color)
            cv2.line(frame, (x_right, y_right - 5), (x_right, y_right + 5), color)

        return frame
