#!/usr/bin/env python3
"""
Camera Detection and Management Utility
Prioritizes Mac built-in camera over mobile/external cameras
"""
import cv2
import platform

def get_available_cameras():
    """Get list of available cameras with their details"""
    cameras = []
    
    # Test up to 10 camera indices
    for i in range(10):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            # Get camera properties
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            # Try to get a frame to verify camera works
            ret, frame = cap.read()
            if ret:
                cameras.append({
                    'index': i,
                    'width': width,
                    'height': height,
                    'fps': fps,
                    'working': True
                })
                print(f"📹 Camera {i}: {width}x{height} @ {fps}fps - Working ✅")
            else:
                print(f"📹 Camera {i}: Available but not working ❌")
            
            cap.release()
        else:
            # Camera not available
            continue
    
    return cameras

def get_best_camera_index():
    """Get the best camera index, prioritizing Mac built-in camera"""
    cameras = get_available_cameras()
    
    if not cameras:
        print("❌ No working cameras found!")
        return None
    
    # On macOS, built-in camera is usually index 0
    # Mobile cameras (iPhone Continuity) are usually higher indices
    if platform.system() == "Darwin":  # macOS
        # Prioritize camera 0 (built-in) if available
        for cam in cameras:
            if cam['index'] == 0 and cam['working']:
                print(f"✅ Using Mac built-in camera (index {cam['index']})")
                return cam['index']
        
        # If camera 0 not available, use the first working camera
        first_cam = cameras[0]
        print(f"⚠️  Mac built-in camera not available, using camera {first_cam['index']}")
        return first_cam['index']
    
    # For other systems, just use the first available camera
    first_cam = cameras[0]
    print(f"✅ Using camera {first_cam['index']}")
    return first_cam['index']

def init_camera_with_fallback():
    """Initialize camera with automatic fallback and Mac preference"""
    camera_index = get_best_camera_index()
    
    if camera_index is None:
        return None
    
    cap = cv2.VideoCapture(camera_index)
    
    # Configure camera for optimal performance
    if cap.isOpened():
        # Set reasonable resolution
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        # Set camera to use direct show on Windows or AVFoundation on macOS
        if platform.system() == "Darwin":  # macOS
            cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
        
        print(f"✅ Camera {camera_index} initialized successfully")
        return cap
    else:
        print(f"❌ Failed to initialize camera {camera_index}")
        return None

def test_camera():
    """Test camera functionality"""
    print("🔍 Detecting available cameras...")
    cap = init_camera_with_fallback()
    
    if cap is None:
        print("❌ No camera available for testing")
        return False
    
    print("📸 Testing camera... Press 'q' to quit or 's' to save test image")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ Failed to read from camera")
            break
        
        # Show frame info
        h, w = frame.shape[:2]
        cv2.putText(frame, f"Camera Test - {w}x{h}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, "Press 'q' to quit, 's' to save", (10, 70), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        cv2.imshow('Camera Test', frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            cv2.imwrite('camera_test.jpg', frame)
            print("📸 Test image saved as 'camera_test.jpg'")
    
    cap.release()
    cv2.destroyAllWindows()
    print("✅ Camera test completed")
    return True

if __name__ == "__main__":
    print("🎯 Camera Detection and Management Utility")
    print("=" * 50)
    test_camera()
