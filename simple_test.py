#!/usr/bin/env python3
"""
Simple Face Detection Test
"""
import cv2
import sqlite3
import numpy as np

def simple_test():
    print("🔍 Simple Face Detection and Recognition Test")
    print("=" * 50)
    
    # Initialize camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Cannot open camera")
        return
    
    # Load face detector
    face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
    if face_cascade.empty():
        print("❌ Cannot load face detector")
        cap.release()
        return
    
    print("✅ Camera and face detector ready")
    
    # Load database
    conn = sqlite3.connect('data/attendance.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name, face_data FROM faces")
    data = cursor.fetchall()
    
    if not data:
        print("❌ No training data found")
        cap.release()
        conn.close()
        return
    
    # Prepare training data
    faces = []
    labels = []
    label_names = {}
    
    print(f"📚 Loading training data...")
    for i, (name, face_data) in enumerate(data):
        face_np = np.frombuffer(face_data, dtype=np.uint8).reshape(50, 50, 3)
        face_gray = cv2.cvtColor(face_np, cv2.COLOR_BGR2GRAY)
        faces.append(face_gray)
        labels.append(0)  # All same person for now
        label_names[0] = name
    
    # Create recognizer
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.train(faces, np.array(labels))
    
    print(f"✅ Trained with {len(faces)} samples for {label_names[0]}")
    print("\\n🎥 Testing live detection...")
    print("Look at the camera. Press 'q' to quit.")
    
    frame_count = 0
    detection_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            continue
        
        frame_count += 1
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Try different detection parameters
        faces_detected = face_cascade.detectMultiScale(
            gray, 
            scaleFactor=1.05,  # More sensitive
            minNeighbors=3,    # Less strict
            minSize=(30, 30),  # Smaller minimum size
            maxSize=(500, 500)
        )
        
        if len(faces_detected) > 0:
            detection_count += 1
            print(f"👤 Frame {frame_count}: Detected {len(faces_detected)} face(s)")
        
        for (x, y, w, h) in faces_detected:
            # Draw detection rectangle
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
            
            # Extract and test recognition
            face_roi = gray[y:y+h, x:x+w]
            if face_roi.size > 0:
                face_resized = cv2.resize(face_roi, (50, 50))
                
                # Test multiple confidence thresholds
                label, confidence = recognizer.predict(face_resized)
                
                print(f"   🎯 Recognition: confidence={confidence:.1f}")
                
                # Very lenient threshold for testing
                if confidence < 150:  # Very high threshold
                    name = label_names[label]
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 3)
                    cv2.putText(frame, f"{name} ({confidence:.1f})", (x, y-10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    print(f"   ✅ RECOGNIZED: {name}")
                else:
                    cv2.putText(frame, f"Unknown ({confidence:.1f})", (x, y-10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        # Show stats
        cv2.putText(frame, f"Frames: {frame_count}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, f"Detections: {detection_count}", (10, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, f"Rate: {detection_count/frame_count*100:.1f}%", (10, 70), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        cv2.imshow('Simple Face Test', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    conn.close()
    
    print(f"\\n📊 Results:")
    print(f"   - Total frames: {frame_count}")
    print(f"   - Face detections: {detection_count}")
    print(f"   - Detection rate: {detection_count/frame_count*100:.1f}%")

if __name__ == "__main__":
    simple_test()
