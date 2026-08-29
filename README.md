# ⚓ Nakama Streak

A full-stack discipline tracker built with Python Django + SQLite.
Black & white premium UI with GitHub-style heatmap, Pomodoro timer, and badge system.

---

## Features
- 🔐 Register / Login (Django auth)
- 🗓️ **Voyage Log** — GitHub-style contribution heatmap (52 weeks)
- 📋 **Task System** — schedule tasks for any future date; locked until that day
- 🍅 **Pomodoro Timer** — 25 / 45 / 60 min focus sessions with ring animation
- 🏆 **Badge System** — streak badges + achievement badges (locked/unlocked display)
- 🛡️ **Streak Shields** — protect your streak on a missed day
- 🌙 **Midnight / Paper theme** toggle
- 📊 **History** — last 90 days with progress bars
- 📱 Responsive design

---

## Quick Start

```bash
# 1. Make sure Python 3.10+ is installed
python --version

# 2. Install Django
pip install Django

# 3. Run setup + start server
bash start.sh

# OR manually:
python manage.py migrate
python manage.py create_badges
python manage.py runserver
```

Open → **http://127.0.0.1:8000**

---

## Stack
| Layer    | Tech                  |
|----------|-----------------------|
| Backend  | Python 3 + Django 4.2 |
| Database | SQLite (db.sqlite3)   |
| Frontend | Vanilla HTML/CSS/JS   |
| Auth     | Django built-in auth  |

---

## Project Structure
```
nakama_streak/
├── manage.py
├── start.sh
├── requirements.txt
├── db.sqlite3          ← auto-created on first run
├── nakama/             ← Django project config
├── accounts/           ← auth app (register/login/profile)
├── tracker/            ← main app (tasks/streaks/badges/pomodoro)
├── templates/          ← HTML templates
└── static/             ← CSS + JS
```

---

## Badge System
| Badge          | Type        | Unlock                    |
|----------------|-------------|---------------------------|
| First Step     | Achievement | Complete 1 day            |
| Shield Bearer  | Achievement | Use a shield              |
| Focus Master   | Achievement | 25 pomodoro sessions      |
| Architect      | Achievement | Create 10 tasks           |
| Century        | Achievement | Complete 100 days total   |
| Zen Mode       | Achievement | 100 pomodoro sessions     |
| Navigator      | Streak      | 30-day streak             |
| Rookie Sailor  | Streak      | 50-day streak             |
| Warrior        | Streak      | 100-day streak            |
| Legend         | Streak      | 365-day streak            |

Streak badges also grant +1 shield when earned!

---

*Built with ❤️ — keep the streak alive, nakama.*
