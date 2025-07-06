#!/usr/bin/env python3
"""
Simplified Smart Face Attendance System using OpenCV's built-in face recognition
"""
import cv2
import sqlite3
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import pyttsx3
import os
import sys

def speak(text):
    """Text to speech function"""
    try:
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"Speech error: {e}")

def initialize_system():
    """Initialize camera, face detection, and database"""
    print("Initializing Smart Face Attendance System...")
    
    # Initialize camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Cannot open camera")
        return None, None, None, None
    
    # Set camera properties
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    # Load face detector
    face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
    if face_cascade.empty():
        print("Error: Cannot load face cascade classifier")
        cap.release()
        return None, None, None, None
    
    # Initialize face recognizer (using LBPH - Local Binary Pattern Histogram)
    face_recognizer = cv2.face.LBPHFaceRecognizer_create()
    
    # Connect to database
    try:
        conn = sqlite3.connect('data/attendance.db')
        cursor = conn.cursor()
        
        # Check if we have trained data
        cursor.execute("SELECT name, face_data FROM faces")
        data = cursor.fetchall()
        
        if not data:
            print("No registered students found! Please run student registration first.")
            cap.release()
            conn.close()
            return None, None, None, None
        
        # Prepare training data
        faces = []
        labels = []
        label_names = {}
        label_id = 0
        
        for row in data:
            name, face_data = row
            # Convert blob back to image
            face_np = np.frombuffer(face_data, dtype=np.uint8).reshape(50, 50, 3)
            # Convert to grayscale for recognition
            face_gray = cv2.cvtColor(face_np, cv2.COLOR_BGR2GRAY)
            
            faces.append(face_gray)
            labels.append(label_id)
            label_names[label_id] = name
            label_id += 1
        
        # Train the recognizer
        face_recognizer.train(faces, np.array(labels))
        print(f"Trained with {len(data)} face samples from {len(set([row[0] for row in data]))} students")
        
        conn.close()
        return cap, face_cascade, face_recognizer, label_names
        
    except Exception as e:
        print(f"Database error: {e}")
        cap.release()
        return None, None, None, None

def mark_attendance(name, csv_file, late_file):
    """Mark attendance for a student"""
    current_time = datetime.now()
    current_date = current_time.strftime("%d-%m-%Y")
    current_time_str = current_time.strftime("%H:%M:%S")
    
    # Create directories and files if they don't exist
    os.makedirs("Attendance", exist_ok=True)
    
    # Check if CSV file exists and has correct format
    try:
        df = pd.read_csv(csv_file)
        
        # Check if the CSV has the correct columns
        expected_columns = ["Name", "Time", "Date"]
        if not all(col in df.columns for col in expected_columns):
            print(f"Old CSV format detected. Creating new format...")
            # Create new DataFrame with correct structure
            df = pd.DataFrame(columns=expected_columns)
            df.to_csv(csv_file, index=False)
        
        # Check if already marked today
        if not df.empty:
            today_attendance = df[df['Date'] == current_date]
            if name in today_attendance['Name'].values:
                return f"{name} already marked present today"
                
    except FileNotFoundError:
        # Create empty DataFrame with correct columns
        df = pd.DataFrame(columns=["Name", "Time", "Date"])
        df.to_csv(csv_file, index=False)
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        # Create new DataFrame with correct structure
        df = pd.DataFrame(columns=["Name", "Time", "Date"])
        df.to_csv(csv_file, index=False)
    
    # Mark attendance
    new_entry = pd.DataFrame({
        "Name": [name],
        "Time": [current_time_str], 
        "Date": [current_date]
    })
    
    # Read the current file again to ensure we have the latest data
    try:
        df = pd.read_csv(csv_file)
    except:
        df = pd.DataFrame(columns=["Name", "Time", "Date"])
    
    df = pd.concat([df, new_entry], ignore_index=True)
    df.to_csv(csv_file, index=False)
    
    # Check if late (after 9 AM)
    if current_time.hour >= 9:
        try:
            late_df = pd.read_csv(late_file)
            # Check if late file has correct format
            if not all(col in late_df.columns for col in ["Name", "Time", "Date"]):
                late_df = pd.DataFrame(columns=["Name", "Time", "Date"])
        except FileNotFoundError:
            late_df = pd.DataFrame(columns=["Name", "Time", "Date"])
        except Exception:
            late_df = pd.DataFrame(columns=["Name", "Time", "Date"])
        
        late_df = pd.concat([late_df, new_entry], ignore_index=True)
        late_df.to_csv(late_file, index=False)
        return f"{name} marked present (LATE) at {current_time_str}"
    
    return f"{name} marked present at {current_time_str}"

def main():
    """Main attendance recognition loop"""
    # Initialize system
    cap, face_cascade, face_recognizer, label_names = initialize_system()
    
    if cap is None:
        return
    
    # Set up CSV files
    csv_file = "Attendance/Attendance_.csv"
    late_file = "Attendance/late_attendance_record.csv"
    
    # Initialize CSV files with correct format
    os.makedirs("Attendance", exist_ok=True)
    
    # Check and fix attendance file format
    try:
        df = pd.read_csv(csv_file)
        expected_columns = ["Name", "Time", "Date"]
        if not all(col in df.columns for col in expected_columns):
            print("Converting old CSV format to new format...")
            df = pd.DataFrame(columns=expected_columns)
            df.to_csv(csv_file, index=False)
    except FileNotFoundError:
        df = pd.DataFrame(columns=["Name", "Time", "Date"])
        df.to_csv(csv_file, index=False)
    except Exception as e:
        print(f"Creating new attendance file due to error: {e}")
        df = pd.DataFrame(columns=["Name", "Time", "Date"])
        df.to_csv(csv_file, index=False)
    
    # Check and fix late attendance file format
    try:
        late_df = pd.read_csv(late_file)
        if not all(col in late_df.columns for col in expected_columns):
            late_df = pd.DataFrame(columns=expected_columns)
            late_df.to_csv(late_file, index=False)
    except FileNotFoundError:
        late_df = pd.DataFrame(columns=["Name", "Time", "Date"])
        late_df.to_csv(late_file, index=False)
    except Exception:
        late_df = pd.DataFrame(columns=["Name", "Time", "Date"])
        late_df.to_csv(late_file, index=False)
    
    print("System ready! Students can now approach the camera for attendance.")
    print("Press 'q' to quit")
    
    # Recognition parameters
    confidence_threshold = 150  # Increased from 100 to 150
    last_recognition_time = {}  # To avoid multiple recognitions of same person
    recognition_cooldown = 10  # seconds
    
    while True:
        ret, frame = cap.read()
        
        if not ret:
            print("Error reading frame")
            continue
        
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        
        current_time = datetime.now()
        
        for (x, y, w, h) in faces:
            # Extract face region
            face_roi = gray[y:y+h, x:x+w]
            
            # Resize to match training data
            face_roi = cv2.resize(face_roi, (50, 50))
            
            # Recognize face
            label, confidence = face_recognizer.predict(face_roi)
            
            # Draw rectangle around face
            color = (0, 255, 0) if confidence < confidence_threshold else (0, 0, 255)
            cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
            
            if confidence < confidence_threshold and label in label_names:
                name = label_names[label]
                
                # Check cooldown
                if name not in last_recognition_time or \
                   (current_time - last_recognition_time[name]).seconds > recognition_cooldown:
                    
                    # Mark attendance
                    result = mark_attendance(name, csv_file, late_file)
                    print(result)
                    speak(f"Hello {name}")
                    
                    last_recognition_time[name] = current_time
                    
                    # Display name
                    cv2.putText(frame, f"{name} - Present", (x, y-10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                else:
                    cv2.putText(frame, f"{name} - Already marked", (x, y-10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            else:
                cv2.putText(frame, "Unknown", (x, y-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        # Display info
        cv2.putText(frame, f"Registered Students: {len(label_names)}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, "Press 'q' to quit", (10, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Show frame
        cv2.imshow('Smart Face Attendance System', frame)
        
        # Check for quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    print("Attendance system stopped.")

if __name__ == "__main__":
    main()
