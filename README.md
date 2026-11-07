# JARVIS — Just A Rather Very Intelligent System

A **local AI assistant** for Windows with voice control, system management, web dashboard, and task automation. No cloud APIs required — everything runs on your machine.

## Features

### 🧠 Hybrid Intelligence
- **Rule-based commands** for fast, reliable system operations
- **Local LLM support** (Ollama) for natural conversation (optional)

### 🔊 Voice Control
- Speech-to-text via browser (Web Speech API)
- Text-to-speech responses (pyttsx3)
- Configurable language and voice

### 💻 System Control
- **Volume control** — up, down, mute, set level
- **App management** — open, close, list running applications
- **System monitoring** — CPU, RAM, disk, battery status
- **File operations** — search, list, open files and folders

### 🌐 Web Dashboard
- Real-time chat interface via WebSocket
- Live system stats (CPU, RAM, disk)
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

## Installation

### Prerequisites
- Python 3.8+
- Windows 10/11

### Setup

1. **Navigate to the project directory:**
```bash
cd C:\Users\DELL\OneDrive\JARVIS
```

2. **Create a virtual environment:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure (optional):**
Edit `config.yaml` to customize:
- Server port and host
- Voice settings (language, TTS voice)
- Allowed applications
- Favorite directories
- Local LLM settings (Ollama)

## Usage

### Start JARVIS
```bash
python main.py
```

This starts the web server. Open your browser to:
```
http://localhost:8080
```

### Optional: Enable Local AI (Ollama)

1. Install [Ollama](https://ollama.ai)
2. Pull a model: `ollama pull phi3`
3. In `config.yaml`, set:
```yaml
llm:
  enabled: true
  model: "phi3"
```

## Commands

### Time & Date
- "what time is it"
- "what's the date"
- "what day is it"

### Volume
- "volume up" / "volume down"
- "mute volume"
- "volume to 50"

### Applications
- "open Chrome" / "open VS Code"
- "close notepad"
- "list running apps"

### Files & Folders
- "open documents" / "open downloads"
- "search for report"
- "list files in desktop"

### System Info
- "system info"
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
├── requirements.txt        # Python dependencies
├── data/                   # Runtime data (reminders)
└── jarvis/
    ├── __init__.py
    ├── brain/              # Core intelligence
    │   ├── __init__.py
    │   ├── router.py       # Command parsing & routing
    │   └── scheduler.py    # Task & reminder scheduler
    ├── tools/              # System utilities
    │   ├── __init__.py
    │   ├── system.py       # System control (volume, apps, info)
    │   ├── voice.py        # Speech recognition & TTS
    │   └── files.py        # File search & management
    └── ui/                 # Web interface
        ├── __init__.py
        ├── server.py       # Starlette web server
        └── index.html      # Dashboard frontend
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
