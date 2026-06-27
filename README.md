# 🎙️ VCFight V2 - Advanced Voice Chat Bot

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

## 📖 Features

- 🎤 **Voice Chat Bridge** - Forward audio between groups
- 🖥️ **Screenshare** - Share screen in voice chats
- 🎛️ **Audio Effects** - Bass boost, echo, loudness, gain
- 📻 **Radio Streaming** - Play internet radio
- 🎵 **YouTube Support** - Play YouTube audio
- 🎚️ **Live Effects Control** - Real-time audio processing

## 🚀 Commands

### Voice Chat
| Command | Description |
|---------|-------------|
| `/bridge <target>` | Start audio bridge |
| `/leavevc` | Leave voice chat |
| `/joinvc` | Join voice chat |
| `/vcstatus` | Check status |

### Screenshare
| Command | Description |
|---------|-------------|
| `/screenshare [quality] [fps]` | Start screenshare (replies with pic) |
| `/screenshareoff` | Stop screenshare |

### Audio Effects
| Command | Description |
|---------|-------------|
| `/bass <0-100>` | Set bass boost |
| `/echo <0-100>` | Set echo effect |
| `/loudness <0-100>` | Set loudness |
| `/gain <0-500>` | Set volume |
| `/effects` | Show all effects |
| `/preset <name>` | Apply preset |
| `/reset` | Reset effects |

### Streaming
| Command | Description |
|---------|-------------|
| `/radio <url>` | Play radio stream |
| `/yt <url>` | Play YouTube audio |
| `/play` | Play replied audio file |

### Admin (Private Chat)
| Command | Description |
|---------|-------------|
| `/addstring <session>` | Add assistant |
| `/removeassistant` | Remove assistant |
| `/assistants` | List assistants |
| `/stopall` | Stop all bridges |
| `/bridges` | List active bridges |

## 📦 Installation

### Local Setup
```bash
# Clone repository
git clone https://github.com/yourusername/vcfight-v2
cd vcfight-v2

# Create virtual environment
python3.10 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install system dependencies (Ubuntu/Debian)
sudo apt install ffmpeg pulseaudio scrot

# Create .env file
cp .env.example .env
# Edit .env with your credentials

# Run validation
python validate_startup.py

# Start bot
python main.py