import os

import cv2


CASCADE_PATH = os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml")


def detect_faces(frame_paths: list[str], output_dir: str) -> dict:
	"""Locate faces in sampled frames and save crops for model inference."""
	detector = cv2.CascadeClassifier(CASCADE_PATH)
	if detector.empty():
		raise RuntimeError("OpenCV's bundled face detector could not be loaded.")

	face_crops = []
	frames_with_faces = []
	for frame_index, frame_path in enumerate(frame_paths):
		frame = cv2.imread(frame_path)
		if frame is None:
			continue
		gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
		faces = detector.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40))
		if len(faces):
			frames_with_faces.append(frame_index)
		for face_index, (x, y, width, height) in enumerate(faces):
			crop_path = os.path.join(output_dir, f"face_{frame_index:04d}_{face_index:02d}.jpg")
			cv2.imwrite(crop_path, frame[y:y + height, x:x + width])
			face_crops.append({"frame_index": frame_index, "path": crop_path})

	return {
		"faces_detected": len(face_crops),
		"frames_with_faces": frames_with_faces,
		"face_crops": face_crops,
	}
