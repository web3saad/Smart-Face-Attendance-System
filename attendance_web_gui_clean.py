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
                success = self.start_attendance_system()
                if success:
                    return jsonify({'success': True, 'message': 'Attendance system started'})
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
    
    def start_registration(self, student_name):
        """Start student registration using external script"""
        def run_registration():
            try:
                print(f"🎯 Starting registration for: {student_name}")
                
                # Use the dedicated web_register.py script
                result = subprocess.run([
                    '/Users/sahadchad/Desktop/smart-face-attendance-system-main/.venv/bin/python',
                    'web_register.py',
                    student_name
                ], cwd='/Users/sahadchad/Desktop/smart-face-attendance-system-main',
                   capture_output=True, text=True)
                
                if result.returncode == 0:
                    print(f"✅ Registration completed successfully for {student_name}")
                else:
                    print(f"❌ Registration failed for {student_name}")
                    if result.stderr:
                        print(f"Error: {result.stderr}")
                
            except Exception as ex:
                print(f"❌ Registration error: {ex}")
        
        threading.Thread(target=run_registration, daemon=True).start()
    
    def start_attendance_system(self):
        """Start improved attendance system in background"""
        try:
            print("🎯 Starting attendance system...")
            
            # Check if the main_improved.py file exists
            main_script = '/Users/sahadchad/Desktop/smart-face-attendance-system-main/main_improved.py'
            if not os.path.exists(main_script):
                print("❌ Error: main_improved.py not found!")
                return False
            
            # Check if attendance system is already running
            try:
                result = subprocess.run(['pgrep', '-f', 'main_improved.py'], 
                                      capture_output=True, text=True)
                if result.stdout.strip():
                    print("⚠️  Attendance system is already running!")
                    return True  # Return success since it's already running
            except:
                pass  # pgrep might not be available on all systems
            
            def run_attendance():
                try:
                    # Start the attendance system
                    process = subprocess.Popen([
                        '/Users/sahadchad/Desktop/smart-face-attendance-system-main/.venv/bin/python',
                        'main_improved.py'
                    ], cwd='/Users/sahadchad/Desktop/smart-face-attendance-system-main',
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    
                    print(f"✅ Attendance system started with PID: {process.pid}")
                    
                except Exception as e:
                    print(f"❌ Error running attendance system: {e}")
            
            # Start in background thread
            thread = threading.Thread(target=run_attendance, daemon=True)
            thread.start()
            
            # Give it a moment to start
            time.sleep(0.5)
            return True
            
        except Exception as e:
            print(f"❌ Error starting attendance system: {e}")
            return False
    
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

def main():
    web_app = AttendanceWebApp()
    print("🚀 Starting Smart Face Attendance Web Dashboard...")
    print("📊 Open your browser and go to: http://localhost:8080")
    print("🔄 Press Ctrl+C to stop the server")
    
    web_app.app.run(debug=True, host='0.0.0.0', port=8080)

if __name__ == "__main__":
    main()
