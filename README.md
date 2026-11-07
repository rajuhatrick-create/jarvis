# JARVIS — Just A Rather Very Intelligent System

A **self-learning AI assistant** with voice control, system management, web dashboard, and cloud deployment. Runs locally on your machine or in the cloud on Render.com.

## Features

### 🧠 Self-Learning AI
- **Teach JARVIS facts** — "teach me Python is a programming language"
- **Recall with variations** — "what is Python", "tell me about Python", "explain Python"
- **Entity extraction** — automatically learns about people, places, projects
- **Word network** — builds semantic associations from conversations
- **Internet learning** — fetches knowledge from Wikipedia while on power

### 🔊 Voice Control (Local Mode)
- Speech-to-text via browser (Web Speech API)
- Text-to-speech responses using Edge TTS (neural voices)
- Configurable language and voice

### 💻 System Control (Local Mode)
- **Volume control** — up, down, mute, set level
- **App management** — open, close, list running applications
- **System monitoring** — CPU, RAM, disk, battery status
- **File operations** — search, list, open files and folders

### 🌐 Web Dashboard
- Voice-first interface with large microphone button
- Real-time chat via WebSocket
- Live system stats graphs (Chart.js)
- Quick command buttons
- Reminder management
- Dark theme with responsive design

### ⏰ Task Automation
- Set reminders with natural language ("remind me in 30 minutes")
- Persistent storage of reminders
- Automatic alerts when due

### 🧮 Built-in Tools
- Calculator for math expressions
- Web search (opens browser)
- Jokes and inspirational quotes
- Time and date queries

### ☁️ Cloud Deployment
- Deploy to Render.com (free tier)
- SQLite database for cloud memory storage
- Cloud/local mode split with shared brain

## Quick Start (Local)

### Prerequisites
- Python 3.8+
- Windows 10/11

### Setup

1. **Navigate to the project directory:**
```bash
cd C:\Users\DELL\JARVIS
```

2. **Create a virtual environment:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements-local.txt
```

4. **Start JARVIS:**
```bash
python main.py
```

5. **Open your browser:**
```
http://localhost:8080
```

## Cloud Deployment (Render.com)

Deploy JARVIS to the cloud in 5 minutes:

### 1. Push to GitHub
```bash
cd C:\Users\DELL\JARVIS
git remote add origin https://github.com/YOUR_USERNAME/JARVIS.git
git push -u origin master
```

### 2. Deploy to Render.com
1. Go to [https://render.com](https://render.com) and sign up (free)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository (`JARVIS`)
4. Use these settings:
   - **Name:** jarvis-cloud
   - **Environment:** Python
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python main.py`
   - **Plan:** Free
5. Add environment variables:
   - `JARVIS_MODE` = `cloud`
   - `PORT` = `10000`
   - `DATABASE_PATH` = `/opt/render/app/data/jarvis.db`
6. Click **"Create Web Service"**

### 3. Access Your Cloud JARVIS
Render will provide a URL like: `https://jarvis-cloud-xxxx.onrender.com`

**Note:** Free tier spins down after 15 min idle. First request takes ~30-60s to wake up.

## Commands

### Time & Date
- "what time is it"
- "what's the date"
- "what day is it"

### Volume (Local Only)
- "volume up" / "volume down"
- "mute volume"
- "volume to 50"

### Applications (Local Only)
- "open Chrome" / "open VS Code"
- "close notepad"
- "list running apps"

### Files & Folders (Local Only)
- "open documents" / "open downloads"
- "search for report"
- "list files in desktop"

### System Info
- "system info" / "system status"
- "CPU usage" / "memory usage"
- "disk space" / "battery status"

### Web
- "search Python tutorial"
- "open google.com"

### Reminders
- "remind me in 30 minutes to take a break"
- "remind me at 3 PM about the meeting"
- "list my reminders"

### Calculator
- "calculate 25 * 4"
- "what is 100 / 7"

### Learning
- "teach me Python is a programming language"
- "what is Python"
- "learning status"
- "local status"

### Fun
- "tell me a joke"
- "give me a quote"

### General
- "hello" / "hi" / "hey"
- "help" (shows all commands)
- "goodbye" / "bye"

## Project Structure

```
JARVIS/
├── main.py                 # Entry point
├── config.yaml             # Configuration
├── requirements.txt        # Cloud dependencies (Linux-compatible)
├── requirements-local.txt  # Local dependencies (with Windows packages)
├── Procfile                # Render.com startup command
├── render.yaml             # Render.com service config
├── Dockerfile              # Container definition
├── .gitignore              # Git exclusions
├── data/                   # Runtime data (SQLite DB, local cache)
└── jarvis/
    ├── __init__.py
    ├── brain/              # Core intelligence
    │   ├── __init__.py
    │   ├── router.py       # Command parsing & routing
    │   ├── scheduler.py    # Task & reminder scheduler
    │   ├── learning.py     # Self-learning AI (TF-IDF memory)
    │   ├── local_learning.py  # Entity extraction, word network
    │   └── internet_learning.py  # Wikipedia knowledge fetching
    ├── tools/              # System utilities
    │   ├── __init__.py
    │   ├── system.py       # System control (volume, apps, info)
    │   ├── voice.py        # Speech recognition & Edge TTS
    │   ├── files.py        # File search & management
    │   ├── power.py        # Battery/power monitoring
    │   └── cloud_sync.py   # Cloud/local memory sync
    ├── database/           # Database layer
    │   ├── __init__.py
    │   └── sqlite_db.py    # SQLite cloud storage
    └── ui/                 # Web interface
        ├── __init__.py
        ├── server.py       # Starlette web server + WebSocket
        └── index.html      # Voice-first dashboard with Chart.js
```

## Configuration

Edit `config.yaml` to customize:

```yaml
server:
  host: "0.0.0.0"
  port: 8080

voice:
  language: "en-in"
  tts_voice: 0
  wake_word: "jarvis"

system:
  allowed_apps:
    - name: "chrome"
      path: "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
  favorite_dirs:
    documents: "C:\\Users\\DELL\\Documents"
    downloads: "C:\\Users\\DELL\\Downloads"
```

## Troubleshooting

- **Voice not working**: Make sure your microphone is connected and allowed in Windows settings
- **Apps not opening**: Check the paths in `config.yaml` are correct for your system
- **psutil errors**: Run `pip install psutil` in your virtual environment

## License

Personal project — free to use and modify.
