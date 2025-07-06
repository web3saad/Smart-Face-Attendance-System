#!/usr/bin/env python3
"""
Test script to verify camera and face detection are working
"""
import cv2
import sys
import time

def test_camera_and_face_detection():
    print("Testing camera and face detection...")
    
    # Initialize camera
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Cannot open camera")
        return False
    
    # Load face detector
    face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
    if face_cascade.empty():
        print("Error: Cannot load face cascade classifier")
        cap.release()
        return False
    
    print("Camera and face detection initialized successfully!")
    print("Press 'q' to quit, 's' to take a test screenshot")
    
    frame_count = 0
    while True:
        ret, frame = cap.read()
        
        if not ret:
            print("Error: Cannot read frame")
            continue
            
        frame_count += 1
        
        # Convert to grayscale for face detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        
        # Draw rectangles around faces
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
            cv2.putText(frame, f"Face {len(faces)}", (x, y-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)
        
        # Add frame info
        cv2.putText(frame, f"Frame: {frame_count}, Faces: {len(faces)}", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Show frame
        cv2.imshow('Camera Test - Press q to quit', frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            cv2.imwrite(f'test_frame_{frame_count}.jpg', frame)
            print(f"Screenshot saved as test_frame_{frame_count}.jpg")
    
    cap.release()
    cv2.destroyAllWindows()
    print("Camera test completed successfully!")
    return True

if __name__ == "__main__":
    test_camera_and_face_detection()
