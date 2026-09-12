# Maktab dars jadvali boti (TEST versiya)

Bu bot quyidagi funksiyalarni bajaradi:

- 👨‍🎓 **O'quvchi**: o'z sinfi jadvalini ko'rish (bugungi kun avtomatik + istalgan
  kunni tanlash), o'qituvchini qidirish (hozir qayerda ekanini ko'rsatadi),
  sinfni qidirish (hozir qaysi darsda ekanini ko'rsatadi)
- 👨‍🏫 **O'qituvchi**: o'z jadvalini ko'rish, qaysi sinflarda dars berishini
  ko'rish, boshqa o'qituvchi yoki sinfni qidirish
- 🔧 **Admin**: barcha foydalanuvchilarga xabar yuborish, botni texnik ishlar
  rejimiga o'tkazish, statistikani ko'rish

> ⚠️ **Diqqat:** hozircha `data.py` faylida **test (namunaviy) ma'lumotlar**
> bor — 3 ta sinf (5-A, 6-B, 7-A) va 7 ta o'qituvchi, avtomatik generatsiya
> qilingan. Haqiqiy jadval tayyor bo'lganda, shu faylni real ma'lumotlar bilan
> almashtirishingiz kerak (struktura fayl ichida tushuntirilgan).

## 1. Botni Telegram'da yaratish

1. Telegram'da [@BotFather](https://t.me/BotFather) ga yozing
2. `/newbot` buyrug'ini yuboring, nom va username bering
3. Sizga beriladigan **tokenni** saqlab qo'ying

## 2. Kompyuteringizda sinab ko'rish

```bash
cd school_bot
pip install -r requirements.txt

# Linux / macOS:
export BOT_TOKEN="sizning_tokeningiz"
export ADMIN_IDS="sizning_telegram_id"

# Windows (PowerShell):
$env:BOT_TOKEN="sizning_tokeningiz"
$env:ADMIN_IDS="sizning_telegram_id"

python bot.py
```

Telegram ID'ingizni bilmasangiz — botni ishga tushirib, unga `/id` buyrug'ini
yuboring, u ID'ingizni qaytaradi. Shundan keyin `ADMIN_IDS` ga shu raqamni
qo'yib, botni qayta ishga tushiring.

Bir nechta admin bo'lsa, vergul bilan ajrating: `ADMIN_IDS="111111,222222"`

## 3. Render'ga joylashtirish (deploy)

1. Bu papkani GitHub repo'siga yuklang
2. [render.com](https://render.com) da yangi **Background Worker** yarating
   va shu repo'ni bog'lang
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `python bot.py`
5. Environment tab'ida `BOT_TOKEN` va `ADMIN_IDS` qiymatlarini kiriting
6. Deploy qiling

> Background Worker doim ishlab turadi (polling rejimida), shuning uchun
> "uyg'otib turish" uchun cronjob/ping shart emas — bu faqat bepul **Web
> Service** turi uchun kerak bo'ladi.

## 4. Ma'lumotlarni yangilash

Haqiqiy dars jadvalingiz tayyor bo'lganda, `data.py` faylidagi `SCHEDULE`
lug'atini o'zingizning ma'lumotlaringiz bilan almashtiring, so'ng GitHub'ga
qayta yuklang — Render avtomatik qayta deploy qiladi.

## 5. Fayllar tuzilishi

```
school_bot/
├── bot.py           # Asosiy bot kodi (handler'lar)
├── data.py          # Sinflar jadvali (TEST ma'lumot - shu yerni o'zgartirasiz)
├── logic.py         # Vaqtni hisoblash, jadval bilan ishlash mantig'i
├── storage.py       # Statistika va texnik ishlar rejimi (JSON, vaqtinchalik)
├── requirements.txt # Kerakli kutubxonalar
├── Procfile         # Render uchun ishga tushirish buyrug'i
└── .env.example     # Environment o'zgaruvchilar namunasi
```
