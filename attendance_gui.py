#!/usr/bin/env python3
"""
Smart Face Attendance System - GUI Dashboard
A modern, user-friendly interface for managing attendance and viewing reports
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import os
from PIL import Image, ImageTk
import subprocess
import threading

class AttendanceGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Face Attendance System - Dashboard")
        self.root.geometry("1200x800")
        self.root.configure(bg="#f0f0f0")
        
        # Configure style
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Configure colors
        self.colors = {
            'primary': '#2c3e50',
            'secondary': '#3498db',
            'success': '#27ae60',
            'warning': '#f39c12',
            'danger': '#e74c3c',
            'light': '#ecf0f1',
            'dark': '#34495e'
        }
        
        self.setup_styles()
        self.create_widgets()
        self.load_data()
        
    def setup_styles(self):
        """Configure custom styles for the interface"""
        self.style.configure('Title.TLabel', 
                           font=('Arial', 16, 'bold'), 
                           background='#f0f0f0',
                           foreground=self.colors['primary'])
        
        self.style.configure('Header.TLabel', 
                           font=('Arial', 12, 'bold'), 
                           background='#f0f0f0',
                           foreground=self.colors['dark'])
        
        self.style.configure('Info.TLabel', 
                           font=('Arial', 10), 
                           background='#f0f0f0',
                           foreground=self.colors['dark'])
        
        self.style.configure('Success.TButton', 
                           font=('Arial', 10, 'bold'))
        
    def create_widgets(self):
        """Create and layout all GUI components"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Header
        self.create_header(main_frame)
        
        # Left sidebar
        self.create_sidebar(main_frame)
        
        # Main content area
        self.create_main_content(main_frame)
        
        # Status bar
        self.create_status_bar(main_frame)
        
    def create_header(self, parent):
        """Create the header section"""
        header_frame = ttk.Frame(parent, style='Header.TFrame')
        header_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        header_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(header_frame, 
                               text="🎓 Smart Face Attendance System", 
                               style='Title.TLabel')
        title_label.grid(row=0, column=0, sticky=tk.W)
        
        # Current date/time
        self.datetime_label = ttk.Label(header_frame, 
                                       text=datetime.now().strftime("%A, %B %d, %Y - %I:%M %p"), 
                                       style='Info.TLabel')
        self.datetime_label.grid(row=0, column=1, sticky=tk.E)
        
        # Update time every minute
        self.update_datetime()
        
    def create_sidebar(self, parent):
        """Create the left sidebar with navigation"""
        sidebar_frame = ttk.LabelFrame(parent, text="📊 Dashboard Menu", padding="10")
        sidebar_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # System status
        status_frame = ttk.LabelFrame(sidebar_frame, text="System Status", padding="5")
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.status_labels = {}
        self.update_system_status(status_frame)
        
        # Action buttons
        buttons_frame = ttk.LabelFrame(sidebar_frame, text="Actions", padding="5")
        buttons_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Register student button
        register_btn = ttk.Button(buttons_frame, 
                                 text="👤 Register New Student", 
                                 command=self.register_student,
                                 style='Success.TButton')
        register_btn.pack(fill=tk.X, pady=2)
        
        # Start attendance button
        attendance_btn = ttk.Button(buttons_frame, 
                                   text="📹 Start Attendance", 
                                   command=self.start_attendance)
        attendance_btn.pack(fill=tk.X, pady=2)
        
        # Refresh data button
        refresh_btn = ttk.Button(buttons_frame, 
                                text="🔄 Refresh Data", 
                                command=self.refresh_data)
        refresh_btn.pack(fill=tk.X, pady=2)
        
        # Export report button
        export_btn = ttk.Button(buttons_frame, 
                               text="📤 Export Report", 
                               command=self.export_report)
        export_btn.pack(fill=tk.X, pady=2)
        
        # Clear database button
        clear_btn = ttk.Button(buttons_frame, 
                              text="🗑️ Clear Database", 
                              command=self.clear_database)
        clear_btn.pack(fill=tk.X, pady=2)
        
    def create_main_content(self, parent):
        """Create the main content area with tabs"""
        # Notebook for tabs
        self.notebook = ttk.Notebook(parent)
        self.notebook.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Overview tab
        self.create_overview_tab()
        
        # Students tab
        self.create_students_tab()
        
        # Attendance tab
        self.create_attendance_tab()
        
        # Reports tab
        self.create_reports_tab()
        
    def create_overview_tab(self):
        """Create the overview/dashboard tab"""
        overview_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(overview_frame, text="📊 Overview")
        
        # Quick stats
        stats_frame = ttk.LabelFrame(overview_frame, text="Quick Statistics", padding="10")
        stats_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Stats grid
        self.stats_frame_content = stats_frame
        self.update_quick_stats()
        
        # Recent attendance
        recent_frame = ttk.LabelFrame(overview_frame, text="Recent Attendance", padding="10")
        recent_frame.pack(fill=tk.BOTH, expand=True)
        
        # Treeview for recent attendance
        columns = ('Name', 'Time', 'Date', 'Status')
        self.recent_tree = ttk.Treeview(recent_frame, columns=columns, show='headings', height=10)
        
        # Configure columns
        for col in columns:
            self.recent_tree.heading(col, text=col)
            self.recent_tree.column(col, width=120)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(recent_frame, orient=tk.VERTICAL, command=self.recent_tree.yview)
        self.recent_tree.configure(yscrollcommand=scrollbar.set)
        
        self.recent_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
    def create_students_tab(self):
        """Create the students management tab"""
        students_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(students_frame, text="👥 Students")
        
        # Students list
        students_list_frame = ttk.LabelFrame(students_frame, text="Registered Students", padding="10")
        students_list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Treeview for students
        columns = ('Name', 'Face Samples', 'Registration Date', 'Last Seen')
        self.students_tree = ttk.Treeview(students_list_frame, columns=columns, show='headings')
        
        for col in columns:
            self.students_tree.heading(col, text=col)
            self.students_tree.column(col, width=150)
        
        # Scrollbar for students
        students_scrollbar = ttk.Scrollbar(students_list_frame, orient=tk.VERTICAL, command=self.students_tree.yview)
        self.students_tree.configure(yscrollcommand=students_scrollbar.set)
        
        self.students_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        students_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
    def create_attendance_tab(self):
        """Create the attendance records tab"""
        attendance_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(attendance_frame, text="📅 Attendance")
        
        # Date filter
        filter_frame = ttk.Frame(attendance_frame)
        filter_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(filter_frame, text="Filter by Date:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.date_var = tk.StringVar(value=datetime.now().strftime("%d-%m-%Y"))
        date_entry = ttk.Entry(filter_frame, textvariable=self.date_var, width=15)
        date_entry.pack(side=tk.LEFT, padx=(0, 5))
        
        filter_btn = ttk.Button(filter_frame, text="Filter", command=self.filter_attendance)
        filter_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        all_btn = ttk.Button(filter_frame, text="Show All", command=self.show_all_attendance)
        all_btn.pack(side=tk.LEFT)
        
        # Attendance list
        attendance_list_frame = ttk.LabelFrame(attendance_frame, text="Attendance Records", padding="10")
        attendance_list_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ('Name', 'Time', 'Date', 'Status')
        self.attendance_tree = ttk.Treeview(attendance_list_frame, columns=columns, show='headings')
        
        for col in columns:
            self.attendance_tree.heading(col, text=col)
            self.attendance_tree.column(col, width=150)
        
        attendance_scrollbar = ttk.Scrollbar(attendance_list_frame, orient=tk.VERTICAL, command=self.attendance_tree.yview)
        self.attendance_tree.configure(yscrollcommand=attendance_scrollbar.set)
        
        self.attendance_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        attendance_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
    def create_reports_tab(self):
        """Create the reports and analytics tab"""
        reports_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(reports_frame, text="📈 Reports")
        
        # Report options
        options_frame = ttk.LabelFrame(reports_frame, text="Report Options", padding="10")
        options_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Individual student report
        ttk.Label(options_frame, text="Individual Report:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        
        self.student_var = tk.StringVar()
        self.student_combo = ttk.Combobox(options_frame, textvariable=self.student_var, state="readonly")
        self.student_combo.grid(row=0, column=1, padx=(0, 5))
        
        individual_btn = ttk.Button(options_frame, text="Generate Report", command=self.generate_individual_report)
        individual_btn.grid(row=0, column=2)
        
        # Charts frame
        charts_frame = ttk.LabelFrame(reports_frame, text="Analytics", padding="10")
        charts_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create matplotlib figure
        self.create_charts(charts_frame)
        
    def create_charts(self, parent):
        """Create attendance charts"""
        # Create figure with subplots
        self.fig, (self.ax1, self.ax2) = plt.subplots(1, 2, figsize=(12, 5))
        self.fig.patch.set_facecolor('#f0f0f0')
        
        # Canvas for matplotlib
        self.canvas = FigureCanvasTkAgg(self.fig, parent)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        self.update_charts()
        
    def create_status_bar(self, parent):
        """Create the status bar at the bottom"""
        self.status_bar = ttk.Label(parent, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
    def update_datetime(self):
        """Update the date/time display"""
        current_time = datetime.now().strftime("%A, %B %d, %Y - %I:%M %p")
        self.datetime_label.config(text=current_time)
        self.root.after(60000, self.update_datetime)  # Update every minute
        
    def update_system_status(self, parent):
        """Update system status information"""
        try:
            # Clear existing widgets
            for widget in parent.winfo_children():
                widget.destroy()
            
            # Database status
            conn = sqlite3.connect('data/attendance.db')
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(DISTINCT name) FROM faces")
            student_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM faces")
            face_samples = cursor.fetchone()[0]
            conn.close()
            
            # Attendance files status
            attendance_exists = os.path.exists('Attendance/Attendance_.csv')
            
            # Status labels
            ttk.Label(parent, text=f"👥 Students: {student_count}", style='Info.TLabel').pack(anchor=tk.W)
            ttk.Label(parent, text=f"📸 Face Samples: {face_samples}", style='Info.TLabel').pack(anchor=tk.W)
            ttk.Label(parent, text=f"📁 Files: {'✅' if attendance_exists else '❌'}", style='Info.TLabel').pack(anchor=tk.W)
            
        except Exception as e:
            ttk.Label(parent, text="❌ Database Error", style='Info.TLabel').pack(anchor=tk.W)
            
    def update_quick_stats(self):
        """Update quick statistics"""
        try:
            # Clear existing widgets
            for widget in self.stats_frame_content.winfo_children():
                widget.destroy()
            
            # Load attendance data
            if os.path.exists('Attendance/Attendance_.csv'):
                df = pd.read_csv('Attendance/Attendance_.csv')
                late_df = pd.read_csv('Attendance/late_attendance_record.csv') if os.path.exists('Attendance/late_attendance_record.csv') else pd.DataFrame()
                
                today = datetime.now().strftime("%d-%m-%Y")
                today_attendance = df[df['Date'] == today] if not df.empty else pd.DataFrame()
                
                # Create stats grid
                stats = [
                    ("📅 Today's Attendance", len(today_attendance)),
                    ("📊 Total Records", len(df)),
                    ("⏰ Late Today", len(late_df[late_df['Date'] == today]) if not late_df.empty else 0),
                    ("👥 Unique Students", df['Name'].nunique() if not df.empty else 0)
                ]
                
                for i, (label, value) in enumerate(stats):
                    frame = ttk.Frame(self.stats_frame_content)
                    frame.grid(row=i//2, column=i%2, padx=10, pady=5, sticky=tk.W)
                    
                    ttk.Label(frame, text=label, style='Info.TLabel').pack()
                    ttk.Label(frame, text=str(value), style='Header.TLabel').pack()
            else:
                ttk.Label(self.stats_frame_content, text="No attendance data available", style='Info.TLabel').pack()
                
        except Exception as e:
            ttk.Label(self.stats_frame_content, text=f"Error loading stats: {e}", style='Info.TLabel').pack()
            
    def load_data(self):
        """Load all data into the interface"""
        self.load_students_data()
        self.load_attendance_data()
        self.load_recent_attendance()
        self.update_student_combo()
        
    def load_students_data(self):
        """Load students data into the treeview"""
        # Clear existing data
        for item in self.students_tree.get_children():
            self.students_tree.delete(item)
            
        try:
            conn = sqlite3.connect('data/attendance.db')
            cursor = conn.cursor()
            cursor.execute("SELECT name, COUNT(*) as samples FROM faces GROUP BY name")
            students = cursor.fetchall()
            conn.close()
            
            # Load attendance for last seen
            attendance_df = pd.read_csv('Attendance/Attendance_.csv') if os.path.exists('Attendance/Attendance_.csv') else pd.DataFrame()
            
            for name, samples in students:
                # Find last seen
                if not attendance_df.empty:
                    student_records = attendance_df[attendance_df['Name'] == name]
                    if not student_records.empty:
                        last_seen = student_records.iloc[-1]['Date']
                    else:
                        last_seen = "Never"
                else:
                    last_seen = "Never"
                
                self.students_tree.insert('', 'end', values=(name, samples, "N/A", last_seen))
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load students data: {e}")
            
    def load_attendance_data(self):
        """Load attendance data into the treeview"""
        self.show_all_attendance()
        
    def load_recent_attendance(self):
        """Load recent attendance records"""
        # Clear existing data
        for item in self.recent_tree.get_children():
            self.recent_tree.delete(item)
            
        try:
            if os.path.exists('Attendance/Attendance_.csv'):
                df = pd.read_csv('Attendance/Attendance_.csv')
                late_df = pd.read_csv('Attendance/late_attendance_record.csv') if os.path.exists('Attendance/late_attendance_record.csv') else pd.DataFrame()
                
                # Get last 10 records
                recent_records = df.tail(10)
                
                for _, row in recent_records.iterrows():
                    # Check if late
                    is_late = not late_df[(late_df['Name'] == row['Name']) & 
                                         (late_df['Date'] == row['Date'])].empty if not late_df.empty else False
                    status = "🔴 Late" if is_late else "🟢 On Time"
                    
                    self.recent_tree.insert('', 0, values=(row['Name'], row['Time'], row['Date'], status))
                    
        except Exception as e:
            print(f"Error loading recent attendance: {e}")
            
    def update_student_combo(self):
        """Update student combobox options"""
        try:
            conn = sqlite3.connect('data/attendance.db')
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT name FROM faces ORDER BY name")
            students = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            self.student_combo['values'] = students
            if students:
                self.student_combo.current(0)
                
        except Exception as e:
            print(f"Error updating student combo: {e}")
            
    def update_charts(self):
        """Update attendance charts"""
        try:
            if not os.path.exists('Attendance/Attendance_.csv'):
                return
                
            df = pd.read_csv('Attendance/Attendance_.csv')
            if df.empty:
                return
                
            # Clear axes
            self.ax1.clear()
            self.ax2.clear()
            
            # Chart 1: Daily attendance count
            daily_counts = df.groupby('Date').size()
            self.ax1.bar(range(len(daily_counts)), daily_counts.values, color=self.colors['secondary'])
            self.ax1.set_title('Daily Attendance Count')
            self.ax1.set_xlabel('Days')
            self.ax1.set_ylabel('Students')
            
            # Chart 2: Student attendance frequency
            student_counts = df['Name'].value_counts().head(10)
            self.ax2.barh(student_counts.index, student_counts.values, color=self.colors['success'])
            self.ax2.set_title('Top 10 Students by Attendance')
            self.ax2.set_xlabel('Days Present')
            
            # Refresh canvas
            self.canvas.draw()
            
        except Exception as e:
            print(f"Error updating charts: {e}")
            
    def filter_attendance(self):
        """Filter attendance by date"""
        # Clear existing data
        for item in self.attendance_tree.get_children():
            self.attendance_tree.delete(item)
            
        try:
            date_filter = self.date_var.get()
            
            if os.path.exists('Attendance/Attendance_.csv'):
                df = pd.read_csv('Attendance/Attendance_.csv')
                late_df = pd.read_csv('Attendance/late_attendance_record.csv') if os.path.exists('Attendance/late_attendance_record.csv') else pd.DataFrame()
                
                # Filter by date
                filtered_df = df[df['Date'] == date_filter]
                
                for _, row in filtered_df.iterrows():
                    # Check if late
                    is_late = not late_df[(late_df['Name'] == row['Name']) & 
                                         (late_df['Date'] == row['Date'])].empty if not late_df.empty else False
                    status = "🔴 Late" if is_late else "🟢 On Time"
                    
                    self.attendance_tree.insert('', 'end', values=(row['Name'], row['Time'], row['Date'], status))
                    
        except Exception as e:
            messagebox.showerror("Error", f"Failed to filter attendance: {e}")
            
    def show_all_attendance(self):
        """Show all attendance records"""
        # Clear existing data
        for item in self.attendance_tree.get_children():
            self.attendance_tree.delete(item)
            
        try:
            if os.path.exists('Attendance/Attendance_.csv'):
                df = pd.read_csv('Attendance/Attendance_.csv')
                late_df = pd.read_csv('Attendance/late_attendance_record.csv') if os.path.exists('Attendance/late_attendance_record.csv') else pd.DataFrame()
                
                for _, row in df.iterrows():
                    # Check if late
                    is_late = not late_df[(late_df['Name'] == row['Name']) & 
                                         (late_df['Date'] == row['Date'])].empty if not late_df.empty else False
                    status = "🔴 Late" if is_late else "🟢 On Time"
                    
                    self.attendance_tree.insert('', 'end', values=(row['Name'], row['Time'], row['Date'], status))
                    
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load attendance: {e}")
            
    def register_student(self):
        """Launch student registration"""
        def run_registration():
            try:
                subprocess.run([
                    '/Users/sahadchad/Desktop/smart-face-attendance-system-main/.venv/bin/python',
                    'student_db_improved.py'
                ], cwd='/Users/sahadchad/Desktop/smart-face-attendance-system-main')
                # Refresh data after registration
                self.root.after(1000, self.refresh_data)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to start registration: {e}")
        
        threading.Thread(target=run_registration, daemon=True).start()
        self.update_status("Student registration started...")
        
    def start_attendance(self):
        """Launch attendance system"""
        def run_attendance():
            try:
                subprocess.run([
                    '/Users/sahadchad/Desktop/smart-face-attendance-system-main/.venv/bin/python',
                    'main_simplified.py'
                ], cwd='/Users/sahadchad/Desktop/smart-face-attendance-system-main')
                # Refresh data after attendance
                self.root.after(1000, self.refresh_data)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to start attendance: {e}")
        
        threading.Thread(target=run_attendance, daemon=True).start()
        self.update_status("Attendance system started...")
        
    def refresh_data(self):
        """Refresh all data"""
        self.load_data()
        self.update_quick_stats()
        self.update_system_status(self.status_labels if hasattr(self, 'status_labels') else None)
        self.update_charts()
        self.update_status("Data refreshed successfully")
        
    def export_report(self):
        """Export attendance report"""
        try:
            if not os.path.exists('Attendance/Attendance_.csv'):
                messagebox.showwarning("Warning", "No attendance data to export")
                return
                
            # Ask for save location
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="Save Attendance Report"
            )
            
            if filename:
                df = pd.read_csv('Attendance/Attendance_.csv')
                df.to_csv(filename, index=False)
                messagebox.showinfo("Success", f"Report exported to {filename}")
                self.update_status(f"Report exported to {filename}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export report: {e}")
            
    def clear_database(self):
        """Clear the database"""
        result = messagebox.askyesno(
            "Confirm Clear Database",
            "Are you sure you want to clear all student registrations and attendance data?\n\nThis action cannot be undone!"
        )
        
        if result:
            try:
                subprocess.run([
                    '/Users/sahadchad/Desktop/smart-face-attendance-system-main/.venv/bin/python',
                    'reset_database.py'
                ], cwd='/Users/sahadchad/Desktop/smart-face-attendance-system-main')
                
                self.refresh_data()
                messagebox.showinfo("Success", "Database cleared successfully")
                self.update_status("Database cleared")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to clear database: {e}")
                
    def generate_individual_report(self):
        """Generate individual student report"""
        student = self.student_var.get()
        if not student:
            messagebox.showwarning("Warning", "Please select a student")
            return
            
        try:
            if os.path.exists('Attendance/Attendance_.csv'):
                df = pd.read_csv('Attendance/Attendance_.csv')
                late_df = pd.read_csv('Attendance/late_attendance_record.csv') if os.path.exists('Attendance/late_attendance_record.csv') else pd.DataFrame()
                
                student_data = df[df['Name'] == student]
                student_late = late_df[late_df['Name'] == student] if not late_df.empty else pd.DataFrame()
                
                if student_data.empty:
                    messagebox.showinfo("No Data", f"No attendance records found for {student}")
                    return
                
                # Create report window
                report_window = tk.Toplevel(self.root)
                report_window.title(f"Attendance Report - {student}")
                report_window.geometry("600x400")
                
                # Report content
                report_text = tk.Text(report_window, wrap=tk.WORD, padx=10, pady=10)
                scrollbar = ttk.Scrollbar(report_window, orient=tk.VERTICAL, command=report_text.yview)
                report_text.configure(yscrollcommand=scrollbar.set)
                
                # Generate report content
                total_days = len(student_data)
                late_days = len(student_late)
                on_time_days = total_days - late_days
                punctuality_rate = (on_time_days / total_days * 100) if total_days > 0 else 0
                
                report_content = f"""
ATTENDANCE REPORT FOR: {student}
{'='*50}

SUMMARY:
📅 Total Days Present: {total_days}
⏰ Days On Time: {on_time_days}
🔴 Days Late: {late_days}
📊 Punctuality Rate: {punctuality_rate:.1f}%

ATTENDANCE HISTORY:
{'='*30}
"""
                
                for _, row in student_data.iterrows():
                    is_late = not student_late[(student_late['Date'] == row['Date'])].empty
                    status = "LATE" if is_late else "ON TIME"
                    status_emoji = "🔴" if is_late else "🟢"
                    report_content += f"{row['Date']} | {row['Time']} | {status_emoji} {status}\n"
                
                report_text.insert(tk.END, report_content)
                report_text.config(state=tk.DISABLED)
                
                report_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate report: {e}")
            
    def update_status(self, message):
        """Update status bar message"""
        self.status_bar.config(text=message)
        self.root.after(3000, lambda: self.status_bar.config(text="Ready"))

def main():
    """Main function to run the GUI"""
    root = tk.Tk()
    app = AttendanceGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
