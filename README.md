# 🎓 UniJadval Bot

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)
![Aiogram](https://img.shields.io/badge/Aiogram-3.x-2CA5E0?style=for-the-badge&logo=telegram)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**UniJadval Bot** — guruhlarda dars jadvallarini avtomatik yuborib turuvchi zamonaviy Telegram boti. U asosan talabalar va o'quv markazlari uchun mo'ljallangan bo'lib, har kuni belgilangan vaqtda guruhga dars jadvalini eslatib turadi.

---

## 🚀 Tezkor Deploy (Railway)

Eng oson yo'l — Railway orqali bepul serverga joylash:

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/new?template=https://github.com/islombek4642/UniJadvalBot&envs=BOT_TOKEN,ADMIN_ID&optionalEnvs=SCHEDULE_TIME,DATABASE_FILE)

> **⚠️ Muhim Eslatma**: Railway (va boshqa bulutli xizmatlar) `sqlite` fayllarni har safar perezagruzka bo'lganda o'chirib yuborishi mumkin. Ma'lumotlar yo'qolmasligi uchun Railway-da **Volume** ulang yoki shunchaki test uchun ishlating.

---

## 🔥 Asosiy Imkoniyatlar

- 🗣 **Ko'p tilli**: O'zbek (lotin) va Ingliz tillarini qo'llab-quvvatlaydi.
- 📅 **Jadvalni Avtomatlashtirish**: Guruh adminlari jadval rasmini yuklaydi va bot uni har kuni (masalan, 07:30 da) guruhga yuboradi.
- 🛑 **Weekend Mode**: "Dam olish kuni" rejimi. Guruhlarda Shanba va Yakshanba kunlari jadval yuborilmasligini sozlash mumkin.
- 🌍 **Public vs Private**: Bot guruhdagi username (link) bor yoki yo'qligini avtomatik aniqlaydi va admin panelda 🌐 (Ochiq) yoki 🔒 (Yopiq) belgisini ko'rsatadi.
- 📊 **Kengaytirilgan Statistika**: Admin uchun to'liq hisobot: foydalanuvchilar, faol jadvallar va umumiy guruhlar soni.
- 📢 **Global Broadcast**: Barcha foydalanuvchi va guruhlarga xabar yuborish imkoniyati (FSM va xavfsizlik tasdiqlari bilan).
- 🐳 **Docker Ready**: Ishga tushirish uchun to'liq Docker va Docker Compose qo'llab-quvvatlovi.

---

## 🛠 O'rnatish va Ishga Tushirish

### 1. Talablar

- Python 3.10+
- Git

### 2. Loyihani yuklab olish

```bash
git clone https://github.com/islombek4642/UniJadvalBot.git
cd UniJadvalBot
```

### 3. Konfiguratsiya (.env)

`.env.example` faylidan nusxa oling va `.env` deb nomlang:

```bash
cp .env.example .env
```

Fayl ichini o'zingizga moslang:

```ini
BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
ADMIN_ID=998877665
DATABASE_FILE=schedules.db
SCHEDULE_TIME=07:30
```

### 4. Ishga tushirish (Metod 1: Python)

Botni tezkor ishga tushirish uchun tayyor skriptdan foydalaning:

```bash
python run.py
```

*Bu skript avtomatik virtual muhit yaratadi, kutubxonalarni o'rnatadi va botni ishga tushiradi.*

### 5. Ishga tushirish (Metod 2: Docker) 🐳

Eng qulay va tavsiya etilgan usul:

```bash
docker-compose up -d --build
```

---

## 📖 Foydalanish Qo'llanmasi

### 👥 Guruh Adminlari Uchun

Botni guruhga qo'shing va **Admin** huquqini bering. Keyin quyidagi buyruqlarni ishlata olasiz:

| Buyruq | Tavsif |
| :--- | :--- |
| `/set_schedule` | Jadval rasmini yuklash (reply in photo). |
| `/set_time HH:MM` | Jadval yuboriladigan vaqtni o'zgartirish (masalan: `/set_time 08:00`). |
| `/weekend_mode` | Dam olish kunlari (Shanba, Yakshanba) jadval yuborishni yoqish/o'chirish. |
| `/set_language` | Bot tilini o'zgartirish (UZ/EN). |

### 👨‍💻 Bot Admini (Owner) Uchun

Bot egasi shaxsiy yozishmada (PM) quyidagi imkoniyatlarga ega:

- **📊 Statistika**: Foydalanuvchilar, faol jadvallar va jami guruhlar sonini ko'rish.
- **📢 Broadcast**: Barcha guruh va foydalanuvchilarga xabar tarqatish.
- **👥 Guruhlar Ro'yxati**: Bot qo'shilgan barcha guruhlarni ko'rish (Public 🌐 va Private 🔒 ajratilgan holda).
- **Tozalash**: Bot guruhdan chiqarilsa, baza avtomatik tozalanadi.

---

## 🤝 Hissa Qo'shish (Contributing)

1. Fork qiling.
2. Yangi branch oching (`git checkout -b feature/NewFeature`).
3. O'zgarishlarni commiting (`git commit -m 'Add new feature'`).
4. Push qiling (`git push origin feature/NewFeature`).
5. Pull Request yuboring.

---

## 📞 Aloqa

Savollar yoki takliflar bo'lsa, muallif bilan bog'laning.

---
*Developed with ❤️ by @islombek4642*
