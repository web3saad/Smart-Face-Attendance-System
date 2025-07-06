#!/usr/bin/env python3
"""
Test script to demonstrate multiple face handling capability
"""
import cv2
import numpy as np

def test_multiple_face_detection():
    """Test how many faces can be detected simultaneously"""
    print("🔍 Testing Multiple Face Detection Capability")
    print("-" * 50)
    
    # Initialize camera and face detector
    cap = cv2.VideoCapture(0)
    face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
    
    if not cap.isOpened():
        print("❌ Cannot open camera")
        return
    
    if face_cascade.empty():
        print("❌ Cannot load face cascade")
        return
    
    print("✅ Camera and face detection initialized")
    print("📹 Instructions:")
    print("   - Get multiple people in front of camera")
    print("   - Press 's' to take screenshot")
    print("   - Press 'q' to quit")
    print()
    
    max_faces_detected = 0
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        
        if not ret:
            continue
            
        frame_count += 1
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect all faces
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        current_face_count = len(faces)
        
        # Update maximum
        if current_face_count > max_faces_detected:
            max_faces_detected = current_face_count
        
        # Draw rectangles around each face with ID
        for i, (x, y, w, h) in enumerate(faces):
            color = (0, 255, 0)  # Green
            cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
            cv2.putText(frame, f"Person {i+1}", (x, y-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        # Display statistics
        cv2.putText(frame, f"Faces Detected: {current_face_count}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, f"Max Detected: {max_faces_detected}", (10, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, "Press 's' for screenshot, 'q' to quit", (10, 90), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        cv2.imshow('Multiple Face Detection Test', frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            filename = f"multiple_faces_test_{frame_count}.jpg"
            cv2.imwrite(filename, frame)
            print(f"📸 Screenshot saved: {filename} ({current_face_count} faces)")
    
    cap.release()
    cv2.destroyAllWindows()
    
    print(f"\n📊 Test Results:")
    print(f"   Maximum faces detected simultaneously: {max_faces_detected}")
    print(f"   Total frames processed: {frame_count}")

if __name__ == "__main__":
    test_multiple_face_detection()
