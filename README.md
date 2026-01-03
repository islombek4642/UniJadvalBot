# UniJadval Bot (Enhanced)

A Telegram bot for group chats that allows admins to set a weekly schedule image, which is then automatically broadcasted daily. This version is **Uzbek-first**, **fully automated**, and **modular**.

## Features

- **Multilingual Support**: Supports **Uzbek (default)** and **English**. Change language per chat with `/set_language`.
- **Automation**: One-click setup and start with `run.py`.
- **Localization**: All messages are stored in `constants/messages.py`, no hard-coded strings.
- **Admin Validation**: Only group admins can set or update schedules and change language.
- **Persistent Storage**: Uses SQLite for reliability.
- **Daily Broadcasts**: Automated schedule delivery via APScheduler.

## Quick Start (Automated)

1. **Clone the project.**
2. **Create `.env` file**:
   - Copy `.env.example` to `.env`.
   - Add your `BOT_TOKEN`.
3. **Run the automation script**:

   ```bash
   python run.py
   ```

   *This script will create a virtual environment, install dependencies, and start the bot.*

## Manual Setup

If you prefer to set up manually:

1. `python -m venv .venv`
2. `source .venv/bin/activate` (or `.venv\Scripts\activate` on Windows)
3. `pip install -r requirements.txt`
4. `python main.py`

## Usage

1. Add the bot to your Telegram group and make it an admin.
2. `/start` - Get a welcome message in the current language.
3. `/set_language` - Admin command to switch between Uzbek and English.
4. `/set_schedule` - Admin command to start the upload process.
5. Send an image when prompted.
6. The bot will send this image daily at the time set in `.env` (default `07:30`).
