# 🎓 Smart Face Attendance System

A modern, intelligent face recognition-based attendance system with a beautiful web interface. Built with Python, OpenCV, and Flask.

![System Status](https://img.shields.io/badge/Status-Fully%20Operational-brightgreen)
![Python](https://img.shields.io/badge/Python-3.8+-blue)
![OpenCV](https://img.shields.io/badge/OpenCV-4.x-green)
![Flask](https://img.shields.io/badge/Flask-2.x-red)

## ✨ Features

- 🎯 **Real-time Face Recognition** - Advanced LBPH face recognition
- 🌐 **Modern Web Interface** - Beautiful Bootstrap dashboard
- 📊 **Analytics & Reports** - Interactive charts with Plotly
- 📱 **Responsive Design** - Works on desktop and mobile
- 🔒 **Secure Database** - SQLite with proper data handling
- 📈 **Late Tracking** - Automatic late arrival detection
- 💾 **Export Functionality** - CSV export for reports
- 🍎 **macOS Optimized** - Native camera support

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- macOS (optimized for Mac cameras)
- Webcam/Built-in camera

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/web3saad/Smart-Face-Attendance-System.git
   cd Smart-Face-Attendance-System
   ```

2. **Create virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Start the system:**
   ```bash
   python attendance_web_gui_clean.py
   ```

5. **Open your browser:**
   ```
   http://localhost:8080
   ```

## 🎯 How to Use

### 📝 Register Students
1. Click **"Register Student"** in the web interface
2. Enter the student's name
3. Camera window opens automatically
4. Capture 20+ face samples from different angles
5. Press 'q' to finish registration

### ✅ Take Attendance
1. Click **"Start Attendance"** button
2. Camera opens for face recognition
3. Students approach the camera one by one
4. Attendance is automatically logged

### 📊 View Reports
- Real-time dashboard with statistics
- Interactive charts and analytics
- Filter attendance by date
- Export data to CSV

## 🛠️ System Components

### Core Files
- `attendance_web_gui_clean.py` - Main web application
- `main_improved.py` - Attendance tracking engine
- `web_register.py` - Student registration script
- `templates/dashboard.html` - Web interface

### Utilities
- `camera_utils.py` - Camera detection and testing
- `configure_camera.py` - Camera setup helper
- `reset_database.py` - Database reset utility

## 📁 Project Structure

```
Smart-Face-Attendance-System/
├── attendance_web_gui_clean.py    # Main web application
├── main_improved.py               # Attendance tracking
├── web_register.py                # Registration script
├── student_db.py                  # Database management
├── templates/
│   └── dashboard.html             # Web interface
├── data/
│   └── attendance.db              # SQLite database
├── Attendance/
│   ├── Attendance_.csv            # Main attendance log
│   └── late_attendance_record.csv # Late arrivals
├── requirements.txt               # Python dependencies
├── haarcascade_frontalface_default.xml # Face detection model
└── README.md                      # This file
```

## 🔧 Configuration

### Camera Settings
The system automatically detects and configures your camera. For macOS users:
- Uses AVFoundation backend for optimal performance
- Prioritizes built-in camera over external/iPhone cameras
- No iPhone continuity camera notifications

### Database Setup
- Automatic SQLite database creation
- Face data stored securely as BLOB
- Attendance logs in both database and CSV format

## 📊 Features in Detail

### Web Dashboard
- 📈 Real-time statistics
- 👥 Student management
- 📅 Attendance records with date filtering
- 📊 Interactive charts and analytics
- 💾 Export functionality
- 🗄️ Database management

### Face Recognition
- Advanced LBPH (Local Binary Pattern Histogram) algorithm
- Adaptive confidence thresholds
- Multiple face detection in single frame
- Robust against lighting variations

### Attendance Tracking
- Real-time face recognition
- Automatic attendance logging
- Late arrival detection and tracking
- Duplicate prevention (cooldown periods)
- Multi-format data storage (DB + CSV)

## 🚀 Advanced Usage

### Manual Commands

**Test Camera:**
```bash
python camera_utils.py
```

**Register Student (CLI):**
```bash
python web_register.py "Student Name"
```

**Start Attendance (CLI):**
```bash
python main_improved.py
```

**Reset Database:**
```bash
python reset_database.py
```

## 🐛 Troubleshooting

### Common Issues

**Camera not opening:**
```bash
python configure_camera.py
```

**Registration errors:**
- Ensure good lighting
- Capture 20+ samples minimum
- Face the camera directly

**iPhone notifications:**
- System automatically uses Mac built-in camera
- Turn off Handoff in System Settings if needed

### System Requirements
- **OS**: macOS (optimized), Windows, Linux
- **Python**: 3.8 or higher
- **RAM**: 4GB minimum, 8GB recommended
- **Camera**: Built-in webcam or USB camera

## 📝 Documentation

- [`SYSTEM_READY.md`](SYSTEM_READY.md) - Complete usage guide
- [`CAMERA_FIXES.md`](CAMERA_FIXES.md) - Camera troubleshooting
- [`FIXES_APPLIED.md`](FIXES_APPLIED.md) - Technical fixes log

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- OpenCV community for face recognition algorithms
- Flask team for the web framework
- Bootstrap for the beautiful UI components
- Plotly for interactive charts

## 🔗 Links

- **GitHub Repository**: https://github.com/web3saad/Smart-Face-Attendance-System
- **Issues**: https://github.com/web3saad/Smart-Face-Attendance-System/issues
- **Releases**: https://github.com/web3saad/Smart-Face-Attendance-System/releases

---

**Status**: ✅ Fully Operational | **Last Updated**: July 2025

Made with ❤️ for educational institutions and organizations