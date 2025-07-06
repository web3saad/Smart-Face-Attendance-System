#!/usr/bin/env python3
"""
Student Attendance Report Generator
This script generates comprehensive attendance reports for the Smart Face Attendance System
"""
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import os
import sys

def display_header():
    """Display a nice header for the report"""
    print("=" * 60)
    print("📊 SMART FACE ATTENDANCE SYSTEM - STUDENT REPORTS")
    print("=" * 60)
    print()

def get_registered_students():
    """Get list of all registered students from database"""
    try:
        conn = sqlite3.connect('data/attendance.db')
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT name FROM faces ORDER BY name")
        students = [row[0] for row in cursor.fetchall()]
        conn.close()
        return students
    except Exception as e:
        print(f"Error accessing database: {e}")
        return []

def load_attendance_data():
    """Load attendance data from CSV files"""
    try:
        # Load regular attendance
        attendance_df = pd.read_csv('Attendance/Attendance_.csv')
        print(f"✅ Loaded {len(attendance_df)} attendance records")
    except FileNotFoundError:
        print("❌ No attendance records found")
        attendance_df = pd.DataFrame(columns=["Name", "Time", "Date"])
    
    try:
        # Load late attendance
        late_df = pd.read_csv('Attendance/late_attendance_record.csv')
        print(f"✅ Loaded {len(late_df)} late attendance records")
    except FileNotFoundError:
        print("❌ No late attendance records found")
        late_df = pd.DataFrame(columns=["Name", "Time", "Date"])
    
    return attendance_df, late_df

def show_all_students_summary(attendance_df, late_df, students):
    """Show summary for all students"""
    print("\n📋 ALL STUDENTS ATTENDANCE SUMMARY")
    print("-" * 50)
    
    if attendance_df.empty:
        print("No attendance records found!")
        return
    
    for student in students:
        student_attendance = attendance_df[attendance_df['Name'] == student]
        student_late = late_df[late_df['Name'] == student]
        
        total_days = len(student_attendance)
        late_days = len(student_late)
        on_time_days = total_days - late_days
        
        print(f"👤 {student}:")
        print(f"   📅 Total Days Present: {total_days}")
        print(f"   ⏰ On Time: {on_time_days}")
        print(f"   ⏰ Late: {late_days}")
        if total_days > 0:
            attendance_rate = (total_days / max(1, total_days)) * 100
            punctuality_rate = (on_time_days / total_days) * 100
            print(f"   📊 Punctuality Rate: {punctuality_rate:.1f}%")
        print()

def show_student_detailed_report(student_name, attendance_df, late_df):
    """Show detailed report for a specific student"""
    print(f"\n📊 DETAILED REPORT FOR: {student_name}")
    print("-" * 50)
    
    student_attendance = attendance_df[attendance_df['Name'] == student_name]
    student_late = late_df[late_df['Name'] == student_name]
    
    if student_attendance.empty:
        print(f"❌ No attendance records found for {student_name}")
        return
    
    print(f"📈 ATTENDANCE STATISTICS:")
    print(f"   Total Days Present: {len(student_attendance)}")
    print(f"   Days On Time: {len(student_attendance) - len(student_late)}")
    print(f"   Days Late: {len(student_late)}")
    
    if len(student_attendance) > 0:
        punctuality_rate = ((len(student_attendance) - len(student_late)) / len(student_attendance)) * 100
        print(f"   Punctuality Rate: {punctuality_rate:.1f}%")
    
    print(f"\n📅 ATTENDANCE HISTORY:")
    print("Date        | Time     | Status")
    print("-" * 35)
    
    # Combine and sort attendance records
    all_records = []
    
    for _, row in student_attendance.iterrows():
        is_late = not student_late[
            (student_late['Name'] == student_name) & 
            (student_late['Date'] == row['Date'])
        ].empty
        
        status = "LATE" if is_late else "ON TIME"
        all_records.append({
            'Date': row['Date'],
            'Time': row['Time'],
            'Status': status
        })
    
    # Sort by date (most recent first)
    all_records.sort(key=lambda x: datetime.strptime(x['Date'], '%d-%m-%Y'), reverse=True)
    
    for record in all_records:
        status_emoji = "🔴" if record['Status'] == "LATE" else "🟢"
        print(f"{record['Date']} | {record['Time']} | {status_emoji} {record['Status']}")

def show_daily_report(attendance_df, date_str=None):
    """Show attendance report for a specific date"""
    if date_str is None:
        date_str = datetime.now().strftime("%d-%m-%Y")
    
    print(f"\n📅 DAILY ATTENDANCE REPORT - {date_str}")
    print("-" * 50)
    
    daily_attendance = attendance_df[attendance_df['Date'] == date_str]
    
    if daily_attendance.empty:
        print(f"❌ No attendance records found for {date_str}")
        return
    
    print(f"👥 Total Students Present: {len(daily_attendance)}")
    print("\nAttendance List:")
    print("Name          | Time     ")
    print("-" * 25)
    
    for _, row in daily_attendance.iterrows():
        print(f"{row['Name']:<12} | {row['Time']}")

def show_date_range_report(attendance_df, late_df, start_date, end_date):
    """Show attendance report for a date range"""
    print(f"\n📊 ATTENDANCE REPORT: {start_date} to {end_date}")
    print("-" * 50)
    
    # Filter data by date range
    try:
        start_dt = datetime.strptime(start_date, '%d-%m-%Y')
        end_dt = datetime.strptime(end_date, '%d-%m-%Y')
        
        filtered_attendance = attendance_df[
            attendance_df['Date'].apply(
                lambda x: start_dt <= datetime.strptime(x, '%d-%m-%Y') <= end_dt
            )
        ]
        
        if filtered_attendance.empty:
            print("❌ No attendance records found for this date range")
            return
        
        # Group by student
        student_stats = filtered_attendance.groupby('Name').agg({
            'Date': 'count'
        }).rename(columns={'Date': 'Days_Present'})
        
        print("Student Attendance Summary:")
        print("Name          | Days Present")
        print("-" * 30)
        
        for student, stats in student_stats.iterrows():
            print(f"{student:<12} | {stats['Days_Present']}")
            
    except ValueError:
        print("❌ Invalid date format. Please use DD-MM-YYYY")

def export_report_to_csv(attendance_df, late_df, students):
    """Export comprehensive report to CSV"""
    report_data = []
    
    for student in students:
        student_attendance = attendance_df[attendance_df['Name'] == student]
        student_late = late_df[late_df['Name'] == student]
        
        total_days = len(student_attendance)
        late_days = len(student_late)
        on_time_days = total_days - late_days
        punctuality_rate = (on_time_days / total_days * 100) if total_days > 0 else 0
        
        report_data.append({
            'Student_Name': student,
            'Total_Days_Present': total_days,
            'Days_On_Time': on_time_days,
            'Days_Late': late_days,
            'Punctuality_Rate': round(punctuality_rate, 2)
        })
    
    report_df = pd.DataFrame(report_data)
    filename = f"attendance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    report_df.to_csv(filename, index=False)
    print(f"📄 Report exported to: {filename}")

def main():
    """Main function to run the attendance report system"""
    display_header()
    
    # Check if attendance files exist
    if not os.path.exists('Attendance/Attendance_.csv'):
        print("❌ No attendance data found!")
        print("Please run the attendance system first to generate data.")
        return
    
    # Load data
    attendance_df, late_df = load_attendance_data()
    students = get_registered_students()
    
    if not students:
        print("❌ No registered students found!")
        return
    
    print(f"👥 Found {len(students)} registered students: {', '.join(students)}")
    
    while True:
        print("\n🔍 REPORT OPTIONS:")
        print("1. All Students Summary")
        print("2. Individual Student Report")
        print("3. Today's Attendance")
        print("4. Specific Date Report")
        print("5. Date Range Report")
        print("6. Export Report to CSV")
        print("7. Exit")
        
        choice = input("\nSelect option (1-7): ").strip()
        
        if choice == '1':
            show_all_students_summary(attendance_df, late_df, students)
            
        elif choice == '2':
            print(f"\nRegistered Students: {', '.join(students)}")
            student_name = input("Enter student name: ").strip()
            if student_name in students:
                show_student_detailed_report(student_name, attendance_df, late_df)
            else:
                print(f"❌ Student '{student_name}' not found!")
                
        elif choice == '3':
            show_daily_report(attendance_df)
            
        elif choice == '4':
            date_str = input("Enter date (DD-MM-YYYY): ").strip()
            show_daily_report(attendance_df, date_str)
            
        elif choice == '5':
            start_date = input("Enter start date (DD-MM-YYYY): ").strip()
            end_date = input("Enter end date (DD-MM-YYYY): ").strip()
            show_date_range_report(attendance_df, late_df, start_date, end_date)
            
        elif choice == '6':
            export_report_to_csv(attendance_df, late_df, students)
            
        elif choice == '7':
            print("👋 Goodbye!")
            break
            
        else:
            print("❌ Invalid option! Please select 1-7.")

if __name__ == "__main__":
    main()
