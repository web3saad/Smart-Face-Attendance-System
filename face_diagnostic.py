#!/usr/bin/env python3
"""
Face Recognition Diagnostic Tool
Helps debug face recognition issues
"""
import cv2
import sqlite3
import numpy as np
import os

def test_face_recognition():
    """Test face recognition system"""
    print("🔍 Face Recognition Diagnostic Tool")
    print("=" * 50)
    
    # Check if database exists
    if not os.path.exists('data/attendance.db'):
        print("❌ Database not found!")
        return
    
    # Connect to database
    conn = sqlite3.connect('data/attendance.db')
    cursor = conn.cursor()
    
    # Check students
    cursor.execute("SELECT name, COUNT(*) FROM faces GROUP BY name")
    students = cursor.fetchall()
    
    print(f"📊 Database Stats:")
    print(f"   - Students registered: {len(students)}")
    for name, count in students:
        print(f"   - {name}: {count} samples")
    
    if not students:
        print("❌ No students registered!")
        conn.close()
        return
    
    # Test camera
    print("\n📹 Testing Camera...")
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Camera not accessible!")
        return
    
    # Test face detection
    print("✅ Camera OK")
    face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
    if face_cascade.empty():
        print("❌ Face cascade not found!")
        cap.release()
        conn.close()
        return
    
    print("✅ Face detector OK")
    
    # Load and test face recognizer
    print("\n🤖 Testing Face Recognition...")
    face_recognizer = cv2.face.LBPHFaceRecognizer_create()
    
    # Load training data
    cursor.execute("SELECT name, face_data FROM faces")
    data = cursor.fetchall()
    
    faces = []
    labels = []
    label_names = {}
    label_id = 0
    
    for name, face_data in data:
        if name not in label_names.values():
            # Convert blob back to image
            face_np = np.frombuffer(face_data, dtype=np.uint8).reshape(50, 50, 3)
            face_gray = cv2.cvtColor(face_np, cv2.COLOR_BGR2GRAY)
            
            faces.append(face_gray)
            labels.append(label_id)
            
            if label_id not in label_names:
                label_names[label_id] = name
                label_id += 1
    
    # Train recognizer
    if faces:
        face_recognizer.train(faces, np.array(labels))
        print(f"✅ Recognizer trained with {len(faces)} samples")
    else:
        print("❌ No training data!")
        cap.release()
        conn.close()
        return
    
    print("\n🎥 Live Test - Look at the camera!")
    print("Press 'q' to quit, 's' to save debug image")
    
    frame_count = 0
    detection_count = 0
    recognition_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            continue
            
        frame_count += 1
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces_detected = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(60, 60))
        
        if len(faces_detected) > 0:
            detection_count += 1
        
        for (x, y, w, h) in faces_detected:
            # Extract face
            face_roi = gray[y:y+h, x:x+w]
            face_roi = cv2.resize(face_roi, (50, 50))
            
            # Recognize
            label, confidence = face_recognizer.predict(face_roi)
            
            # Check if recognized
            if confidence < 100 and label in label_names:
                recognition_count += 1
                name = label_names[label]
                color = (0, 255, 0)
                text = f"{name} ({confidence:.1f})"
            else:
                color = (0, 0, 255)
                text = f"Unknown ({confidence:.1f})"
            
            # Draw
            cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
            cv2.putText(frame, text, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        # Stats overlay
        cv2.putText(frame, f"Frames: {frame_count}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, f"Detections: {detection_count}", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, f"Recognitions: {recognition_count}", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, f"Detection Rate: {detection_count/frame_count*100:.1f}%", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        cv2.imshow('Face Recognition Diagnostic', frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            cv2.imwrite(f'debug_frame_{frame_count}.jpg', frame)
            print(f"💾 Saved debug frame: debug_frame_{frame_count}.jpg")
    
    cap.release()
    cv2.destroyAllWindows()
    conn.close()
    
    print(f"\n📈 Test Results:")
    print(f"   - Total frames: {frame_count}")
    print(f"   - Face detections: {detection_count}")
    print(f"   - Face recognitions: {recognition_count}")
    print(f"   - Detection rate: {detection_count/frame_count*100:.1f}%")
    if detection_count > 0:
        print(f"   - Recognition rate: {recognition_count/detection_count*100:.1f}%")

if __name__ == "__main__":
    test_face_recognition()
