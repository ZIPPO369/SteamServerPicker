# 🎮 Steam Server Picker

A powerful Windows desktop tool for managing Steam game server connections using firewall rules.  
Built with Python + CustomTkinter, designed for competitive players (e.g. CS2) who want full control over matchmaking regions and latency.

---

## 🚀 Features

- 🌍 Automatic Steam server detection (SDR config API)
- 📊 Real-time ping measurement per server
- 🧠 Region presets (EU, NA, ASIA, etc.)
- 🔒 Firewall-based server blocking (netsh integration)
- ⚡ Block / unblock all servers instantly
- 🎯 Per-server blocking toggle
- 🔎 Search and filter servers
- 📉 Ping range filtering system
- 🏳️ Country flag support for servers
- 📱 Responsive UI (adapts to window size)
- 🧩 Parallel ping system for performance
- 🛡️ Admin detection + elevation prompt

---

## 🖥️ Screenshots
*(optional – add images here later)*

---

## ⚙️ Requirements

- Windows 10 / 11
- Python 3.10+
- Administrator privileges (required for firewall changes)
- Steam installed (for CS2 / game routing)

---

## 📦 Installation

```bash
git clone https://github.com/your-username/steam-server-picker.git
cd steam-server-picker
pip install -r requirements.txt
