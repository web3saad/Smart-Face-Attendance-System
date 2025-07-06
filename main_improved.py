#!/usr/bin/env python3
"""
Improved Smart Face Attendance System with better face recognition
"""
import cv2
import sqlite3
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import os
import sys

def initialize_system():
    """Initialize camera, face detection, and database"""
    print("🚀 Initializing Smart Face Attendance System...")
    
    # Initialize camera with Mac-specific optimizations
    import platform
    
    cap = None
    if platform.system() == "Darwin":  # macOS
        print("🍎 Detected macOS - Using AVFoundation backend for built-in camera")
        # Use AVFoundation backend for better Mac compatibility
        cap = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)
        if cap.isOpened():
            # Test if we can read from this camera
            ret, _ = cap.read()
            if not ret:
                print("⚠️  Built-in camera not responding, trying default backend...")
                cap.release()
                cap = None
    
    # Fallback to default backend if AVFoundation fails
    if cap is None:
        cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("❌ Error: Cannot open camera")
        return None, None, None, None
    
    # Set camera properties for stability
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    
    # For macOS, set MJPEG codec for better performance
    if platform.system() == "Darwin":
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
    
    # Test camera
    ret, test_frame = cap.read()
    if not ret:
        print("❌ Error: Camera not working properly")
        cap.release()
        return None, None, None, None
    print("✅ Camera initialized successfully")
    print(f"📹 Camera resolution: {int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}")
    
    
    # Load face detector
    face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
    if face_cascade.empty():
        print("❌ Error: Cannot load face cascade classifier")
        cap.release()
        return None, None, None, None
    print("✅ Face detector loaded")
    
    # Initialize face recognizer (using LBPH - Local Binary Pattern Histogram)
    face_recognizer = cv2.face.LBPHFaceRecognizer_create()
    
    # Connect to database and load training data
    try:
        conn = sqlite3.connect('data/attendance.db')
        cursor = conn.cursor()
        
        # Check if we have trained data
        cursor.execute("SELECT name, face_data FROM faces")
        data = cursor.fetchall()
        
        if not data:
            print("❌ No registered students found!")
            print("📝 Please register students first using the web interface.")
            cap.release()
            conn.close()
            return None, None, None, None
        
        # Group faces by student name
        student_faces = {}
        for name, face_data in data:
            if name not in student_faces:
                student_faces[name] = []
            
            # Convert blob back to image
            face_np = np.frombuffer(face_data, dtype=np.uint8).reshape(50, 50, 3)
            # Convert to grayscale for recognition
            face_gray = cv2.cvtColor(face_np, cv2.COLOR_BGR2GRAY)
            student_faces[name].append(face_gray)
        
        # Prepare training data
        faces = []
        labels = []
        label_names = {}
        
        label_id = 0
        for name, face_list in student_faces.items():
            label_names[label_id] = name
            for face in face_list:
                faces.append(face)
                labels.append(label_id)
            print(f"📚 Loaded {len(face_list)} samples for {name}")
            label_id += 1
        
        # Train the recognizer
        if faces:
            face_recognizer.train(faces, np.array(labels))
            print(f"🎯 Training completed with {len(faces)} samples from {len(student_faces)} students")
        else:
            print("❌ No valid face data found")
            cap.release()
            conn.close()
            return None, None, None, None
        
        conn.close()
        return cap, face_cascade, face_recognizer, label_names
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        cap.release()
        return None, None, None, None

def mark_attendance(name, csv_file, late_file):
    """Mark attendance for a student"""
    current_time = datetime.now()
    current_date = current_time.strftime("%d-%m-%Y")
    current_time_str = current_time.strftime("%H:%M:%S")
    
    # Create directories if they don't exist
    os.makedirs("Attendance", exist_ok=True)
    
    # Check if CSV file exists and has correct format
    try:
        df = pd.read_csv(csv_file)
        expected_columns = ["Name", "Time", "Date"]
        if not all(col in df.columns for col in expected_columns):
            print(f"📝 Updating CSV format for {csv_file}")
            df = pd.DataFrame(columns=expected_columns)
            df.to_csv(csv_file, index=False)
        
        # Check if already marked today
        if not df.empty:
            today_attendance = df[(df['Date'] == current_date) & (df['Name'] == name)]
            if not today_attendance.empty:
                return f"⏰ {name} already marked present today"
                
    except FileNotFoundError:
        # Create empty DataFrame with correct columns
        df = pd.DataFrame(columns=["Name", "Time", "Date"])
        df.to_csv(csv_file, index=False)
    except Exception as e:
        print(f"⚠️ Error with CSV file: {e}")
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
    is_late = current_time.hour >= 9
    
    if is_late:
        try:
            late_df = pd.read_csv(late_file)
            if not all(col in late_df.columns for col in ["Name", "Time", "Date"]):
                late_df = pd.DataFrame(columns=["Name", "Time", "Date"])
        except FileNotFoundError:
            late_df = pd.DataFrame(columns=["Name", "Time", "Date"])
        except Exception:
            late_df = pd.DataFrame(columns=["Name", "Time", "Date"])
        
        late_df = pd.concat([late_df, new_entry], ignore_index=True)
        late_df.to_csv(late_file, index=False)
        return f"🔴 {name} marked present (LATE) at {current_time_str}"
    else:
        return f"✅ {name} marked present (ON TIME) at {current_time_str}"

def main():
    # Initialize system
    cap, face_cascade, face_recognizer, label_names = initialize_system()
    
    if cap is None:
        print("❌ System initialization failed!")
        return
    
    # Set up CSV files
    csv_file = "Attendance/Attendance_.csv"
    late_file = "Attendance/late_attendance_record.csv"
    
    print("🎯 System ready! Students can now approach the camera for attendance.")
    print("🔧 Recognition settings:")
    print("   - Confidence threshold: Adaptive")
    print("   - Cooldown period: 10 seconds")
    print("   - Detection method: Improved cascade + LBPH")
    print("📱 Press 'q' to quit")
    print("-" * 60)
    
    # Recognition parameters
    base_confidence_threshold = 150  # Increased from 80 to 150
    max_confidence_threshold = 200   # Increased from 120 to 200
    last_recognition_time = {}  # To avoid multiple recognitions of same person
    recognition_cooldown = 10  # seconds
    frame_count = 0
    
    try:
        while True:
            ret, frame = cap.read()
            
            if not ret:
                print("⚠️ Warning: Could not read frame")
                continue
            
            frame_count += 1
            
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Enhance image for better detection
            gray = cv2.equalizeHist(gray)
            
            # Detect faces with multiple scales
            faces = face_cascade.detectMultiScale(
                gray, 
                scaleFactor=1.1, 
                minNeighbors=5, 
                minSize=(60, 60),
                maxSize=(300, 300),
                flags=cv2.CASCADE_SCALE_IMAGE
            )
            
            current_time = datetime.now()
            
            # Show detection info every 30 frames
            if frame_count % 30 == 0:
                print(f"🔍 Frame {frame_count}: Detected {len(faces)} face(s)")
            
            for i, (x, y, w, h) in enumerate(faces):
                # Extract face region with some padding
                padding = 10
                face_roi = gray[max(0, y-padding):min(gray.shape[0], y+h+padding), 
                              max(0, x-padding):min(gray.shape[1], x+w+padding)]
                
                if face_roi.size == 0:
                    continue
                
                # Resize to match training data
                face_roi_resized = cv2.resize(face_roi, (50, 50))
                
                # Recognize face
                label, confidence = face_recognizer.predict(face_roi_resized)
                
                # Adaptive confidence threshold based on face size
                face_area = w * h
                adaptive_threshold = base_confidence_threshold + (max_confidence_threshold - base_confidence_threshold) * (1 - min(face_area / 10000, 1))
                
                recognized = confidence < adaptive_threshold and label in label_names
                
                # Draw rectangle around face
                if recognized:
                    color = (0, 255, 0)  # Green for recognized
                    name = label_names[label]
                    label_text = f"{name} ({confidence:.1f})"
                else:
                    color = (0, 0, 255)  # Red for unrecognized
                    label_text = f"Unknown ({confidence:.1f})"
                
                cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
                
                # Draw label background
                label_size = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
                cv2.rectangle(frame, (x, y-30), (x + label_size[0], y), color, -1)
                cv2.putText(frame, label_text, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                
                # Mark attendance if recognized
                if recognized:
                    name = label_names[label]
                    
                    # Check cooldown
                    if name not in last_recognition_time or \
                       (current_time - last_recognition_time[name]).seconds > recognition_cooldown:
                        
                        result = mark_attendance(name, csv_file, late_file)
                        print(result)
                        last_recognition_time[name] = current_time
                        
                        # Visual feedback
                        cv2.putText(frame, "ATTENDANCE MARKED!", (10, 30), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            # Add system info overlay
            info_y = frame.shape[0] - 80
            cv2.putText(frame, f"Students: {len(label_names)}", (10, info_y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(frame, f"Faces: {len(faces)}", (10, info_y + 20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(frame, f"Threshold: {adaptive_threshold:.1f}", (10, info_y + 40), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(frame, "Press 'q' to quit", (10, info_y + 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Show frame
            cv2.imshow('Smart Face Attendance System - Improved', frame)
            
            # Handle key presses
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == ord('Q'):
                print("👋 Shutting down attendance system...")
                break
                
    except KeyboardInterrupt:
        print("\n👋 System interrupted by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    finally:
        # Cleanup
        cap.release()
        cv2.destroyAllWindows()
        print("🔒 System shutdown complete")

if __name__ == "__main__":
    main()
