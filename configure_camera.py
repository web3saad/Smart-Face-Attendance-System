#!/usr/bin/env python3
"""
Camera Configuration Script for macOS
Helps configure camera settings to prioritize Mac built-in camera
"""
import cv2
import platform
import os

def disable_continuity_camera():
    """Configure system to prioritize Mac built-in camera"""
    if platform.system() != "Darwin":
        print("This script is only for macOS")
        return
    
    print("🍎 Configuring macOS Camera Settings")
    print("=" * 40)
    
    # Instructions for user
    print("\n📋 To prevent iPhone camera notifications:")
    print("1. Go to System Settings > General > AirDrop & Handoff")
    print("2. Turn OFF 'iPhone Cellular Calls'")
    print("3. Turn OFF 'Handoff'")
    print("4. Or go to iPhone Settings > General > AirPlay & Handoff")
    print("5. Turn OFF 'Handoff' on your iPhone")
    
    print("\n🔒 For camera permissions:")
    print("1. Go to System Settings > Privacy & Security > Camera")
    print("2. Make sure Terminal and Python are allowed")
    
    # Test cameras to see which one is Mac built-in
    print("\n🔍 Testing available cameras...")
    
    cameras_info = []
    for i in range(5):
        # Try AVFoundation backend first (better for macOS)
        cap = cv2.VideoCapture(i, cv2.CAP_AVFOUNDATION)
        if cap.isOpened():
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # Test if we can actually read a frame
            ret, frame = cap.read()
            if ret:
                cameras_info.append({
                    'index': i,
                    'width': width,
                    'height': height,
                    'backend': 'AVFoundation',
                    'working': True
                })
                print(f"📹 Camera {i} (AVFoundation): {width}x{height} - ✅ Working")
            else:
                print(f"📹 Camera {i} (AVFoundation): Detected but not working")
            cap.release()
        else:
            # Try default backend
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                
                ret, frame = cap.read()
                if ret:
                    cameras_info.append({
                        'index': i,
                        'width': width,
                        'height': height,
                        'backend': 'Default',
                        'working': True
                    })
                    print(f"📹 Camera {i} (Default): {width}x{height} - ✅ Working")
                cap.release()
    
    if not cameras_info:
        print("❌ No working cameras found!")
        return
    
    # Recommend the best camera (usually index 0 for built-in)
    print(f"\n✅ Recommended camera: Index 0 (Mac built-in)")
    print("   This should prevent iPhone notifications.")
    
    # Create a test
    print("\n🧪 Testing recommended camera...")
    cap = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)
    if cap.isOpened():
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
        
        ret, frame = cap.read()
        if ret:
            print("✅ Mac built-in camera is working properly!")
            
            # Save a test frame
            cv2.imwrite('camera_test_mac.jpg', frame)
            print("📸 Test image saved as 'camera_test_mac.jpg'")
        else:
            print("❌ Mac built-in camera not responding")
        
        cap.release()
    else:
        print("❌ Could not open Mac built-in camera")

def create_camera_config():
    """Create a configuration file for camera settings"""
    config = {
        'preferred_camera_index': 0,
        'backend': 'AVFoundation',
        'width': 640,
        'height': 480,
        'fps': 30,
        'codec': 'MJPG'
    }
    
    import json
    with open('camera_config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print("💾 Camera configuration saved to 'camera_config.json'")

if __name__ == "__main__":
    disable_continuity_camera()
    create_camera_config()
    
    print("\n🎯 Camera configuration complete!")
    print("Now you can test the attendance system without iPhone notifications.")
