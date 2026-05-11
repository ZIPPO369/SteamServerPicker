# 🎮 Steam Server Picker

A lightweight Windows tool for managing Steam game server connections using Windows Firewall rules.

Built with Python + CustomTkinter, designed for competitive games like CS2 where latency and region control matters.
<img width="1167" height="832" alt="image" src="https://github.com/user-attachments/assets/18ebd298-937c-4c65-a5d4-52f33b26707c" />

---

## ⚡ One-click download

👉 **[Download SteamServerPicker](https://github.com/ZIPPO369/SteamServerPicker/releases/download/v1.0.0/SteamServerPicker.exe)**

---

## ✨ Features

- 🌍 Automatic Steam server detection (SDR API)
- 📊 Real-time ping measurement
- 🧠 Region presets (EU / NA / ASIA / OTHER)
- 🔒 Block or unblock servers via Windows Firewall
- ⚡ One-click block / unblock all servers
- 🎯 Per-server control
- 🔎 Search & filtering system
- 📉 Ping range filter
- 🏳️ Country flag support
- 📱 Responsive adaptive UI
- 🧩 Parallel ping system for performance
- 🛡️ Admin detection with elevation prompt

---

## 🚀 How to use

### For users (recommended)
1. Download the `.exe` from Releases or link above
2. Run the program
3. Allow administrator permissions (required for firewall control)

---

## 🛠️ For developers

```bash
git clone https://github.com/ZIPPO369/SteamServerPicker.git
cd SteamServerPicker
pip install -r requirements.txt
python main.py
