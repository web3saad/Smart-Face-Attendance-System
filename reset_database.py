#!/usr/bin/env python3
"""
Database Reset Script
This script clears all student data and attendance records for a fresh start
"""
import sqlite3
import os
import pandas as pd
from datetime import datetime

def clear_database():
    """Clear all face data from the database"""
    try:
        conn = sqlite3.connect('data/attendance.db')
        cursor = conn.cursor()
        
        # Clear the faces table
        cursor.execute("DELETE FROM faces")
        conn.commit()
        
        # Get count to verify
        cursor.execute("SELECT COUNT(*) FROM faces")
        count = cursor.fetchone()[0]
        
        conn.close()
        
        if count == 0:
            print("✅ Database cleared successfully!")
            return True
        else:
            print(f"❌ Error: {count} records still remain")
            return False
            
    except Exception as e:
        print(f"❌ Error clearing database: {e}")
        return False

def backup_attendance_data():
    """Backup existing attendance data before clearing"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    try:
        # Backup attendance file
        if os.path.exists('Attendance/Attendance_.csv'):
            backup_file = f"Attendance/Attendance_backup_{timestamp}.csv"
            df = pd.read_csv('Attendance/Attendance_.csv')
            df.to_csv(backup_file, index=False)
            print(f"📄 Attendance data backed up to: {backup_file}")
        
        # Backup late attendance file  
        if os.path.exists('Attendance/late_attendance_record.csv'):
            backup_file = f"Attendance/late_attendance_backup_{timestamp}.csv"
            df = pd.read_csv('Attendance/late_attendance_record.csv')
            df.to_csv(backup_file, index=False)
            print(f"📄 Late attendance data backed up to: {backup_file}")
            
    except Exception as e:
        print(f"⚠️ Warning: Could not backup attendance data: {e}")

def clear_attendance_files():
    """Clear attendance CSV files"""
    try:
        # Clear main attendance file
        if os.path.exists('Attendance/Attendance_.csv'):
            df = pd.DataFrame(columns=["Name", "Time", "Date"])
            df.to_csv('Attendance/Attendance_.csv', index=False)
            print("✅ Attendance file cleared")
        
        # Clear late attendance file
        if os.path.exists('Attendance/late_attendance_record.csv'):
            df = pd.DataFrame(columns=["Name", "Time", "Date"])
            df.to_csv('Attendance/late_attendance_record.csv', index=False)
            print("✅ Late attendance file cleared")
            
    except Exception as e:
        print(f"❌ Error clearing attendance files: {e}")

def main():
    print("🗑️  DATABASE RESET UTILITY")
    print("=" * 50)
    print("This will clear ALL student registrations and attendance data!")
    print("You'll need to register all students again from scratch.")
    print()
    
    # Show current database status
    try:
        conn = sqlite3.connect('data/attendance.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM faces")
        face_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(DISTINCT name) FROM faces")
        student_count = cursor.fetchone()[0]
        conn.close()
        
        print(f"📊 Current Database Status:")
        print(f"   Students registered: {student_count}")
        print(f"   Face samples stored: {face_count}")
    except:
        print("📊 Database status: Unable to read")
    
    print()
    
    # Confirmation
    confirm1 = input("❓ Are you sure you want to clear the database? (yes/no): ").strip().lower()
    
    if confirm1 != 'yes':
        print("❌ Operation cancelled")
        return
    
    confirm2 = input("❓ This action cannot be undone. Type 'DELETE' to confirm: ").strip()
    
    if confirm2 != 'DELETE':
        print("❌ Operation cancelled")
        return
    
    print("\n🔄 Starting database reset...")
    
    # Backup existing data
    print("\n1. Backing up existing attendance data...")
    backup_attendance_data()
    
    # Clear database
    print("\n2. Clearing student registration database...")
    if clear_database():
        print("✅ Student database cleared successfully!")
    else:
        print("❌ Failed to clear student database!")
        return
    
    # Clear attendance files
    print("\n3. Clearing attendance files...")
    clear_attendance_files()
    
    print("\n🎉 DATABASE RESET COMPLETE!")
    print("=" * 50)
    print("✅ All student registrations cleared")
    print("✅ All attendance records cleared") 
    print("✅ Backup files created")
    print()
    print("📝 Next Steps:")
    print("1. Register students using: student_db_improved.py")
    print("2. Start taking attendance using: main_simplified.py")
    print()
    print("🔄 You can now register students from scratch!")

if __name__ == "__main__":
    main()
