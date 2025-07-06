#!/usr/bin/env python3
"""
Smart Face Attendance System - Web Dashboard
A modern, responsive web interface for managing attendance and viewing reports
"""
from flask import Flask, render_template, jsonify, request, send_file
import pandas as pd
import sqlite3
import json
from datetime import datetime, timedelta
import plotly
import plotly.graph_objs as go
import plotly.express as px
import os
import subprocess
import threading
import cv2
import time

app = Flask(__name__)

class AttendanceWebApp:
    def __init__(self):
        self.app = app
        self.setup_routes()
        
    def setup_routes(self):
        """Setup all web routes"""
        
        @self.app.route('/')
        def dashboard():
            """Main dashboard page"""
            return render_template('dashboard.html')
        
        @self.app.route('/api/stats')
        def get_stats():
            """Get quick statistics"""
            try:
                stats = self.get_quick_stats()
                return jsonify(stats)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/students')
        def get_students():
            """Get students data"""
            try:
                students = self.get_students_data()
                return jsonify(students)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/attendance')
        def get_attendance():
            """Get attendance data"""
            try:
                date_filter = request.args.get('date', None)
                attendance = self.get_attendance_data(date_filter)
                return jsonify(attendance)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/charts')
        def get_charts():
            """Get chart data"""
            try:
                charts = self.get_charts_data()
                return jsonify(charts)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/register', methods=['POST'])
        def register_student():
            """Start student registration"""
            try:
                data = request.get_json()
                student_name = data.get('name', '').strip()
                
                if not student_name:
                    return jsonify({'error': 'Student name is required'}), 400
                
                # Check if student already exists
                if self.student_exists(student_name):
                    return jsonify({'error': f'Student "{student_name}" already exists'}), 400
                
                self.start_registration(student_name)
                return jsonify({'success': True, 'message': f'Registration started for {student_name}'})
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/attendance/start', methods=['POST'])
        def start_attendance():
            """Start attendance system"""
            try:
                # Check if attendance system is already running
                if self.is_attendance_running():
                    return jsonify({'error': 'Attendance system is already running'}), 400
                
                success = self.start_attendance_system()
                if success:
                    return jsonify({'success': True, 'message': 'Attendance system started successfully! Camera window should open shortly.'})
                else:
                    return jsonify({'error': 'Failed to start attendance system'}), 500
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/clear-database', methods=['POST'])
        def clear_database():
            """Clear database"""
            try:
                self.clear_database_data()
                return jsonify({'success': True, 'message': 'Database cleared'})
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/export')
        def export_report():
            """Export attendance report"""
            try:
                filename = self.export_attendance_report()
                return send_file(filename, as_attachment=True)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
    
    def get_quick_stats(self):
        """Get quick statistics for dashboard"""
        try:
            # Database stats
            conn = sqlite3.connect('data/attendance.db')
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(DISTINCT name) FROM faces")
            student_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM faces")
            face_samples = cursor.fetchone()[0]
            conn.close()
            
            # Attendance stats
            if os.path.exists('Attendance/Attendance_.csv'):
                df = pd.read_csv('Attendance/Attendance_.csv')
                late_df = pd.read_csv('Attendance/late_attendance_record.csv') if os.path.exists('Attendance/late_attendance_record.csv') else pd.DataFrame()
                
                today = datetime.now().strftime("%d-%m-%Y")
                today_attendance = df[df['Date'] == today] if not df.empty else pd.DataFrame()
                today_late = late_df[late_df['Date'] == today] if not late_df.empty else pd.DataFrame()
                
                return {
                    'students_registered': student_count,
                    'face_samples': face_samples,
                    'today_attendance': len(today_attendance),
                    'today_late': len(today_late),
                    'total_records': len(df),
                    'unique_attendees': df['Name'].nunique() if not df.empty else 0
                }
            else:
                return {
                    'students_registered': student_count,
                    'face_samples': face_samples,
                    'today_attendance': 0,
                    'today_late': 0,
                    'total_records': 0,
                    'unique_attendees': 0
                }
        except Exception as e:
            return {'error': str(e)}
    
    def get_students_data(self):
        """Get students data"""
        try:
            conn = sqlite3.connect('data/attendance.db')
            cursor = conn.cursor()
            cursor.execute("SELECT name, COUNT(*) as samples FROM faces GROUP BY name ORDER BY name")
            students = cursor.fetchall()
            conn.close()
            
            # Get last seen data
            attendance_df = pd.read_csv('Attendance/Attendance_.csv') if os.path.exists('Attendance/Attendance_.csv') else pd.DataFrame()
            
            result = []
            for name, samples in students:
                if not attendance_df.empty:
                    student_records = attendance_df[attendance_df['Name'] == name]
                    last_seen = student_records.iloc[-1]['Date'] if not student_records.empty else "Never"
                else:
                    last_seen = "Never"
                
                result.append({
                    'name': name,
                    'samples': samples,
                    'last_seen': last_seen
                })
            
            return result
        except Exception as e:
            return {'error': str(e)}
    
    def get_attendance_data(self, date_filter=None):
        """Get attendance data"""
        try:
            if not os.path.exists('Attendance/Attendance_.csv'):
                return []
            
            df = pd.read_csv('Attendance/Attendance_.csv')
            late_df = pd.read_csv('Attendance/late_attendance_record.csv') if os.path.exists('Attendance/late_attendance_record.csv') else pd.DataFrame()
            
            if date_filter:
                df = df[df['Date'] == date_filter]
            
            result = []
            for _, row in df.iterrows():
                is_late = not late_df[(late_df['Name'] == row['Name']) & 
                                     (late_df['Date'] == row['Date'])].empty if not late_df.empty else False
                
                result.append({
                    'name': row['Name'],
                    'time': row['Time'],
                    'date': row['Date'],
                    'status': 'Late' if is_late else 'On Time',
                    'status_color': 'danger' if is_late else 'success'
                })
            
            return result
        except Exception as e:
            return {'error': str(e)}
    
    def get_charts_data(self):
        """Get data for charts"""
        try:
            if not os.path.exists('Attendance/Attendance_.csv'):
                return {'error': 'No attendance data available'}
            
            df = pd.read_csv('Attendance/Attendance_.csv')
            if df.empty:
                return {'error': 'No attendance data available'}
            
            # Daily attendance chart
            daily_counts = df.groupby('Date').size().reset_index(name='count')
            daily_chart = {
                'data': [{
                    'x': daily_counts['Date'].tolist(),
                    'y': daily_counts['count'].tolist(),
                    'type': 'bar',
                    'name': 'Daily Attendance',
                    'marker': {'color': '#3498db'}
                }],
                'layout': {
                    'title': 'Daily Attendance Count',
                    'xaxis': {'title': 'Date'},
                    'yaxis': {'title': 'Students Present'}
                }
            }
            
            # Student attendance frequency
            student_counts = df['Name'].value_counts().head(10)
            student_chart = {
                'data': [{
                    'x': student_counts.values.tolist(),
                    'y': student_counts.index.tolist(),
                    'type': 'bar',
                    'orientation': 'h',
                    'name': 'Student Attendance',
                    'marker': {'color': '#27ae60'}
                }],
                'layout': {
                    'title': 'Top 10 Students by Attendance',
                    'xaxis': {'title': 'Days Present'},
                    'yaxis': {'title': 'Students'}
                }
            }
            
            return {
                'daily_chart': daily_chart,
                'student_chart': student_chart
            }
        except Exception as e:
            return {'error': str(e)}
    
    def student_exists(self, student_name):
        """Check if student already exists in database"""
        try:
            conn = sqlite3.connect('data/attendance.db')
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM faces WHERE name = ?", (student_name,))
            count = cursor.fetchone()[0]
            conn.close()
            return count > 0
        except Exception:
            return False
    
    def is_attendance_running(self):
        """Check if attendance system is already running"""
        try:
            # Check for running main_improved.py processes
            result = subprocess.run(['pgrep', '-f', 'main_improved.py'], 
                                  capture_output=True, text=True)
            return result.returncode == 0 and result.stdout.strip()
        except Exception:
            return False
    
    def start_registration(self, student_name):
        """Start student registration using external script (more stable)"""
        def run_registration():
            try:
                # Create registration script with name pre-filled
                script_content = f'''#!/usr/bin/env python3
import cv2
import sqlite3
import time
import os

def main():
    student_name = "{student_name}"
    print(f"Starting face registration for: {{student_name}}")
    
    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)
    
    # Test camera access first
    print("Testing camera access...")
    cap = cv2.VideoCapture(0)
    
    # Try different camera indices if 0 doesn't work
    if not cap.isOpened():
        print("Camera 0 not available, trying camera 1...")
        cap = cv2.VideoCapture(1)
    
    if not cap.isOpened():
        print("❌ Error: Cannot access camera. Please check:")
        print("1. Camera is not being used by another application")
        print("2. Camera permissions are granted to Terminal/Python")
        print("3. Camera is properly connected")
        return False
    
    # Set camera properties with error handling
    try:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)
    except Exception as e:
        print(f"Warning: Could not set camera properties: {{e}}")
    
    # Test camera by reading a frame
    print("Testing camera...")
    ret, test_frame = cap.read()
    if not ret or test_frame is None:
        print("❌ Error: Camera is not working properly")
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
        
        cursor.execute("""CREATE TABLE IF NOT EXISTS faces
                          (id INTEGER PRIMARY KEY AUTOINCREMENT,
                           name TEXT,
                           face_data BLOB)""")
        conn.commit()
        
    except Exception as e:
        print(f"❌ Database error: {{e}}")
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
                print(f"Captured sample {{len(faces_data)}}")
            
            # Draw rectangle around face
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(frame, "Face Detected", (x, y-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # Add status information
        cv2.putText(frame, f"Student: {{student_name}}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, f"Samples: {{len(faces_data)}}/100", (10, 60), 
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
        cv2.imshow(f'Registration: {{student_name}} - Press Q to finish', frame)
        
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
            print(f"✅ Successfully registered {{student_name}} with {{len(faces_data)}} samples")
            success = True
        except Exception as e:
            print(f"❌ Error saving to database: {{e}}")
    else:
        print(f"❌ Not enough samples collected ({{len(faces_data)}}). Need at least 20.")
    
    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    conn.close()
    
    if success:
        print("🎉 Registration completed successfully!")
    else:
        print("❌ Registration failed - please try again")
    
    return success

    def is_attendance_running(self):
        """Check if attendance system is already running"""
        try:
            # Check for running main_improved.py processes
            result = subprocess.run(['pgrep', '-f', 'main_improved.py'], 
                                  capture_output=True, text=True)
            return result.returncode == 0 and result.stdout.strip()
        except Exception:
            return False
    
    def start_attendance_system(self):
        """Start improved attendance system in background with better feedback"""
        def run_attendance():
            try:
                print("🎯 Starting attendance system...")
                # Check if the main_improved.py file exists
                if not os.path.exists('main_improved.py'):
                    print("❌ Error: main_improved.py not found!")
                    return False
                
                # Start the attendance system
                process = subprocess.Popen([
                    '/Users/sahadchad/Desktop/smart-face-attendance-system-main/.venv/bin/python',
                    'main_improved.py'
                ], cwd='/Users/sahadchad/Desktop/smart-face-attendance-system-main',
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                
                print(f"✅ Attendance system started with PID: {process.pid}")
                
                # Wait a bit to see if it starts successfully
                try:
                    return_code = process.wait(timeout=3)
                    if return_code != 0:
                        stderr = process.stderr.read()
                        print(f"❌ Attendance system failed to start: {stderr}")
                        return False
                except subprocess.TimeoutExpired:
                    # If it's still running after 3 seconds, it probably started successfully
                    print("✅ Attendance system appears to be running successfully")
                    return True
                
            except Exception as e:
                print(f"❌ Error starting attendance system: {e}")
                return False
        
        threading.Thread(target=run_attendance, daemon=True).start()
        return True
    
    def clear_database_data(self):
        """Clear database"""
        subprocess.run([
            '/Users/sahadchad/Desktop/smart-face-attendance-system-main/.venv/bin/python',
            'reset_database.py'
        ], cwd='/Users/sahadchad/Desktop/smart-face-attendance-system-main', input='yes\nDELETE\n', text=True)
    
    def export_attendance_report(self):
        """Export attendance report"""
        if not os.path.exists('Attendance/Attendance_.csv'):
            raise Exception("No attendance data to export")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"attendance_report_{timestamp}.csv"
        
        df = pd.read_csv('Attendance/Attendance_.csv')
        df.to_csv(filename, index=False)
        
        return filename

# Create Flask app templates
templates_dir = 'templates'
os.makedirs(templates_dir, exist_ok=True)

# Create the main dashboard template
dashboard_html = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Smart Face Attendance System</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body { background-color: #f8f9fa; }
        .card { border: none; box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075); }
        .card-header { background-color: #fff; border-bottom: 1px solid #dee2e6; }
        .stat-card { transition: transform 0.2s; }
        .stat-card:hover { transform: translateY(-2px); }
        .navbar-brand { font-weight: bold; }
        .chart-container { height: 400px; }
        .table-container { max-height: 400px; overflow-y: auto; }
    </style>
</head>
<body>
    <!-- Navigation -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <span class="navbar-brand">🎓 Smart Face Attendance System</span>
            <span class="navbar-text" id="currentDateTime"></span>
        </div>
    </nav>

    <div class="container mt-4">
        <!-- Quick Stats Row -->
        <div class="row mb-4">
            <div class="col-md-2">
                <div class="card stat-card bg-primary text-white">
                    <div class="card-body text-center">
                        <i class="fas fa-users fa-2x mb-2"></i>
                        <h4 id="studentsRegistered">0</h4>
                        <small>Students Registered</small>
                    </div>
                </div>
            </div>
            <div class="col-md-2">
                <div class="card stat-card bg-success text-white">
                    <div class="card-body text-center">
                        <i class="fas fa-calendar-check fa-2x mb-2"></i>
                        <h4 id="todayAttendance">0</h4>
                        <small>Today's Attendance</small>
                    </div>
                </div>
            </div>
            <div class="col-md-2">
                <div class="card stat-card bg-warning text-white">
                    <div class="card-body text-center">
                        <i class="fas fa-clock fa-2x mb-2"></i>
                        <h4 id="todayLate">0</h4>
                        <small>Late Today</small>
                    </div>
                </div>
            </div>
            <div class="col-md-2">
                <div class="card stat-card bg-info text-white">
                    <div class="card-body text-center">
                        <i class="fas fa-chart-bar fa-2x mb-2"></i>
                        <h4 id="totalRecords">0</h4>
                        <small>Total Records</small>
                    </div>
                </div>
            </div>
            <div class="col-md-2">
                <div class="card stat-card bg-secondary text-white">
                    <div class="card-body text-center">
                        <i class="fas fa-camera fa-2x mb-2"></i>
                        <h4 id="faceSamples">0</h4>
                        <small>Face Samples</small>
                    </div>
                </div>
            </div>
            <div class="col-md-2">
                <div class="card stat-card bg-dark text-white">
                    <div class="card-body text-center">
                        <i class="fas fa-user-check fa-2x mb-2"></i>
                        <h4 id="uniqueAttendees">0</h4>
                        <small>Unique Attendees</small>
                    </div>
                </div>
            </div>
        </div>

        <!-- Action Buttons -->
        <div class="row mb-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h5 class="mb-0"><i class="fas fa-cogs"></i> System Actions</h5>
                    </div>
                    <div class="card-body">
                        <button class="btn btn-success me-2" onclick="showRegisterModal()">
                            <i class="fas fa-user-plus"></i> Register New Student
                        </button>
                        <button class="btn btn-primary me-2" onclick="startAttendance()">
                            <i class="fas fa-video"></i> Start Attendance
                        </button>
                        <button class="btn btn-info me-2" onclick="refreshData()">
                            <i class="fas fa-sync-alt"></i> Refresh Data
                        </button>
                        <button class="btn btn-warning me-2" onclick="exportReport()">
                            <i class="fas fa-download"></i> Export Report
                        </button>
                        <button class="btn btn-danger" onclick="clearDatabase()">
                            <i class="fas fa-trash"></i> Clear Database
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Main Content Tabs -->
        <ul class="nav nav-tabs" id="mainTabs" role="tablist">
            <li class="nav-item" role="presentation">
                <button class="nav-link active" id="overview-tab" data-bs-toggle="tab" data-bs-target="#overview" type="button">
                    <i class="fas fa-tachometer-alt"></i> Overview
                </button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="students-tab" data-bs-toggle="tab" data-bs-target="#students" type="button">
                    <i class="fas fa-users"></i> Students
                </button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="attendance-tab" data-bs-toggle="tab" data-bs-target="#attendance" type="button">
                    <i class="fas fa-calendar"></i> Attendance
                </button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="reports-tab" data-bs-toggle="tab" data-bs-target="#reports" type="button">
                    <i class="fas fa-chart-line"></i> Reports
                </button>
            </li>
        </ul>

        <div class="tab-content" id="mainTabsContent">
            <!-- Overview Tab -->
            <div class="tab-pane fade show active" id="overview" role="tabpanel">
                <div class="row mt-3">
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">
                                <h5><i class="fas fa-chart-bar"></i> Daily Attendance</h5>
                            </div>
                            <div class="card-body">
                                <div id="dailyChart" class="chart-container"></div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">
                                <h5><i class="fas fa-user-friends"></i> Top Students</h5>
                            </div>
                            <div class="card-body">
                                <div id="studentChart" class="chart-container"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Students Tab -->
            <div class="tab-pane fade" id="students" role="tabpanel">
                <div class="card mt-3">
                    <div class="card-header">
                        <h5><i class="fas fa-users"></i> Registered Students</h5>
                    </div>
                    <div class="card-body">
                        <div class="table-container">
                            <table class="table table-striped">
                                <thead>
                                    <tr>
                                        <th>Name</th>
                                        <th>Face Samples</th>
                                        <th>Last Seen</th>
                                    </tr>
                                </thead>
                                <tbody id="studentsTableBody">
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Attendance Tab -->
            <div class="tab-pane fade" id="attendance" role="tabpanel">
                <div class="card mt-3">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h5><i class="fas fa-calendar-check"></i> Attendance Records</h5>
                        <div>
                            <input type="date" id="dateFilter" class="form-control d-inline-block" style="width: auto;">
                            <button class="btn btn-primary btn-sm ms-2" onclick="filterAttendance()">Filter</button>
                            <button class="btn btn-secondary btn-sm ms-1" onclick="showAllAttendance()">Show All</button>
                        </div>
                    </div>
                    <div class="card-body">
                        <div class="table-container">
                            <table class="table table-striped">
                                <thead>
                                    <tr>
                                        <th>Name</th>
                                        <th>Time</th>
                                        <th>Date</th>
                                        <th>Status</th>
                                    </tr>
                                </thead>
                                <tbody id="attendanceTableBody">
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Reports Tab -->
            <div class="tab-pane fade" id="reports" role="tabpanel">
                <div class="card mt-3">
                    <div class="card-header">
                        <h5><i class="fas fa-chart-line"></i> Analytics Dashboard</h5>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-12">
                                <p class="text-muted">Detailed analytics and reporting features will be displayed here.</p>
                                <div class="alert alert-info">
                                    <i class="fas fa-info-circle"></i>
                                    Use the Export Report button to download attendance data as CSV files.
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Loading Modal -->
    <div class="modal fade" id="loadingModal" tabindex="-1">
        <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content">
                <div class="modal-body text-center">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <p class="mt-3" id="loadingMessage">Processing...</p>
                </div>
            </div>
        </div>
    </div>

    <!-- Student Registration Modal -->
    <div class="modal fade" id="registerModal" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">👤 Register New Student</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <form id="registerForm">
                        <div class="mb-3">
                            <label for="studentName" class="form-label">Student Name</label>
                            <input type="text" class="form-control" id="studentName" placeholder="Enter student's full name" required>
                            <div class="form-text">Please enter the full name of the student to register.</div>
                        </div>
                        <div class="alert alert-info">
                            <i class="fas fa-info-circle"></i>
                            <strong>Instructions:</strong>
                            <ul class="mb-0 mt-2">
                                <li>After clicking "Start Registration", a camera window will open</li>
                                <li>Position your face in front of the camera</li>
                                <li>Move your head slightly for different angles</li>
                                <li>The system will capture 50-100 face samples</li>
                                <li>Press 'q' in the camera window when done</li>
                            </ul>
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <button type="button" class="btn btn-success" onclick="registerStudent()">
                        <i class="fas fa-camera"></i> Start Registration
                    </button>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Update current date/time
        function updateDateTime() {
            const now = new Date();
            document.getElementById('currentDateTime').textContent = now.toLocaleDateString() + ' ' + now.toLocaleTimeString();
        }
        updateDateTime();
        setInterval(updateDateTime, 1000);

        // Load initial data
        loadStats();
        loadStudents();
        loadAttendance();
        loadCharts();

        function showLoading(message = 'Processing...') {
            document.getElementById('loadingMessage').textContent = message;
            new bootstrap.Modal(document.getElementById('loadingModal')).show();
        }

        function hideLoading() {
            bootstrap.Modal.getInstance(document.getElementById('loadingModal'))?.hide();
        }

        function loadStats() {
            fetch('/api/stats')
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        console.error('Error loading stats:', data.error);
                        return;
                    }
                    document.getElementById('studentsRegistered').textContent = data.students_registered;
                    document.getElementById('todayAttendance').textContent = data.today_attendance;
                    document.getElementById('todayLate').textContent = data.today_late;
                    document.getElementById('totalRecords').textContent = data.total_records;
                    document.getElementById('faceSamples').textContent = data.face_samples;
                    document.getElementById('uniqueAttendees').textContent = data.unique_attendees;
                })
                .catch(error => console.error('Error loading stats:', error));
        }

        function loadStudents() {
            fetch('/api/students')
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        console.error('Error loading students:', data.error);
                        return;
                    }
                    const tbody = document.getElementById('studentsTableBody');
                    tbody.innerHTML = '';
                    data.forEach(student => {
                        const row = tbody.insertRow();
                        row.innerHTML = `
                            <td>${student.name}</td>
                            <td><span class="badge bg-primary">${student.samples}</span></td>
                            <td>${student.last_seen}</td>
                        `;
                    });
                })
                .catch(error => console.error('Error loading students:', error));
        }

        function loadAttendance(dateFilter = null) {
            const url = dateFilter ? `/api/attendance?date=${dateFilter}` : '/api/attendance';
            fetch(url)
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        console.error('Error loading attendance:', data.error);
                        return;
                    }
                    const tbody = document.getElementById('attendanceTableBody');
                    tbody.innerHTML = '';
                    data.forEach(record => {
                        const row = tbody.insertRow();
                        row.innerHTML = `
                            <td>${record.name}</td>
                            <td>${record.time}</td>
                            <td>${record.date}</td>
                            <td><span class="badge bg-${record.status_color}">${record.status}</span></td>
                        `;
                    });
                })
                .catch(error => console.error('Error loading attendance:', error));
        }

        function loadCharts() {
            fetch('/api/charts')
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        console.error('Error loading charts:', data.error);
                        return;
                    }
                    if (data.daily_chart) {
                        Plotly.newPlot('dailyChart', data.daily_chart.data, data.daily_chart.layout, {responsive: true});
                    }
                    if (data.student_chart) {
                        Plotly.newPlot('studentChart', data.student_chart.data, data.student_chart.layout, {responsive: true});
                    }
                })
                .catch(error => console.error('Error loading charts:', error));
        }

        function showRegisterModal() {
            new bootstrap.Modal(document.getElementById('registerModal')).show();
        }

        function registerStudent() {
            const studentName = document.getElementById('studentName').value.trim();
            
            if (!studentName) {
                alert('Please enter a student name');
                return;
            }
            
            // Close the modal
            bootstrap.Modal.getInstance(document.getElementById('registerModal')).hide();
            
            showLoading(`Starting registration for ${studentName}...`);
            
            fetch('/api/register', { 
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ name: studentName })
            })
                .then(response => response.json())
                .then(data => {
                    hideLoading();
                    if (data.error) {
                        alert('Error: ' + data.error);
                    } else {
                        alert(`Registration started for ${studentName}! Please use the camera window that opened.`);
                        // Clear the form
                        document.getElementById('studentName').value = '';
                        // Refresh data after a delay to show new student
                        setTimeout(refreshData, 2000);
                    }
                })
                .catch(error => {
                    hideLoading();
                    console.error('Error starting registration:', error);
                    alert('Error starting registration. Please try again.');
                });
        }

        function startAttendance() {
            showLoading('Starting attendance system...');
            fetch('/api/attendance/start', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    hideLoading();
                    if (data.error) {
                        alert('Error: ' + data.error);
                    } else {
                        alert('Attendance system started! Please use the camera window that opened.');
                    }
                })
                .catch(error => {
                    hideLoading();
                    console.error('Error starting attendance:', error);
                });
        }

        function refreshData() {
            showLoading('Refreshing data...');
            loadStats();
            loadStudents();
            loadAttendance();
            loadCharts();
            setTimeout(hideLoading, 1000);
        }

        function exportReport() {
            showLoading('Exporting report...');
            window.open('/api/export', '_blank');
            setTimeout(hideLoading, 2000);
        }

        function clearDatabase() {
            if (confirm('Are you sure you want to clear all data? This action cannot be undone!')) {
                showLoading('Clearing database...');
                fetch('/api/clear-database', { method: 'POST' })
                    .then(response => response.json())
                    .then(data => {
                        hideLoading();
                        if (data.error) {
                            alert('Error: ' + data.error);
                        } else {
                            alert('Database cleared successfully!');
                            refreshData();
                        }
                    })
                    .catch(error => {
                        hideLoading();
                        console.error('Error clearing database:', error);
                    });
            }
        }

        function filterAttendance() {
            const dateFilter = document.getElementById('dateFilter').value;
            if (dateFilter) {
                // Convert from YYYY-MM-DD to DD-MM-YYYY
                const [year, month, day] = dateFilter.split('-');
                const formattedDate = `${day}-${month}-${year}`;
                loadAttendance(formattedDate);
            }
        }

        function showAllAttendance() {
            document.getElementById('dateFilter').value = '';
            loadAttendance();
        }

        // Auto-refresh data every 30 seconds
        setInterval(() => {
            loadStats();
            loadAttendance();
        }, 30000);
    </script>
</body>
</html>
'''

with open('templates/dashboard.html', 'w') as f:
    f.write(dashboard_html)

def main():
    web_app = AttendanceWebApp()
    print("🚀 Starting Smart Face Attendance Web Dashboard...")
    print("📊 Open your browser and go to: http://localhost:8080")
    print("🔄 Press Ctrl+C to stop the server")
    
    web_app.app.run(debug=True, host='0.0.0.0', port=8080)

if __name__ == "__main__":
    main()
