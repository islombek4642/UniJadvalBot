# 🖥 AWS EC2 Serverni Boshqarish Qo'llanmasi

Ushbu qo'llanma UniJadvalBot ishlayotgan AWS EC2 serverini boshqarish uchun barcha kerakli buyruqlar va ma'lumotlarni o'z ichiga oladi.

## 🔑 1. Serverga Ulanish (SSH)

Serverga ulanish uchun terminalda (PowerShell yoki CMD) loyiha papkasiga kiring va quyidagi buyruqni ishlating:

```bash
ssh -i unijadval-key3.pem ubuntu@98.94.54.91
```

> [!IMPORTANT]
> `unijadval-key3.pem` fayli serverga kirish uchun yagona kalit hisoblanadi. Uni yo'qotib qo'ymang!

---

## ⚙️ 2. Bot Xizmatini Boshqarish (systemd)

Bot serverda `unijadvalbot` xizmati sifatida ishlaydi. Uni boshqarish uchun quyidagi buyruqlar ishlatiladi:

| Amallar | Buyruq |
| :--- | :--- |
| **Holatni ko'rish** | `sudo systemctl status unijadvalbot` |
| **Qayta ishga tushirish** | `sudo systemctl restart unijadvalbot` |
| **To'xtatish** | `sudo systemctl stop unijadvalbot` |
| **Ishga tushirish** | `sudo systemctl start unijadvalbot` |

---

## 📜 3. Loglarni Kuzatish

Bot xatolarini yoki ish faoliyatini real vaqtda ko'rish uchun:

```bash
sudo journalctl -u unijadvalbot -f
```

*(Chiqish uchun `Ctrl + C` bosing)*

---

## 🔄 4. Kodni Yangilash (Update)

GitHub-dagi oxirgi o'zgarishlarni serverga tushirish uchun:

1. Serverga SSH orqali kiring.
2. Bot papkasiga o'ting:

   ```bash
   cd /opt/unijadvalbot
   ```

3. Kodni yangilang:

   ```bash
   git pull
   ```

4. Botni qayta ishga tushiring:

   ```bash
   sudo systemctl restart unijadvalbot
   ```

---

## 📝 5. Sozlamalarni O'zgartirish (.env)

Token yoki boshqa sozlamalarni o'zgartirish kerak bo'lsa:

1. Serverda `.env` faylini tahrirlang:

   ```bash
   sudo nano /opt/unijadvalbot/.env
   ```

2. O'zgarishlarni qilib, `Ctrl + O` (saqlash), `Enter` va `Ctrl + X` (chiqish) bosing.
3. Botni qayta ishga tushiring:

   ```bash
   sudo systemctl restart unijadvalbot
   ```

---

## 📂 6. Muhim Papkalar va Fayllar

- **Bot Joylashuvi**: `/opt/unijadvalbot`
- **Virtual Muhit (Python)**: `/opt/unijadvalbot/venv`
- **Baza (SQLite)**: `/opt/unijadvalbot/schedules.db`
- **Service Fayli**: `/etc/systemd/system/unijadvalbot.service`

---

## 🛠 7. Muammolarni Tuzatish (Troubleshooting)

- **Bot ishlamay qolsa**: Birinchi navbatda `sudo systemctl status unijadvalbot` buyrug'i bilan holatni tekshiring.
- **SQLite xatosi**: Agar baza bilan bog'liq xato bo'lsa, `/opt/unijadvalbot/schedules.db` fayli mavjudligini tekshiring.
- **Python-da xato bo'lsa**: `journalctl` loglarini tekshirib, xatoni o'qing.

---
*Developed with ❤️ for UniJadvalBot*
