import cv2
import sqlite3
import sys
import time
import platform

# Initialize video capture and face detection with Mac optimization
print("Initializing camera...")

# Mac-specific camera initialization
if platform.system() == "Darwin":  # macOS
    print("🍎 Detected macOS - Using optimized camera settings")
    video = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)
    if video.isOpened():
        # Test if camera works
        ret, _ = video.read()
        if not ret:
            print("⚠️  Built-in camera not responding, trying default backend...")
            video.release()
            video = cv2.VideoCapture(0)
    else:
        video = cv2.VideoCapture(0)
else:
    video = cv2.VideoCapture(0)

# Check if camera is opened successfully
if not video.isOpened():
    print("Error: Could not open camera. Please check:")
    print("1. Camera is connected properly")
    print("2. No other application is using the camera")
    print("3. Camera permissions are granted to Terminal/Python")
    print("4. Try using a different camera index (0, 1, 2, etc.)")
    sys.exit(1)

# Set camera properties for better compatibility
video.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
video.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
video.set(cv2.CAP_PROP_FPS, 30)

# Wait a moment for camera to initialize
time.sleep(2)

facedetect = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

# Check if face cascade is loaded
if facedetect.empty():
    print("Error: Could not load face detection classifier")
    print("Make sure 'haarcascade_frontalface_default.xml' exists in the current directory")
    video.release()
    sys.exit(1)

# Connect to SQLite database (create if not exists)
conn = sqlite3.connect('data/attendance.db')
cursor = conn.cursor()

# Create table if not exists
cursor.execute('''CREATE TABLE IF NOT EXISTS faces
                  (id INTEGER PRIMARY KEY AUTOINCREMENT,
                   name TEXT,
                   face_data BLOB)''')

# Initialize variables
faces_data = []
i = 0
name = input("Enter Your Name: ")

print(f"Starting face capture for {name}...")
print("Position your face in front of the camera and press 'q' when done")

while True:
    ret, frame = video.read()
    
    # Check if frame was read successfully
    if not ret or frame is None:
        print("Error: Could not read frame from camera")
        continue
    
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = facedetect.detectMultiScale(gray, 1.3, 5)

    for (x, y, w, h) in faces:
        crop_img = frame[y:y + h, x:x + w, :]
        resized_img = cv2.resize(crop_img, (50, 50))

        # Convert image to bytes for storage in SQLite
        resized_img_bytes = resized_img.tobytes()

        # Store every 10th detected face
        if len(faces_data) <= 100 and i % 10 == 0:
            faces_data.append((name, resized_img_bytes))

        i += 1
        cv2.putText(frame, f"Faces Collected: {len(faces_data)}", (50, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (50, 50, 255),
                    1)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (50, 50, 255), 1)

    cv2.imshow("Frame", frame)
    k = cv2.waitKey(1)

    # Exit loop if 'q' is pressed or 100 faces are collected
    if k == ord('q') or len(faces_data) == 100:
        break

print(f"\nCollected {len(faces_data)} face samples for {name}")

# Insert faces_data into SQLite database
if faces_data:
    cursor.executemany('INSERT INTO faces (name, face_data) VALUES (?, ?)', faces_data)
    conn.commit()
    print(f"Successfully saved {len(faces_data)} face samples to database")
else:
    print("No face samples were collected")

# Close video capture and SQLite connection
video.release()
cv2.destroyAllWindows()
conn.close()
print("Face registration completed!")
