# 🎮 Steam Server Picker

<<<<<<< HEAD
Moderní a rychlá aplikace pro blokování nechtěných CS:GO/CS2 (Steam) serverů pomocí Windows Firewallu.

![Steam Server Picker UI](https://github.com/ZIPPO369/SteamServerPicker/raw/main/screenshot.png) *(Poznámka: Přidejte screenshot po nahrání)*

## ✨ Funkce
- **Plynulé UI:** Agresivní optimalizace pro hladké zvětšování/zmenšování okna.
- **Adaptivní Layout:** Automatické skrývání prvků při malé velikosti okna.
- **Vlajky zemí:** Okamžité asynchronní načítání vlajek pro každý server.
- **Rychlé Presety:** Blokování celých regionů (Evropa, Amerika, Asie) na jedno kliknutí.
- **Ping Checker:** Automatické měření odezvy všech serverů v reálném čase.

## 🚀 Jak spustit (pro uživatele)
Nejjednodušší způsob, jak program používat:
1. Přejděte do sekce **[Releases](https://github.com/ZIPPO369/SteamServerPicker/releases)**.
2. Stáhněte si nejnovější verzi souboru `SteamServerPicker.exe`.
3. Spusťte jej (program si automaticky vyžádá práva administrátora pro úpravu Firewallu).

## 🛠️ Pro vývojáře
Pokud chcete program upravovat:
1. Nainstalujte Python 3.10+.
2. Nainstalujte závislosti: `pip install -r requirements.txt`.
3. Spusťte: `python main.py`.

## 📜 Licence
Tento projekt je open-source pod licencí **MIT**. Více v souboru [LICENSE](LICENSE).
=======
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
>>>>>>> origin/main
