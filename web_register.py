#!/usr/bin/env python3
"""
Simple Registration Script for Web Interface
Takes student name as command line argument
"""
import cv2
import sqlite3
import time
import os
import platform
import sys

def register_student(student_name):
    """Register a student with face data"""
    print(f"🎯 Starting face registration for: {student_name}")
    
    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)
    
    # Initialize camera with Mac optimization
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
    
    # Set camera properties
    try:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)
        if platform.system() == "Darwin":
            cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
    except Exception as e:
        print(f"Warning: Could not set camera properties: {e}")
    
    # Test camera
    ret, test_frame = cap.read()
    if not ret:
        print("❌ Error: Camera not working properly")
        cap.release()
        return False
    
    print("✅ Camera is working!")
    
    # Load face detector
    face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
    if face_cascade.empty():
        print("❌ Error: Cannot load face cascade classifier")
        cap.release()
        return False
    
    # Connect to database
    try:
        conn = sqlite3.connect('data/attendance.db')
        cursor = conn.cursor()
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS faces
                          (id INTEGER PRIMARY KEY AUTOINCREMENT,
                           name TEXT,
                           face_data BLOB)''')
        conn.commit()
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        cap.release()
        return False
    
    print("🎥 Camera window will open now...")
    print("📝 Instructions:")
    print("   - Look directly at the camera")
    print("   - Move your head slightly for different angles")
    print("   - Press 'q' when you have enough samples (50+)")
    print("   - The system will auto-stop at 100 samples")
    
    faces_data = []
    frame_count = 0
    last_save_time = time.time()
    
    # Give camera time to adjust
    time.sleep(1)
    
    while True:
        ret, frame = cap.read()
        
        if not ret or frame is None:
            print("Warning: Could not read frame")
            continue
        
        frame_count += 1
        current_time = time.time()
        
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = face_cascade.detectMultiScale(
            gray, 
            scaleFactor=1.1, 
            minNeighbors=5, 
            minSize=(30, 30)
        )
        
        # Process detected faces
        for (x, y, w, h) in faces:
            # Crop and resize face
            face_crop = frame[y:y+h, x:x+w]
            face_resized = cv2.resize(face_crop, (50, 50))
            
            # Save face sample every 0.5 seconds to avoid duplicates
            if current_time - last_save_time > 0.5:
                face_bytes = face_resized.tobytes()
                faces_data.append((student_name, face_bytes))
                last_save_time = current_time
                print(f"Captured sample {len(faces_data)}")
            
            # Draw rectangle around face
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(frame, "Face Detected", (x, y-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # Add status information
        cv2.putText(frame, f"Student: {student_name}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, f"Samples: {len(faces_data)}/100", (10, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, "Press 'q' to finish", (10, 90), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Color coding for sample count
        if len(faces_data) < 30:
            color = (0, 0, 255)  # Red
            status = "Need more samples"
        elif len(faces_data) < 50:
            color = (0, 255, 255)  # Yellow
            status = "Getting better"
        else:
            color = (0, 255, 0)  # Green
            status = "Good quality!"
        
        cv2.putText(frame, status, (10, 120), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        # Show the frame
        cv2.imshow(f'Registration: {student_name} - Press Q to finish', frame)
        
        # Handle key presses
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == ord('Q'):
            break
        
        # Auto-stop at 100 samples
        if len(faces_data) >= 100:
            print("✅ Reached 100 samples - stopping automatically")
            break
    
    # Save to database
    success = False
    if len(faces_data) >= 20:  # Minimum 20 samples
        try:
            cursor.executemany('INSERT INTO faces (name, face_data) VALUES (?, ?)', faces_data)
            conn.commit()
            print(f"✅ Successfully registered {student_name} with {len(faces_data)} samples")
            success = True
        except Exception as e:
            print(f"❌ Error saving to database: {e}")
    else:
        print(f"❌ Not enough samples collected ({len(faces_data)}). Need at least 20.")
    
    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    conn.close()
    
    if success:
        print("🎉 Registration completed successfully!")
    else:
        print("❌ Registration failed - please try again")
    
    return success

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python web_register.py <student_name>")
        sys.exit(1)
    
    student_name = sys.argv[1]
    success = register_student(student_name)
    sys.exit(0 if success else 1)
