import cv2
import sqlite3
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sklearn.metrics.pairwise import cosine_similarity
import pyttsx3
import torch
from facenet_pytorch import InceptionResnetV1


def speak(str1):
    engine = pyttsx3.init()
    engine.say(str1)
    engine.runAndWait()


facenet_model = InceptionResnetV1(pretrained='casia-webface').eval()


def get_embedding(face_pixels):
    """
    Generate face embedding using FaceNet model

    Args:
        face_pixels (numpy.ndarray): Input face image

    Returns:
        numpy.ndarray: Face embedding vector
    """
    if face_pixels.shape[:2] != (160, 160):
        face_pixels = cv2.resize(face_pixels, (160, 160))

    face_pixels = face_pixels.astype('float32')
    mean, std = face_pixels.mean(), face_pixels.std()
    face_pixels = (face_pixels - mean) / std
    samples = np.expand_dims(face_pixels, axis=0)
    samples = torch.tensor(samples).permute(0, 3, 1, 2)
    with torch.no_grad():
        yhat = facenet_model(samples)
    return yhat[0].numpy()


print("Initializing camera...")
video = cv2.VideoCapture(0)

# Check if camera is opened successfully
if not video.isOpened():
    print("Error: Could not open camera. Please check:")
    print("1. Camera is connected properly")
    print("2. No other application is using the camera")
    print("3. Camera permissions are granted to Terminal/Python")
    print("4. Try using a different camera index (0, 1, 2, etc.)")
    exit(1)

# Set camera properties for better compatibility
video.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
video.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
video.set(cv2.CAP_PROP_FPS, 30)

facedetect = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

# Check if face cascade is loaded
if facedetect.empty():
    print("Error: Could not load face detection classifier")
    print("Make sure 'haarcascade_frontalface_default.xml' exists in the current directory")
    video.release()
    exit(1)

conn = sqlite3.connect('data/attendance.db')
cursor = conn.cursor()
cursor.execute("SELECT name, face_data FROM faces")
data = cursor.fetchall()

LABELS = []
EMBEDDINGS = []
for row in data:
    name, face_data = row
    face_np = np.frombuffer(face_data, dtype=np.uint8).reshape(50, 50, 3)
    embedding = get_embedding(face_np)
    LABELS.append(name)
    EMBEDDINGS.append(embedding)

LABELS = np.array(LABELS)
EMBEDDINGS = np.array(EMBEDDINGS)

print(f"Loaded {len(LABELS)} registered students: {', '.join(LABELS)}")
print("Starting attendance system...")
print("Press 'q' to quit")

# Use proper path separators for cross-platform compatibility
csv_file = "Attendance/Attendance_.csv"
late_attendance_file = "Attendance/late_attendance_record.csv"

# Create attendance directory if it doesn't exist
import os
os.makedirs("Attendance", exist_ok=True)

# Initialize CSV files if they don't exist
if not os.path.exists(csv_file):
    pd.DataFrame(columns=["Name", "Time", "Date"]).to_csv(csv_file, index=False)

if not os.path.exists(late_attendance_file):
    pd.DataFrame(columns=["Name", "Time", "Date"]).to_csv(late_attendance_file, index=False)

attendance_df = pd.read_csv(csv_file)
late_attendance_df = pd.read_csv(late_attendance_file)

yesterday_date = (datetime.now() - timedelta(1)).strftime("%d-%m-%Y")
current_date = datetime.now().strftime("%d-%m-%Y")

absentees_marked = False

while True:
    ret, frame = video.read()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = facedetect.detectMultiScale(gray, 1.3, 5)

    current_time = datetime.now().strftime("%H:%M:%S")
    current_time_obj = datetime.strptime(current_time, "%H:%M:%S")
    cutoff_time = datetime.strptime("09:00:00", "%H:%M:%S")

    for (x, y, w, h) in faces:
        crop_img = frame[y:y + h, x:x + w, :]
        resized_img = cv2.resize(crop_img, (160, 160))
        embedding = get_embedding(resized_img)

        similarities = cosine_similarity([embedding], EMBEDDINGS)
        best_match_idx = np.argmax(similarities)
        output = LABELS[best_match_idx]

        if similarities[0][best_match_idx] > 0.7:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 1)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (50, 50, 255), 2)
            cv2.rectangle(frame, (x, y - 60), (x + w, y), (50, 50, 255), -1)
            cv2.putText(frame, str(output), (x, y - 35), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 1)
        else:
            output = "Unknown"
            cv2.putText(frame, output, (x, y - 35), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 1)

    cv2.putText(frame, current_time, (frame.shape[1] - 200, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 2)


    cv2.imshow("Frame", frame)

    k = cv2.waitKey(5)
    if k == ord('o'):
        reason = ""
        late_duration = current_time_obj - cutoff_time
        marked_attendance = False

        # Determine attendance status
        if current_time <= "9:05:00":
            present = 1
            speak("Attendance Taken..")
            marked_attendance = True
        else:
            present = 1
            speak("You're late. So you were marked as present but must provide a reason for being late.")
            reason = input("Please type the reason for being late: ")

        for (x, y, w, h) in faces:
            crop_img = frame[y:y + h, x:x + w, :]
            resized_img = cv2.resize(crop_img, (160, 160))
            embedding = get_embedding(resized_img)

            similarities = cosine_similarity([embedding], EMBEDDINGS)
            best_match_idx = np.argmax(similarities)
            output = LABELS[best_match_idx]

            if similarities[0][best_match_idx] > 0.7:
                if current_date in attendance_df.columns:
                    attendance_df.loc[attendance_df['names'] == output, current_date] = present
                    marked_attendance = True

                    if current_time > "9:05:00":
                        late_attendance_df[current_date] = late_attendance_df[current_date].astype('object')
                        late_attendance_df.loc[
                            late_attendance_df['name'] == output, current_date] = f"{reason} ({current_time})"
                        speak("Your reason taken...")
                        late_attendance_df.to_csv(late_attendance_file, index=False)
                else:
                    print(f"Current date {current_date} not found in the CSV columns.")
            else:
                print("Unknown face detected.")


        if not marked_attendance:
            print("No attendance marked due to time constraints or multiple people after 9:05 AM.")

        if not absentees_marked:
            for index, row in attendance_df.iterrows():
                if pd.isna(row[yesterday_date]):
                    attendance_df.at[index, yesterday_date] = 0
            absentees_marked = True

        attendance_df.to_csv(csv_file, index=False)

    if k == ord('q'):
        break

# Clean up resources
video.release()
cv2.destroyAllWindows()
conn.close()
