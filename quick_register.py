#!/usr/bin/env python3
"""
Quick student registration for testing
"""
import cv2
import os
import sqlite3
from datetime import datetime

def create_database():
    """Create database and tables if they don't exist"""
    conn = sqlite3.connect('data/attendance.db')
    cursor = conn.cursor()
    
    # Create Students table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Students (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            Name TEXT NOT NULL,
            RegisterDate DATE
        )
    ''')
    
    # Create AttendanceRecord table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS AttendanceRecord (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            StudentID INTEGER,
            Date DATE,
            Time TIME,
            Status TEXT,
            FOREIGN KEY (StudentID) REFERENCES Students(ID)
        )
    ''')
    
    conn.commit()
    conn.close()

def register_student(name):
    """Register a student with face data"""
    print(f"🎯 Registering student: {name}")
    
    # Create database if needed
    create_database()
    
    # Create directory for face data
    os.makedirs('face_data', exist_ok=True)
    
    # Initialize camera with Mac optimization
    import platform
    cap = None
    
    if platform.system() == "Darwin":  # macOS
        print("🍎 Using optimized camera settings for macOS")
        cap = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)
        if cap.isOpened():
            # Test if camera works
            ret, _ = cap.read()
            if not ret:
                print("⚠️  Built-in camera not responding, trying default backend...")
                cap.release()
                cap = None
    
    # Fallback to default backend
    if cap is None:
        cap = cv2.VideoCapture(0)
        
    if not cap.isOpened():
        print("❌ Error: Could not access camera")
        return False
    
    # Load face detector
    face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
    
    face_id = len(os.listdir('face_data')) + 1
    count = 0
    
    print("📸 Look at the camera and press SPACE to capture faces (ESC to quit)")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
            
        cv2.putText(frame, f"Registering: {name} | Press SPACE to capture | ESC to quit", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f"Photos captured: {count}/50", 
                   (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        cv2.imshow('Face Registration', frame)
        
        key = cv2.waitKey(1) & 0xFF
        
        if key == 27:  # ESC key
            break
        elif key == 32:  # SPACE key
            if len(faces) > 0:
                x, y, w, h = faces[0]  # Take the first detected face
                roi_gray = gray[y:y+h, x:x+w]
                img_name = f"face_data/User.{face_id}.{count}.jpg"
                cv2.imwrite(img_name, roi_gray)
                count += 1
                print(f"📸 Captured image {count}/50")
                
                if count >= 50:
                    break
            else:
                print("❌ No face detected, try again")
    
    cap.release()
    cv2.destroyAllWindows()
    
    if count >= 20:  # Minimum 20 images for good recognition
        # Add to database
        conn = sqlite3.connect('data/attendance.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Students (Name, RegisterDate) VALUES (?, ?)", 
                      (name, datetime.now().date()))
        conn.commit()
        conn.close()
        
        print(f"✅ Successfully registered {name} with {count} face samples!")
        return True
    else:
        print(f"❌ Registration failed. Only captured {count} images (minimum 20 required)")
        return False

if __name__ == "__main__":
    name = input("Enter student name: ").strip()
    if name:
        register_student(name)
    else:
        print("❌ No name provided")
