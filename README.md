# 🎓 UniJadval Bot

![Python](https://img.shields.io/badge/Python-3.11%2B-blue?style=for-the-badge&logo=python)
![Aiogram](https://img.shields.io/badge/Aiogram-3.x-2CA5E0?style=for-the-badge&logo=telegram)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**UniJadval Bot** — guruhlarda dars jadvallarini avtomatik yuborib turuvchi Telegram boti. Talabalar va o'quv markazlari uchun mo'ljallangan.

---

## 🚀 Tezkor O'rnatish

```bash
# 1. Loyihani yuklab olish
git clone https://github.com/islombek4642/UniJadvalBot.git
cd UniJadvalBot

# 2. Konfiguratsiya
cp .env.example .env
# .env faylini tahrirlang (BOT_TOKEN va ADMIN_ID)

# 3. Ishga tushirish
python run.py
```

---

## 🔥 Asosiy Imkoniyatlar

| Imkoniyat | Tavsif |
| :--- | :--- |
| 🌐 **Ko'p tilli** | O'zbek va Ingliz tillarini qo'llab-quvvatlaydi |
| 📅 **Avto-jadval** | Har kuni belgilangan vaqtda jadval yuboradi |
| ⏰ **Moslashuvchan vaqt** | Har bir guruh uchun alohida vaqt sozlash |
| 🛑 **Weekend Mode** | Shanba/Yakshanba kunlari jadval yubormaslik |
| 📊 **Statistika** | Foydalanuvchilar va guruhlar hisoboti |
| 📢 **Broadcast** | Barcha foydalanuvchilarga xabar yuborish |

---

## 📁 Loyiha Tuzilishi

```text
UniJadvalBot/
├── main.py              # Bot entry point
├── database.py          # SQLite database operations
├── scheduler.py         # Daily broadcast scheduler
├── run.py               # Quick start script
├── handlers/
│   ├── __init__.py      # Router aggregation
│   ├── common.py        # Shared keyboards & utilities
│   ├── start.py         # /start, /cancel, contact
│   ├── schedule.py      # /set_schedule, /set_time
│   ├── settings.py      # /set_language, /weekend_mode
│   ├── admin_panel.py   # /stats, users, groups
│   ├── broadcast.py     # Broadcast feature
│   └── events.py        # Bot added/removed events
├── constants/
│   └── messages.py      # Localization (UZ/EN)
├── utils/
│   └── admin_check.py   # Admin verification
├── tests/
│   └── test_database.py # Automated tests
└── deploy/              # Docker & systemd configs
```

---

## 🛠 Konfiguratsiya

`.env` fayli:

```ini
BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
ADMIN_ID=998877665
SCHEDULE_TIME=07:30
TIMEZONE=Asia/Tashkent
DATABASE_FILE=schedules.db
```

---

## 📖 Buyruqlar

### 👥 Guruh Adminlari Uchun

| Buyruq | Tavsif |
| :--- | :--- |
| `/set_schedule` | Jadval rasmini yuklash |
| `/set_time HH:MM` | Yuborish vaqtini o'zgartirish |
| `/weekend_mode` | Dam olish kunlari rejimini yoqish/o'chirish |
| `/set_language` | Bot tilini o'zgartirish |
| `/help` | Yordam |

### 👨‍💻 Bot Admini Uchun (PM)

| Tugma | Tavsif |
| :--- | :--- |
| 📊 Statistika | Foydalanuvchilar va guruhlar soni |
| 📢 Broadcast | Hammaga xabar yuborish |
| 👥 Guruhlar | Barcha guruhlar ro'yxati |
| 👤 Foydalanuvchilar | Ro'yxatdan o'tganlar |

---

## 🐳 Docker bilan Ishga Tushirish

```bash
docker-compose up -d --build
```

---

## 🧪 Testlarni Ishga Tushirish

```bash
pip install pytest
python -m pytest tests/ -v
```

---

## 📞 Aloqa

Savollar yoki takliflar bo'lsa: [@islombek4642](https://t.me/islombek4642)

---

### Developed with ❤️ by @islombek4642
