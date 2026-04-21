# 🤖 HonneyAI — Futuristic Voice Assistant

A modern, fully-featured AI voice assistant with a **dark Jarvis-style UI** built in PyQt5.

---

## ✨ Features

| Feature | Details |
|---|---|
| 🎤 Voice Recognition | Google Web Speech API via `SpeechRecognition` |
| 🔊 Text-to-Speech | `pyttsx3` (offline) + PowerShell fallback |
| 🤖 AI Responses | Perplexity `sonar-pro` (online, conversational memory) |
| 🖥 UI | PyQt5 dark dashboard with mic animation, waveform, history panel |
| ⌨️ Text Mode | Type commands in the bottom bar — no mic needed |
| 🌐 Web Control | Open YouTube, Google, GitHub, Gmail, Reddit, Netflix, etc. |
| 💻 PC Control | Volume, mute, lock, shutdown, restart, open apps, screenshots |
| 📚 Wikipedia | Instant summaries with disambiguation handling |
| 🎵 Music | Play local files; search by song name |
| 😄 Jokes | Random programming jokes via `pyjokes` |
| 📁 AI Saves | Long AI answers saved to `ai_responses/` folder |

---

## 🗂 Project Structure

```
HonneyAI/
├── main.py                  ← Run this
├── requirements.txt
├── .env.example             ← Copy to .env and add your keys
├── honney.log               ← Created at runtime
│
├── utils/
│   ├── config.py            ← All settings (reads .env)
│   └── logger.py            ← Centralised logging
│
├── voice/
│   ├── tts.py               ← Text-to-speech
│   └── stt.py               ← Speech-to-text
│
├── core/
│   ├── commands.py          ← Every command the assistant can do
│   └── assistant.py         ← Intent routing (the brain)
│
└── ui/
    ├── styles.py            ← Dark theme colours & stylesheet
    ├── widgets.py           ← MicButton, WaveformWidget, StatusBadge
    └── main_window.py       ← Main PyQt5 application window
```

---

## 🚀 Setup (Step-by-Step)

### 1. Prerequisites

- **Python 3.10+** (3.11 recommended)
- **Windows 10/11** (Linux/macOS work with minor TTS changes)

### 2. Clone / Download

```bash
# If using git
git clone <your-repo-url>
cd HonneyAI

# Or just extract the ZIP into a folder called HonneyAI
```

### 3. Create a Virtual Environment (recommended)

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/macOS
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

> **PyAudio on Windows** — if `pip install pyaudio` fails, install the wheel manually:
> ```bash
> pip install pipwin
> pipwin install pyaudio
> ```

### 5. Configure Your API Key

```bash
# Copy the example file
copy .env.example .env      # Windows
# cp .env.example .env      # Linux/macOS

# Open .env in Notepad and add your Perplexity key
notepad .env
```

Get a free Perplexity API key at: https://www.perplexity.ai/settings/api

Your `.env` should look like:
```
PERPLEXITY_API_KEY=pplx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
ASSISTANT_NAME=Honney
USER_NAME=Harsh
WAKE_WORD=hey honey
```

### 6. Run the Assistant

```bash
python main.py
```

---

## 🎮 How to Use

| Action | How |
|---|---|
| **Start listening** | Click the mic button **or** press `Space` |
| **Send text command** | Type in the bottom bar and press `Enter` |
| **Cancel listening** | Press `Escape` |
| **Clear history** | Click "Clear History" in the left panel |

---

## 💬 Voice Commands

### 🕐 Time & Date
- *"What time is it?"*
- *"What's today's date?"*

### 🌐 Web
- *"Open YouTube / GitHub / Gmail / Netflix / Spotify"*
- *"Search for Python tutorials"*
- *"Play Blinding Lights on YouTube"*

### 💻 PC Control
- *"Volume up / down"*
- *"Mute / unmute"*
- *"Take a screenshot"*
- *"Lock the PC"*
- *"Open Notepad / Calculator / Task Manager"*
- *"Shutdown / Restart"*

### 📚 Knowledge
- *"Wikipedia Albert Einstein"*
- *"Tell me a joke"*

### 🎵 Music
- *"Play music"*
- *"Play song Bohemian Rhapsody"*

### 🤖 AI Conversation
- Anything not matching the above → sent to Perplexity AI with conversation memory

### ⚙ Assistant Settings
- *"Change your name"*
- *"Clear history"*
- *"Goodbye / Exit / Stop"*

---

## 🔧 Troubleshooting

| Problem | Fix |
|---|---|
| No mic input | Check Windows Sound Settings → Input device |
| PyAudio install fails | Use `pipwin install pyaudio` |
| pyttsx3 no voice | Run `python -c "import pyttsx3; e=pyttsx3.init(); print(e.getProperty('voices'))"` |
| AI not responding | Check `.env` has your Perplexity key and you have internet |
| UI fonts look off | Install "Segoe UI" font or the UI falls back to Arial |

---

## 📦 All Required Libraries

```bash
pip install PyQt5 pyttsx3 SpeechRecognition pyaudio openai \
            requests python-dotenv pyautogui wikipedia \
            pywhatkit pyjokes
```

---

## 🛠 Extending the Assistant

Add a new command in `core/commands.py` (write the function), then add a rule in `core/assistant.py`:

```python
# In core/assistant.py
@_rule(30, _any("weather", "temperature"))
def _weather(q):
    city = _strip(q, "weather", "temperature", "in", "at")
    return get_weather(city), True   # get_weather() defined in commands.py
```

That's it — no boilerplate, no re-routing logic.

---

*Built with ❤️ using Python, PyQt5, and Perplexity AI.*
