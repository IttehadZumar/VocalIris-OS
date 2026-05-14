import dlib

# Point to the subfolder
predictor_path = "trained_models/shape_predictor_68_face_landmarks.dat"

detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(predictor_path)

print("Success! Model loaded from the trained_models folder.")
