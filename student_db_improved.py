#!/usr/bin/env python3
"""
Improved student database registration with better error handling
"""
import cv2
import sqlite3
import sys
import time
import os

def main():
    print("=== Student Face Registration System ===")
    
    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)
    
    # Initialize camera
    print("Initializing camera...")
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Cannot open camera")
        print("Please check:")
        print("1. Camera is connected")
        print("2. No other application is using the camera")
        print("3. Camera permissions are granted")
        return False
    
    # Set camera properties
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    # Load face detector
    face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
    if face_cascade.empty():
        print("Error: Cannot load face cascade classifier")
        print("Make sure 'haarcascade_frontalface_default.xml' is in the current directory")
        cap.release()
        return False
    
    # Connect to database
    try:
        conn = sqlite3.connect('data/attendance.db')
        cursor = conn.cursor()
        
        # Create table if not exists
        cursor.execute('''CREATE TABLE IF NOT EXISTS faces
                          (id INTEGER PRIMARY KEY AUTOINCREMENT,
                           name TEXT,
                           face_data BLOB)''')
        conn.commit()
        
    except Exception as e:
        print(f"Database error: {e}")
        cap.release()
        return False
    
    # Get student name
    name = input("Enter Student Name: ").strip()
    if not name:
        print("Name cannot be empty!")
        cap.release()
        conn.close()
        return False
    
    print(f"Starting face capture for: {name}")
    print("Instructions:")
    print("- Look at the camera")
    print("- Move your head slightly to capture different angles")
    print("- Press 'q' when you have captured enough samples (aim for 50+)")
    print("- Press 's' to skip a frame if needed")
    
    faces_data = []
    frame_count = 0
    
    # Allow camera to warm up
    time.sleep(2)
    
    while True:
        ret, frame = cap.read()
        
        if not ret or frame is None:
            print("Warning: Could not read frame, retrying...")
            continue
        
        frame_count += 1
        
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        
        # Process detected faces
        for (x, y, w, h) in faces:
            # Crop face
            face_crop = frame[y:y+h, x:x+w]
            
            # Resize to standard size
            face_resized = cv2.resize(face_crop, (50, 50))
            
            # Save every 5th frame to avoid too similar images
            if frame_count % 5 == 0:
                face_bytes = face_resized.tobytes()
                faces_data.append((name, face_bytes))
            
            # Draw rectangle around face
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(frame, f"Face detected", (x, y-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        # Add information overlay
        cv2.putText(frame, f"Samples collected: {len(faces_data)}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, f"Student: {name}", (10, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, "Press 'q' to finish", (10, 90), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Show frame
        cv2.imshow('Face Registration - Press q to finish', frame)
        
        # Handle key presses
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            print("Skipping current frame...")
            continue
        
        # Auto-stop at 100 samples
        if len(faces_data) >= 100:
            print("Collected maximum samples (100), stopping...")
            break
    
    # Save to database
    if faces_data:
        try:
            cursor.executemany('INSERT INTO faces (name, face_data) VALUES (?, ?)', faces_data)
            conn.commit()
            print(f"✅ Successfully saved {len(faces_data)} face samples for {name}")
        except Exception as e:
            print(f"Error saving to database: {e}")
    else:
        print("❌ No face samples were collected")
    
    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    conn.close()
    
    print("Face registration completed!")
    return len(faces_data) > 0

if __name__ == "__main__":
    main()
