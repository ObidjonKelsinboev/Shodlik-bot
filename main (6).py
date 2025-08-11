import json
import datetime
from telegram import (
    Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto, ReplyKeyboardRemove
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
)
from telegram.constants import ChatAction
import re
import random

ADMIN_ID = 1143475155  # Admin user_id
TOKEN = '8025141379:AAFqQQYicKKn7tt3d1Loj2AoiTnE94jESvI'

def load_data():
    try:
        with open('data.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {
            'rooms': [],
            'about': {'uz': '', 'ru': ''},
            'location': '',
            'restaurant': '',
            'bookings': [],
            'lang': {},
        }

def save_data(data):
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_lang(user_id, data):
    return data['lang'].get(str(user_id), 'uz')

def set_lang(user_id, lang, data):
    data['lang'][str(user_id)] = lang
    save_data(data)

def main_menu(lang, is_admin=False):
    if lang == 'uz':
        rows = [
            ['🏨 Xonalar', '📞 Aloqa'],
            ['📍 Lokatsiya', 'ℹ️ Biz haqimizda'],
            ['🍽 Restoran', '🌐 Til']
        ]
        if is_admin:
            rows.append(['🛠 Admin Panelga kirish'])
        return ReplyKeyboardMarkup(rows, resize_keyboard=True)
    else:
        rows = [
            ['🏨 Номера', '📞 Oбратная связь'],
            ['📍 Локация', 'ℹ️ О нас'],
            ['🍽 Ресторан', '🌐 Язык']
        ]
        if is_admin:
            rows.append(['🛠 Войти в админ-панель'])
        return ReplyKeyboardMarkup(rows, resize_keyboard=True)

def admin_panel_menu(lang):
    if lang == 'uz':
        return ReplyKeyboardMarkup([
            ['🏨 Xonalar ro‘yxati', '➕ Xona qo‘shish'],
            ['❌ Xona o‘chirish', '📋 Bronlar ro‘yxati'],
            ['❌ Bronni o‘chirish'],
            ['➕ Sifat qo‘shish', '❌ Sifat o‘chirish'],
            ['ℹ️ Biz haqimizda o‘zgartirish'],
            ['📍 Lokatsiyani o‘zgartirish'],
            ['🍽 Restoran raqamini o‘zgartirish'],
            ['Orqaga']
        ], resize_keyboard=True)
    else:
        return ReplyKeyboardMarkup([
            ['🏨 Список номеров', '➕ Добавить номер'],
            ['❌ Удалить номер', '📋 Список броней'],
            ['❌ Удалить бронь'],
            ['➕ Добавить качество', '❌ Удалить качество'],
            ['ℹ️ Изменить о нас'],
            ['📍 Изменить локацию'],
            ['🍽 Изменить номер ресторана'],
            ['Назад']
        ], resize_keyboard=True)

def room_quality_menu(lang):
    data = load_data()
    qualities = data.get('qualities', [])
    if not qualities:
        # Default sifatlar
        qualities = ['Lux', 'Oddiy', 'Normal'] if lang == 'uz' else ['Люкс', 'Обычный', 'Нормальный']
    kb = [[InlineKeyboardButton(q, callback_data=f'room_quality_{q}')] for q in qualities]
    return InlineKeyboardMarkup(kb)

def room_delete_menu(data):
    kb = [[InlineKeyboardButton(f"{r['name']} (ID:{r['id']})", callback_data=f"delroom_{r['id']}")] for r in data['rooms']]
    return InlineKeyboardMarkup(kb)

def room_delete_confirm_menu(room_id, lang):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton('Ha' if lang == 'uz' else 'Да', callback_data=f'confirm_delroom_yes_{room_id}'),
            InlineKeyboardButton('Yo‘q' if lang == 'uz' else 'Нет', callback_data=f'confirm_delroom_no_{room_id}')
        ]
    ])

def room_quality_inline(lang):
    data = load_data()
    qualities = data.get('qualities', [])
    if not qualities:
        qualities = ['Lux', 'Oddiy', 'Normal'] if lang == 'uz' else ['Люкс', 'Обычный', 'Нормальный']
    kb = [[InlineKeyboardButton(q, callback_data=f'room_quality_{q}')] for q in qualities]
    return InlineKeyboardMarkup(kb)

def month_menu(lang, prefix='month_'):
    months_uz = ['Yanvar', 'Fevral', 'Mart', 'Aprel', 'May', 'Iyun', 'Iyul', 'Avgust', 'Sentabr', 'Oktabr', 'Noyabr', 'Dekabr']
    months_ru = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']
    months = months_uz if lang == 'uz' else months_ru
    kb = []
    for i in range(0, 12, 3):
        row = [InlineKeyboardButton(months[j], callback_data=f'{prefix}{j+1}') for j in range(i, min(i+3, 12))]
        kb.append(row)
    return InlineKeyboardMarkup(kb)

def days_menu(year, month, prefix='day_', booked_days=None, lang='uz'):
    days = (datetime.date(year, month % 12 + 1, 1) - datetime.timedelta(days=1)).day
    if booked_days is None:
        booked_days = set()
    kb = []
    row = []
    for d in range(1, days + 1):
        if d not in booked_days:
            row.append(InlineKeyboardButton(str(d), callback_data=f'{prefix}{d}'))
        if len(row) == 7:
            kb.append(row)
            row = []
    if row:
        kb.append(row)
    # Orqaga tugmasi
    kb.append([InlineKeyboardButton('Orqaga' if lang == 'uz' else 'Назад', callback_data=f'{prefix}back')])
    return InlineKeyboardMarkup(kb)

def user_rooms_menu(data, lang):
    kb = [[InlineKeyboardButton(f"{r['name']}", callback_data=f"user_room_{r['id']}")] for r in data['rooms']]
    kb.append([InlineKeyboardButton('Orqaga' if lang == 'uz' else 'Назад', callback_data='user_back')])
    return InlineKeyboardMarkup(kb)

def user_room_detail_menu(room_id, lang):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('Bron qilish' if lang == 'uz' else 'Забронировать', callback_data=f"user_book_{room_id}")],
        [InlineKeyboardButton('Orqaga' if lang == 'uz' else 'Назад', callback_data='user_quality_back')]
    ])

def check_booking_conflict(bookings, room_id, from_date, to_date):
    for b in bookings:
        if b['room_id'] == room_id:
            b_from = datetime.datetime.strptime(b['from'], '%Y-%m-%d').date()
            b_to = datetime.datetime.strptime(b['to'], '%Y-%m-%d').date()
            if (from_date <= b_to and to_date >= b_from):
                return True
    return False

def get_message_text(update):
    if hasattr(update, 'message') and update.message and update.message.text:
        return update.message.text
    elif hasattr(update, 'callback_query') and update.callback_query and update.callback_query.message and update.callback_query.message.text:
        return update.callback_query.message.text
    return None

async def smart_reply(update, text, **kwargs):
    if hasattr(update, 'message') and update.message:
        return await update.message.reply_text(text, **kwargs)
    elif hasattr(update, 'callback_query') and update.callback_query and update.callback_query.message:
        return await update.callback_query.message.reply_text(text, **kwargs)

def get_booked_days_for_month(bookings, room_id, year, month):
    booked_days = set()
    for b in bookings:
        if b['room_id'] == room_id:
            b_from = datetime.datetime.strptime(b['from'], '%Y-%m-%d').date()
            b_to = datetime.datetime.strptime(b['to'], '%Y-%m-%d').date()
            current = b_from
            while current <= b_to:
                if current.year == year and current.month == month:
                    booked_days.add(current.day)
                current += datetime.timedelta(days=1)
    return booked_days

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    user_id = update.effective_user.id
    lang = get_lang(user_id, data)
    is_admin = (user_id == ADMIN_ID)
    await smart_reply(
        update,
        'Xush kelibsiz!' if lang == 'uz' else 'Добро пожаловать!',
        reply_markup=main_menu(lang, is_admin)
    )

def clean_text(text):
    # O‘, o', ў harflarini oddiy o ga almashtiradi
    return re.sub(r'[^a-zA-Zа-яА-ЯёЁ0-9]', '', text.lower().replace('o‘', 'o').replace("o'", 'o').replace('ў', 'o'))

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    user_id = update.effective_user.id
    lang = get_lang(user_id, data)
    is_admin = (user_id == ADMIN_ID)
    text = update.message.text if update.message and update.message.text else ''
    text_clean = clean_text(text)

    # ADMIN: Lokatsiyani o‘zgartirish
    if is_admin and text in ['Lokatsiyani o‘zgartirish', 'Изменить локацию', '📍 Lokatsiyani o‘zgartirish', '📍 Изменить локацию']:
        await smart_reply(update, 'Yangi lokatsiya matnini kiriting:')
        context.user_data['state'] = 'setlocation_input'
        return
    if is_admin and context.user_data.get('state') == 'setlocation_input' and text:
        data = load_data()
        data['location'] = text
        save_data(data)
        await smart_reply(update, 'Lokatsiya saqlandi!')
        context.user_data.clear()
        return
    if is_admin and context.user_data.get('state') == 'setlocation_input' and update.message and update.message.location:
        loc = update.message.location
        data = load_data()
        data['location'] = f"{loc.latitude},{loc.longitude}"
        save_data(data)
        await smart_reply(update, 'Lokatsiya saqlandi!')
        context.user_data.clear()
        return
    
    # handle_message funksiyasida, admin panel tugmasi uchun:
    if is_admin and text in ['Restoran raqamini o‘zgartirish', 'Изменить номер ресторана', '🍽 Restoran raqamini o‘zgartirish', '🍽 Изменить номер ресторана']:
        await smart_reply(update, 'Restoran egasining ismini kiriting:')
        context.user_data['state'] = 'setrestaurant_owner'
        return

    if is_admin and context.user_data.get('state') == 'setrestaurant_owner' and text:
        context.user_data['restaurant_owner'] = text
        await smart_reply(update, 'Restoran raqamini kiriting:')
        context.user_data['state'] = 'setrestaurant_number'
        return

    if is_admin and context.user_data.get('state') == 'setrestaurant_number' and text:
        data = load_data()
        data['restaurant_owner'] = context.user_data.get('restaurant_owner', '')
        data['restaurant'] = text
        save_data(data)
        await smart_reply(update, 'Restoran ma’lumotlari saqlandi!')
        context.user_data.clear()
        return

    # ADMIN: Sifat qo'shish
    if is_admin and text in ['Sifat qo‘shish', 'Добавить качество', '➕ Sifat qo‘shish', '➕ Добавить качество']:
        await smart_reply(update, 'Yangi sifat nomini kiriting:' if lang == 'uz' else 'Введите новое качество:')
        context.user_data['state'] = 'add_quality_input'
        return
    if is_admin and context.user_data.get('state') == 'add_quality_input' and text:
        data = load_data()
        qualities = data.get('qualities', [])
        if text in qualities:
            await smart_reply(update, 'Bu sifat allaqachon mavjud.' if lang == 'uz' else 'Это качество уже существует.')
        else:
            qualities.append(text)
            data['qualities'] = qualities
            save_data(data)
            await smart_reply(update, 'Sifat qo‘shildi!' if lang == 'uz' else 'Качество добавлено!')
        context.user_data.clear()
        return
    # ADMIN: Sifat o‘chirish
    if is_admin and text in ['Sifat o‘chirish', 'Удалить качество', '❌ Sifat o‘chirish', '❌ Удалить качество']:
        data = load_data()
        qualities = data.get('qualities', [])
        if not qualities:
            await smart_reply(update, 'Sifatlar yo‘q.' if lang == 'uz' else 'Качеств нет.')
            return
        kb = [[InlineKeyboardButton(q, callback_data=f'delquality_{i}')] for i, q in enumerate(qualities)]
        kb.append([InlineKeyboardButton('Orqaga' if lang == 'uz' else 'Назад', callback_data='delquality_back')])
        await smart_reply(update, 'O‘chirmoqchi bo‘lgan sifatni tanlang:' if lang == 'uz' else 'Выберите качество для удаления:', reply_markup=InlineKeyboardMarkup(kb))
        context.user_data['state'] = 'delquality_choose'
        return

    # Aloqa
    if text in ['Aloqa', 'Связь', '📞 Aloqa', '📞 Связь']:
        await smart_reply(
            update,
            'Nomeringizni kiriting:' if lang == 'uz' else 'Введите свой номер:',
            reply_markup=ReplyKeyboardMarkup(
                [[KeyboardButton('📱 Telefon raqamni yuborish', request_contact=True)]],
                resize_keyboard=True
            )
        )
        context.user_data['state'] = 'contact_phone'
        return

    # Til tanlash
    if text in ['Til', 'Язык', '🌐 Til', '🌐 Язык']:
        await smart_reply(
            update,
            'Tilni tanlang:' if lang == 'uz' else 'Выберите язык:',
            reply_markup=ReplyKeyboardMarkup([['🇺🇿 O‘zbek', '🇷🇺 Русский']], resize_keyboard=True)
        )
        context.user_data['state'] = 'choose_lang'
        return

    if context.user_data.get('state') == 'choose_lang' and text in ['🇺🇿 O‘zbek', '🇷🇺 Русский']:
        new_lang = 'uz' if text == '🇺🇿 O‘zbek' else 'ru'
        set_lang(user_id, new_lang, data)
        await smart_reply(
            update,
            'Til o‘zgardi.' if new_lang == 'uz' else 'Язык изменён.',
            reply_markup=main_menu(new_lang, is_admin)
        )
        context.user_data.clear()
        return

    # ADMIN PANEL
    if is_admin and ('adminpanelgakirish' in text_clean or 'войтивадинпанель' in text_clean):
        await handle_menu(update, context)
        return
    if is_admin and text.strip() in ['Orqaga', 'Назад']:
        await smart_reply(update, 'Asosiy menyu' if lang == 'uz' else 'Главное меню', reply_markup=main_menu(lang, is_admin))
        context.user_data.clear()
        return
    if is_admin and text in ['Xonalar ro‘yxati', 'Список номеров', '🏨 Xonalar ro‘yxati', '🏨 Список номеров']:
        if not data['rooms']:
            await smart_reply(update, 'Xonalar yo‘q.')
            return
        msg = ''
        for r in data['rooms']:
            msg += (
                f"🏨 <b>{r['name']}</b> (ID: <code>{r['id']}</code>)\n"
                f"🏷️ Sifat: <b>{r['quality']}</b>\n"
                f"💵 Narx: <b>{r['price']}</b>\n"
                f"👥 Odamlar soni: <b>{r.get('capacity', 7)}</b>\n"
                f"📝 {r['desc']}\n"
                "----------------------\n"
            )
        await smart_reply(update, msg, parse_mode='HTML')
        return
    if is_admin and text in ['Bronlar ro‘yxati', 'Список броней', '📋 Bronlar ro‘yxati', '📋 Список броней']:
        await bookings(update, context)
        return
    if is_admin and text in ['Xona qo‘shish', 'Добавить номер', '➕ Xona qo‘shish', '➕ Добавить номер']:
        await smart_reply(update, 'Xona nomini kiriting:')
        context.user_data['state'] = 'addroom_name'
        return
    if context.user_data.get('state') == 'addroom_name' and text:
        context.user_data['addroom_name'] = text
        await smart_reply(update, 'Sifatini tanlang:' if lang == 'uz' else 'Выберите категорию:', reply_markup=room_quality_menu(lang))
        context.user_data['state'] = 'addroom_quality'
        return
    if is_admin and text in ['Xona o‘chirish', 'Удалить номер', '❌ Xona o‘chirish', '❌ Удалить номер']:
        if not data['rooms']:
            await smart_reply(update, 'Xonalar yo‘q.')
            return
        await smart_reply(update,
            'O‘chirmoqchi bo‘lgan xonani tanlang:' if lang == 'uz' else 'Выберите номер для удаления:',
            reply_markup=room_delete_menu(data)
        )
        context.user_data['state'] = 'delroom_choose'
        return
    if is_admin and text in ['Bronni o‘chirish', 'Удалить бронь', '❌ Bronni o‘chirish', '❌ Удалить бронь']:
        data = load_data()
        if not data['bookings']:
            await smart_reply(update, 'Bronlar yo‘q.')
            return
        await smart_reply(update, 'O‘chirmoqchi bo‘lgan bronni tanlang:', reply_markup=booking_delete_menu(data, lang))
        context.user_data['state'] = 'delbooking_choose'
        return
    if is_admin and text in ['Biz haqimizda o‘zgartirish', 'Изменить о нас', 'ℹ️ Biz haqimizda o‘zgartirish', 'ℹ️ Изменить о нас']:
        await smart_reply(update, 'Qaysi til uchun o‘zgartirmoqchisiz?', reply_markup=ReplyKeyboardMarkup([
            ['🇺🇿 O‘zbek', '🇷🇺 Русский'],
            ['Orqaga']
        ], resize_keyboard=True))
        context.user_data['state'] = 'setabout_choose_lang'
        return
    # ADMIN: Biz haqimizda o‘zgartirish (til tanlash bosqichi)
    if is_admin and context.user_data.get('state') == 'setabout_choose_lang' and text in ['🇺🇿 O‘zbek', '🇷🇺 Русский']:
        if context.user_data.get('state') != 'setabout_choose_lang':
            # Faqat til tanlash bosqichida ishlasin
            return
        lang_code = 'uz' if text == '🇺🇿 O‘zbek' else 'ru'
        context.user_data['setabout_lang'] = lang_code
        await smart_reply(update, f'Iltimos, "Biz haqimizda" matnini yozing ({"o‘zbek" if lang_code=="uz" else "rus"} tilida):')
        context.user_data['state'] = 'setabout_input'
        return
    # ADMIN: Biz haqimizda o‘zgartirish (matn kiritish bosqichi)
    if is_admin and context.user_data.get('state') == 'setabout_input' and text:
        if text in ['🇺🇿 O‘zbek', '🇷🇺 Русский']:
            # Matn o‘rniga til tugmasi bosilsa, javob bermasin
            return
        lang_code = context.user_data.get('setabout_lang')
        data = load_data()
        data['about'][lang_code] = text
        save_data(data)
        await smart_reply(update, 'Saqlangan!')
        # Yana til tanlashga qaytadi
        await smart_reply(update, 'Qaysi til uchun o‘zgartirmoqchisiz?', reply_markup=ReplyKeyboardMarkup([
            ['🇺🇿 O‘zbek', '🇷🇺 Русский'],
            ['Orqaga']
        ], resize_keyboard=True))
        context.user_data['state'] = 'setabout_choose_lang'
        return
    # ADDROOM: narx, odamlar soni, tavsif, rasm URL/photo matn orqali
    if context.user_data.get('state') == 'addroom_price' and text:
        if not text.isdigit():
            await smart_reply(update, "Iltimos, narxni faqat raqam bilan kiriting (masalan: 250000)")
            return
        context.user_data['addroom_price'] = text
        await smart_reply(update, "Odamlar sonini kiriting (quantity):")
        context.user_data['state'] = 'addroom_capacity'
        return
    if context.user_data.get('state') == 'addroom_capacity' and text:
        if not text.isdigit() or int(text) < 1:
            await smart_reply(update, "Iltimos, odamlar sonini raqam bilan kiriting (masalan: 7)")
            return
        context.user_data['addroom_capacity'] = int(text)
        await smart_reply(update, 'Tavsifini kiriting:')
        context.user_data['state'] = 'addroom_desc'
        return
    if context.user_data.get('state') == 'addroom_desc' and text:
        context.user_data['addroom_desc'] = text
        await smart_reply(update, 'Rasm URL yoki rasm yuboring:')
        context.user_data['state'] = 'addroom_img'
        return
    if context.user_data.get('state') == 'addroom_img':
        # Agar admin rasm yuborsa (photo)
        if update.message and update.message.photo:
            file_id = update.message.photo[-1].file_id
            imgs = context.user_data.get('addroom_imgs', [])
            imgs.append(file_id)
            context.user_data['addroom_imgs'] = imgs
            await smart_reply(update, 'Yana rasm yuboring yoki "stop" deb yozing.')
            return
        # Agar admin 'stop' deb yozsa
        if update.message and update.message.text and update.message.text.strip().lower() == 'stop':
            data = load_data()
            room_id = max([r['id'] for r in data['rooms']], default=0) + 1
            data['rooms'].append({
                'id': room_id,
                'name': context.user_data['addroom_name'],
                'quality': context.user_data['addroom_quality'],
                'price': context.user_data['addroom_price'],
                'desc': context.user_data['addroom_desc'],
                'imgs': context.user_data.get('addroom_imgs', []),
                'capacity': context.user_data.get('addroom_capacity', 7)
            })
            save_data(data)
            await smart_reply(update, 'Xona va rasmlar qo‘shildi!')
            context.user_data.clear()
            return
        # Agar admin URL yuborsa (text, lekin 'stop' emas)
        if update.message and update.message.text:
            url = update.message.text.strip()
            imgs = context.user_data.get('addroom_imgs', [])
            imgs.append(url)
            context.user_data['addroom_imgs'] = imgs
            await smart_reply(update, 'Yana rasm yuboring yoki "stop" deb yozing.')
            return
    # USER XONALAR
    if text_clean in [clean_text('Xonalar'), clean_text('Номера')]:
        await smart_reply(
            update,
            'Xona turini tanlang:' if lang == 'uz' else 'Выберите категорию номера:',
            reply_markup=room_quality_menu(lang)
        )
        context.user_data['state'] = 'choose_room_quality'
        return
    # BOOKING PHONE
    if context.user_data.get('state') == 'booking_phone' and update.message and update.message.contact:
        context.user_data['booking_phone'] = update.message.contact.phone_number
        await smart_reply(update, 'Ism-familyangizni kiriting:' if lang == 'uz' else 'Введите имя и фамилию:', reply_markup=ReplyKeyboardRemove())
        context.user_data['state'] = 'booking_name'
        return
    
    # BOOKING NAME
    if context.user_data.get('state') == 'booking_name' and text:
        context.user_data['booking_name'] = text
        await smart_reply(update, 'Odamlar sonini kiriting:' if lang == 'uz' else 'Введите количество человек:')
        context.user_data['state'] = 'booking_people'
        return
    
    if context.user_data.get('state') == 'awaiting_payment_check' and (update.message.photo or update.message.document):
        booking_idx = context.user_data.get('last_booking_id')  # <-- BU QATORNI QO‘YING!
        data = load_data()
        booking = data['bookings'][booking_idx] if (booking_idx is not None and 0 <= booking_idx < len(data['bookings'])) else None
        
        if booking:
            room = next((r for r in data['rooms'] if r['id'] == booking['room_id']), None)
            await context.bot.send_message(
                ADMIN_ID,
                (
                    f"🆕 <b>Yangi bron!</b>\n"
                    f"👤 <b>Foydalanuvchi:</b> @{booking['username']}\n"
                    f"📞 <b>Telefon:</b> {booking['phone']}\n"
                    f"🏨 <b>Xona:</b> {room['name'] if room else ''} (ID: <code>{booking['room_id']}</code>)\n"
                    f"🏷️ <b>Sifat:</b> {booking['quality']}\n"
                    f"👥 <b>Odamlar soni:</b> {booking['people']}\n"
                    f"📅 <b>Sana:</b> {booking['from']} ➡️ {booking['to']}\n"
                    f"📝 <b>Ism-familya:</b> {booking['name']}"
                ),
                parse_mode='HTML'
            )
        # --- YANGI BRON XABARI TUGADI ---

        caption = (
            f"🧾 Yangi to‘lov cheki!\n"
            f"👤 <b>{booking['name']}</b>\n"
            f"📞 {booking['phone']}\n"
            f"🏨 {room['name']}\n"
            f"📅 {booking['from']} ➡️ {booking['to']}\n"
            f"Ushbu to‘lovni qabul qilasizmi?"
        ) if booking else "Yangi to‘lov cheki. Qabul qilasizmi?"

        kb = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Ha", callback_data=f"accept_payment_{booking_idx}"),
                InlineKeyboardButton("❌ Yo‘q", callback_data=f"reject_payment_{booking_idx}")
            ]
        ])

        if update.message.photo:
            await context.bot.send_photo(
                ADMIN_ID,
                photo=update.message.photo[-1].file_id,
                caption=caption,
                parse_mode='HTML',
                reply_markup=kb
            )
        elif update.message.document:
            await context.bot.send_document(
                ADMIN_ID,
                document=update.message.document.file_id,
                caption=caption,
                parse_mode='HTML',
                reply_markup=kb
            )
        await smart_reply(update, "Chek adminga yuborildi. Tez orada javob olasiz.")
        context.user_data.clear()
        return
    # BOOKING PEOPLE
    if context.user_data.get('state') == 'booking_people':
        if text.isdigit():
            people = int(text)
            # Tanlangan xonaning sig‘imini aniqlash
            room_id = context.user_data.get('room_id')
            data = load_data()
            room = next((r for r in data['rooms'] if r['id'] == room_id), None)
            capacity = room.get('capacity', 7) if room else 7
            if people > capacity:
                await smart_reply(
                    update,
                    f"Iltimos, to'g'ri kiriting. Bu xona uchun maksimal sig‘im: {capacity} kishi." if lang == 'uz'
                    else f"Пожалуйста, введите правильное количество. Максимальная вместимость для этой комнаты: {capacity} человек."
                )
                return
            context.user_data['booking_people'] = people
            await smart_reply(
                update,
                'Qachondan boshlab yashamoqchisiz? (Sanani tanlang)' if lang == 'uz' else 'С какой даты хотите заселиться?',
                reply_markup=month_menu(lang, prefix='month_')
            )
            context.user_data['state'] = 'choose_month'
        else:
            # Sig‘imni ham ko‘rsatamiz
            room_id = context.user_data.get('room_id')
            data = load_data()
            room = next((r for r in data['rooms'] if r['id'] == room_id), None)
            capacity = room.get('capacity', 7) if room else 7
            await smart_reply(
                update,
                f"Iltimos, odamlar sonini raqam bilan kiriting (maksimal: {capacity})." if lang == 'uz'
                else f"Пожалуйста, введите количество людей цифрами (максимум: {capacity})."
            )
        return

    # BOOKING QUALITY
    if context.user_data.get('state') == 'booking_quality':
        # Bu bosqich endi ishlatilmaydi
        return
    # CONTACT REQUEST
    if update.message and update.message.contact:
        if context.user_data.get('state') == 'contact_phone':
            phone = update.message.contact.phone_number
            name = update.effective_user.full_name
            context.user_data['contact_phone'] = phone
            context.user_data['contact_name'] = name
            await smart_reply(update, (
                'Raqamingiz qabul qilindi! Endi savolingizni yozing:' if lang == 'uz' else 'Ваш номер принят! Теперь напишите свой вопрос:'
            ), reply_markup=ReplyKeyboardRemove())
            context.user_data['state'] = 'contact_question'
            return

    # CONTACT QUESTION
    if context.user_data.get('state') == 'contact_question' and text:
        phone = context.user_data.get('contact_phone')
        name = context.user_data.get('contact_name')
        question = text
        await smart_reply(update, (
            'Savolingiz yuborildi!' if lang == 'uz' else 'Ваш вопрос отправлен!'
        ), reply_markup=main_menu(lang, is_admin=(user_id == ADMIN_ID)))
        await context.bot.send_message(
            ADMIN_ID,
            f"📞 Yangi aloqa so'rovi!\n👤 {name}\n📱 {phone}\n❓ Savol: {question}"
        )
        context.user_data.clear()
        return
    # Lokatsiya
    if text in ['Lokatsiya', 'Локация', '📍 Lokatsiya', '📍 Локация']:
        loc = data['location']
        if loc:
            # Agar location lat,long ko‘rinishida bo‘lsa, Telegram location sifatida yubor
            if ',' in loc and all(part.replace('.', '', 1).replace('-', '', 1).isdigit() for part in loc.split(',')):
                lat, lon = loc.split(',')
                try:
                    await update.message.reply_location(latitude=float(lat), longitude=float(lon))
                except Exception:
                    maps_url = f'https://maps.google.com/?q={lat},{lon}'
                    await smart_reply(update, f'<a href="{maps_url}">Lokatsiya (Google xarita)</a>', parse_mode='HTML')
            else:
                await smart_reply(update, loc)
        else:
            await smart_reply(update, 'Lokatsiya mavjud emas.' if lang == 'uz' else 'Локация не добавлена.')
        return

    # Biz haqimizda
    if text in ['Biz haqimizda', 'О нас', 'ℹ️ Biz haqimizda', 'ℹ️ О нас']:
        about = data['about'][lang]
        if lang == 'uz':
            header = '<b>🏨 Shodlik Haqida</b>'
            default_about = 'Lorem ipsum dolor sit amet, Shodlik mehmonxonasi haqida qisqacha maʼlumot.'
        else:
            header = '<b>🏨 О Shodlik</b>'
            default_about = 'Lorem ipsum dolor sit amet, краткая информация о гостинице Shodlik.'
        msg = f"{header}\n\n{about if about else default_about}"
        await smart_reply(update, msg, parse_mode='HTML')
        return

    # Restoran
    if text in ['Restoran', 'Ресторан', '🍽 Restoran', '🍽 Ресторан']:
        rest = data['restaurant']
        rest_name = data.get('restaurant_owner', 'Obid Dabba')
        rest_number = rest if rest else '+9989999999'
        if lang == 'uz':
            msg = (
                "<b>🍽 Restoran buyurtmasi</b>\n"
                "<i>Agar telefon qilib zakaz qilsangiz, zakazingiz olib kelib beriladi.</i>\n\n"
                f"<b>📞 Nomer:</b> <code>{rest_number}</code>\n"
                f"<b>👤 Ism:</b> {rest_name}"
            )
        else:
            msg = (
                "<b>🍽 Заказ в ресторан</b>\n"
                "<i>Если вы позвоните и закажете, ваш заказ будет доставлен.</i>\n\n"
                f"<b>📞 Номер:</b> <code>{rest_number}</code>\n"
                f"<b>👤 Имя:</b> {rest_name}"
            )
        await smart_reply(update, msg, parse_mode='HTML')
        return

    # Til tanlash
    if text in ['Til', 'Язык']:
        await smart_reply(
            update,
            'Tilni tanlang:' if lang == 'uz' else 'Выберите язык:',
            reply_markup=ReplyKeyboardMarkup([['🇺🇿 O‘zbek', '🇷🇺 Русский']], resize_keyboard=True)
        )
        context.user_data['state'] = 'choose_lang'
        return

    if text in ['🇺🇿 O‘zbek', '🇷🇺 Русский']:
        new_lang = 'uz' if text == '🇺🇿 O‘zbek' else 'ru'
        set_lang(user_id, new_lang, data)
        await smart_reply(
            update,
            'Til o‘zgardi.' if new_lang == 'uz' else 'Язык изменён.',
            reply_markup=main_menu(new_lang, is_admin)
        )
        context.user_data.clear()
        return

    if context.user_data.get('state'):
        await smart_reply(update,
            "Noto'g'ri buyruq." if lang == 'uz' else 'Неверная команда.'
        )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    user_id = update.effective_user.id
    lang = get_lang(user_id, data)
    query = update.callback_query
    await query.answer()
    # Foydalanuvchi bron qilish jarayoni
    if query.data.startswith('room_quality_'):
        quality = query.data.split('_')[-1]
        # AGAR ADMIN YANGI XONA QO‘SHAYOTGAN BO‘LSA
        if context.user_data.get('state') == 'addroom_quality':
            context.user_data['addroom_quality'] = quality
            await query.message.reply_text('Narxini kiriting:')
            context.user_data['state'] = 'addroom_price'
            return
        # Foydalanuvchi uchun xonalar ro‘yxati
        rooms = [r for r in data['rooms'] if r['quality'] == quality]
        if not rooms:
            await query.edit_message_text('Xonalar mavjud emas.' if lang == 'uz' else 'Номера отсутствуют.')
            return
        kb = [[InlineKeyboardButton(f"{r['name']} ({r['capacity']}ta odam)", callback_data=f"user_room_{r['id']}")] for r in rooms]
        kb.append([InlineKeyboardButton('Orqaga' if lang == 'uz' else 'Назад', callback_data='user_back')])
        await query.edit_message_text(
            'Xonani tanlang:' if lang == 'uz' else 'Выберите номер:',
            reply_markup=InlineKeyboardMarkup(kb)
        )
        context.user_data['state'] = 'choose_room'
        context.user_data['quality'] = quality
        return
        # Aks holda, oddiy xonalar ro'yxati chiqsin (oldingi kod)
        rooms = [r for r in data['rooms'] if r['quality'] == quality]
        if not rooms:
            await query.edit_message_text('Xonalar mavjud emas.' if lang == 'uz' else 'Номера отсутствуют.')
            return
        kb = [[InlineKeyboardButton(f"{r['name']} ({r['capacity']}ta odam)", callback_data=f"user_room_{r['id']}")] for r in rooms]
        kb.append([InlineKeyboardButton('Orqaga' if lang == 'uz' else 'Назад', callback_data='user_back')])
        await query.edit_message_text(
            'Xonani tanlang:' if lang == 'uz' else 'Выберите номер:',
            reply_markup=InlineKeyboardMarkup(kb)
        )
        context.user_data['state'] = 'choose_room'
        context.user_data['quality'] = quality
        return
    if query.data == 'user_quality_back':
        await smart_reply(update, 'Sifatni tanlang:' if lang == 'uz' else 'Выберите категорию:', reply_markup=room_quality_menu(lang))
        context.user_data['state'] = 'choose_room_quality'
        return
    if query.data.startswith('user_book_'):
        room_id = int(query.data.split('_')[-1])
        context.user_data['room_id'] = room_id
        context.user_data['state'] = 'booking_phone'
        await smart_reply(
            update,
            'Telefon raqamingizni yuboring:' if lang == 'uz' else 'Отправьте свой номер телефона:',
            reply_markup=ReplyKeyboardMarkup(
                [[KeyboardButton('📱 Telefon raqamni yuborish', request_contact=True)]],
                resize_keyboard=True
            )
        )
        return
    if query.data.startswith('month_'):
        month = int(query.data.split('_')[-1])
        year = datetime.datetime.now().year
        context.user_data['month'] = month
        context.user_data['year'] = year
        room_id = context.user_data.get('room_id')
        if not room_id:
            await query.edit_message_text('Xona tanlanmagan.')
            return
        data = load_data()
        booked_days = get_booked_days_for_month(data['bookings'], room_id, year, month)
        all_days = set(range(1, (datetime.date(year, month % 12 + 1, 1) - datetime.timedelta(days=1)).day + 1))
        free_days = all_days - booked_days
        import random  # Fayl boshida borligiga ishonch hosil qiling

        if not free_days:
            suffix = chr(8203 + random.randint(0, 10))  # Yangi qator
            await query.edit_message_text(
                ('Bo‘sh kunlar yo‘q, boshqa oy tanlang.' if lang == 'uz' else 'Свободных дат нет, выберите другой месяц.') + suffix,
                reply_markup=month_menu(lang, prefix='month_')
            )
            context.user_data['state'] = 'choose_month'
            return

        suffix = chr(8203 + random.randint(0, 10))  # Yangi qator
        await query.edit_message_text(
            ('Bo‘sh kunlar:' if lang == 'uz' else 'Свободные даты:') + suffix,
            reply_markup=days_menu(year, month, prefix='day_', booked_days=booked_days, lang=lang)
        )
        context.user_data['state'] = 'choose_day'
        return
    if query.data.startswith('monthto_'):
        month_to = int(query.data.split('_')[-1])
        year_to = datetime.datetime.now().year
        context.user_data['month_to'] = month_to
        context.user_data['year_to'] = year_to
        # Avval tanlangan oy
        month_from = context.user_data.get('month')
        if month_from and month_to < month_from:
            await query.edit_message_text(
                'Bu xato oy. Boshqatan tanlang.' if lang == 'uz' else 'Это неверный месяц. Пожалуйста, выберите снова.',
                reply_markup=month_menu(lang, prefix='monthto_')
            )
            context.user_data.pop('month_to', None)
            context.user_data.pop('year_to', None)
            context.user_data['state'] = 'choose_month_to'
            return
        room_id = context.user_data.get('room_id')
        if not room_id:
            await query.edit_message_text('Xona tanlanmagan.')
            return
        data = load_data()
        booked_days = get_booked_days_for_month(data['bookings'], room_id, year_to, month_to)
        all_days = set(range(1, (datetime.date(year_to, month_to % 12 + 1, 1) - datetime.timedelta(days=1)).day + 1))
        free_days = all_days - booked_days
        if not free_days:
            await query.edit_message_text(
                'Bo‘sh kunlar yo‘q, boshqa oy tanlang.' if lang == 'uz' else 'Свободных дат нет, выберите другой месяц.',
                reply_markup=month_menu(lang, prefix='monthto_')
            )
            context.user_data['state'] = 'choose_month_to'
            return
        await query.edit_message_text(
            'Bo‘sh kunlar:' if lang == 'uz' else 'Свободные даты:',
            reply_markup=days_menu(year_to, month_to, prefix='dayto_', booked_days=booked_days, lang=lang)
        )
        context.user_data['state'] = 'choose_day_to'
        return
    if query.data.startswith('day_'):
        if query.data == 'day_back':
            context.user_data.pop('month', None)
            context.user_data.pop('year', None)
            await query.edit_message_text(
                'Oy tanlang:' if lang == 'uz' else 'Выберите месяц:',
                reply_markup=month_menu(lang, prefix='month_')
            )
            context.user_data['state'] = 'choose_month'
            return
        day = int(query.data.split('_')[-1])
        context.user_data['day'] = day
        await query.edit_message_text(
            'Qaysi sanagacha turmoqchisiz?' if lang == 'uz' else 'До какой даты будете проживать?',
            reply_markup=month_menu(lang, prefix='monthto_')
        )
        context.user_data['state'] = 'choose_month_to'
        return
    if query.data.startswith('dayto_'):
        if query.data == 'dayto_back':
            context.user_data.pop('month_to', None)
            context.user_data.pop('year_to', None)
            await query.edit_message_text(
                'Oy tanlang:' if lang == 'uz' else 'Выберите месяц:',
                reply_markup=month_menu(lang, prefix='monthto_')
            )
            context.user_data['state'] = 'choose_month_to'
            return
        day = int(query.data.split('_')[-1])
        context.user_data['day_to'] = day
        if not all(k in context.user_data for k in ['month', 'day', 'month_to', 'room_id', 'year', 'year_to']):
            await query.edit_message_text('Maʼlumot yetarli emas.')
            return
        from_date = datetime.date(context.user_data['year'], context.user_data['month'], context.user_data['day'])
        to_date = datetime.date(context.user_data['year_to'], context.user_data['month_to'], day)
        room_id = context.user_data['room_id']
        data = load_data()
        conflict = check_booking_conflict(data['bookings'], room_id, from_date, to_date)
        ...
        room = next((r for r in data['rooms'] if r['id'] == room_id), None)
        quality = room['quality'] if room else ''
        # --- YANGI QISM ---
        try:
            price_per_day = int(room['price'])
        except Exception:
            price_per_day = 0
        days_count = (to_date - from_date).days + 1
        total_price = price_per_day * days_count
        # --- YANGI QISM TUGADI ---
        booking = {
            'user_id': user_id,
            'username': query.from_user.username,
            'room_id': room_id,
            'quality': quality,
            'phone': context.user_data['booking_phone'],
            'name': context.user_data['booking_name'],
            'people': context.user_data['booking_people'],
            'from': from_date.strftime('%Y-%m-%d'),
            'to': to_date.strftime('%Y-%m-%d')
        }
        data['bookings'].append(booking)
        save_data(data)
        await context.bot.send_message(
            user_id,
            (
                'Bron qabul qilindi!\n\n'
                f"Xona narxi: <b>{price_per_day}</b> × {days_count} kun = <b>{total_price} So'm</b>\n"
                'Iltimos, quyidagi karta raqamiga to‘lovni amalga oshiring:\n'
                '<b>8600 1234 5678 9012</b>\n\n'
                'To‘lov cheki (screenshot yoki rasm)ni shu yerga yuboring.'
            ),
            parse_mode='HTML'
        )
        lang = get_lang(user_id, data)
        is_admin = (user_id == ADMIN_ID)
        await context.bot.send_message(
            user_id,
            'Asosiy menyu' if lang == 'uz' else 'Главное меню',
            reply_markup=main_menu(lang, is_admin)
        )
        context.user_data.clear()
        context.user_data['state'] = 'awaiting_payment_check'
        context.user_data['last_booking_id'] = len(data['bookings']) - 1
    # ROOM DELETE: Step 1 - ask for confirmation
    if query.data.startswith('delroom_'):
        if query.data == 'delroom_back':
            # Back to admin panel menu
            await query.edit_message_text('Admin paneli:' if lang == 'uz' else 'Админ-панель:', reply_markup=admin_panel_menu(lang))
            context.user_data['state'] = 'admin_panel'
            return
        room_id = int(query.data.split('_')[-1])
        room = next((r for r in data['rooms'] if r['id'] == room_id), None)
        if not room:
            await query.edit_message_text('Xona topilmadi.' if lang == 'uz' else 'Номер не найден.')
            return
        # Bron tekshirish
        bron_bor = any(b['room_id'] == room_id for b in data['bookings'])
        if bron_bor:
            msg = f"<b>Diqqat!</b> Bu xona bron qilingan. Baribir o‘chirmoqchimisiz?\n<b>{room['name']}</b> (ID: <code>{room_id}</code>)" if lang == 'uz' else f"<b>Внимание!</b> Этот номер забронирован. Всё равно удалить?\n<b>{room['name']}</b> (ID: <code>{room_id}</code>)"
        else:
            msg = f"Shu xonani o‘chirmoqchimisiz?\n<b>{room['name']}</b> (ID: <code>{room_id}</code>)" if lang == 'uz' else f"Вы уверены, что хотите удалить этот номер?\n<b>{room['name']}</b> (ID: <code>{room_id}</code>)"
        await query.edit_message_text(msg, parse_mode='HTML', reply_markup=room_delete_confirm_menu(room_id, lang))
        context.user_data['state'] = 'delroom_confirm'
        context.user_data['delroom_id'] = room_id
        return
    # ROOM DELETE: Step 2 - handle confirmation
    if query.data.startswith('confirm_delroom_yes_'):
        room_id = int(query.data.split('_')[-1])
        data['rooms'] = [r for r in data['rooms'] if r['id'] != room_id]
        save_data(data)
        await query.edit_message_text('Xona o‘chirildi!' if lang == 'uz' else 'Номер удалён!')
        context.user_data.clear()
        return
    if query.data.startswith('confirm_delroom_no_'):
        # Back to room delete menu
        await query.edit_message_text(
            'O‘chirmoqchi bo‘lgan xonani tanlang:' if lang == 'uz' else 'Выберите номер для удаления:',
            reply_markup=room_delete_menu(data)
        )
        context.user_data['state'] = 'delroom_choose'
        return
    if query.data == 'delroom_back':
        # Back to admin panel menu
        await query.edit_message_text('Admin paneli:' if lang == 'uz' else 'Админ-панель:', reply_markup=admin_panel_menu(lang))
        context.user_data['state'] = 'admin_panel'
        return
    # ADMIN: Sifat o‘chirish callback
    if query.data == 'delquality_back':
        await query.edit_message_text('Admin paneli:' if lang == 'uz' else 'Админ-панель:', reply_markup=admin_panel_menu(lang))
        context.user_data['state'] = 'admin_panel'
        return
        
    if query.data.startswith('delquality_'):
        idx = int(query.data.split('_')[-1])
        data = load_data()
        qualities = data.get('qualities', [])
        if idx < 0 or idx >= len(qualities):
            await query.edit_message_text('Sifat topilmadi.' if lang == 'uz' else 'Качество не найдено.')
            return
        del_quality = qualities.pop(idx)
        data['qualities'] = qualities
        save_data(data)
        await query.edit_message_text(f'Sifat o‘chirildi: {del_quality}' if lang == 'uz' else f'Качество удалено: {del_quality}')
        context.user_data.clear()
        return
    
    # ... boshqa admin va foydalanuvchi callbacklar ...
    elif query.data.startswith('room_quality_'):
        quality = query.data.split('_')[-1]
        rooms = [r for r in data['rooms'] if r['quality'] == quality]
        if not rooms:
            await query.edit_message_text('Xonalar mavjud emas.' if lang == 'uz' else 'Номера отсутствуют.')
            return
        kb = [[InlineKeyboardButton(f"{r['name']}", callback_data=f"room_{r['id']}")] for r in rooms]
        await query.edit_message_text(
            'Xonani tanlang:' if lang == 'uz' else 'Выберите номер:',
            reply_markup=InlineKeyboardMarkup(kb)
        )
        context.user_data['state'] = 'choose_room'
        context.user_data['quality'] = quality
    elif query.data.startswith('user_room_'):
        room_id = int(query.data.split('_')[-1])
        room = next((r for r in data['rooms'] if r['id'] == room_id), None)
        if room:
            imgs = room.get('imgs') or ([room.get('img')] if room.get('img') else [])
            if imgs and len(imgs) > 1:
                media = []
                for i, img in enumerate(imgs):
                    if i == 0:
                        media.append(InputMediaPhoto(
                            img,
                            caption=(
                                f"🏨 <b>{room['name']}</b>\n"
                                f"🏷️ Sifat: <b>{room['quality']}</b>\n"
                                f"💵 Narx: <b>{room['price']} So'm</b>\n"
                                f"📝 {room['desc']}"
                            ),
                            parse_mode='HTML'
                        ))
                    else:
                        media.append(InputMediaPhoto(img))
                await context.bot.send_media_group(
                    chat_id=user_id,
                    media=media
                )
                await context.bot.send_message(
                    chat_id=user_id,
                    text='Xona tafsilotlari',
                    reply_markup=user_room_detail_menu(room_id, lang)
                )
            elif imgs:
                await context.bot.send_photo(
                    chat_id=user_id,
                    photo=imgs[0],
                    caption=(
                        f"🏨 <b>{room['name']}</b>\n"
                        f"🏷️ Sifat: <b>{room['quality']}</b>\n"
                        f"💵 Narx: <b>{room['price']} So'm</b>\n"
                        f"📝 {room['desc']}"
                    ),
                    parse_mode='HTML',
                    reply_markup=user_room_detail_menu(room_id, lang)
                )
            else:
                await smart_reply(update, 'Rasm mavjud emas.')
            context.user_data['room_id'] = room_id
            context.user_data['state'] = 'choose_room_detail'
            return
    elif query.data.startswith('room_'):
        room_id = int(query.data.split('_')[-1])
        context.user_data['room_id'] = room_id
        room = next((r for r in data['rooms'] if r['id'] == room_id), None)
        if room:
            await context.bot.send_photo(
                chat_id=user_id,
                photo=room['img'],
                caption=f"{room['name']}\n{room['desc']}\nNarxi: {room['price']}" if lang == 'uz' else f"{room['name']}\n{room['desc']}\nЦена: {room['price']}"
            )
        await smart_reply(
            update,
            'Telefon raqamingizni yuboring:' if lang == 'uz' else 'Отправьте свой номер телефона:',
            reply_markup=ReplyKeyboardMarkup(
                [[KeyboardButton('📱 Telefon raqamni yuborish', request_contact=True)]],
                resize_keyboard=True
            )
        )
        context.user_data['state'] = 'booking_phone'
    elif query.data.startswith('addroom_quality_'):
        context.user_data['addroom_quality'] = query.data.split('_')[-1]
        await query.message.reply_text('Narxini kiriting:')
        context.user_data['state'] = 'addroom_price'
        return
    elif query.data.startswith('addroom_price'):
        context.user_data['addroom_price'] = query.data
        await query.message.reply_text('Odamlar sonini kiriting (quantity):')
        context.user_data['state'] = 'addroom_capacity'
        return
    elif query.data.startswith('addroom_capacity'):
        if not query.data.isdigit() or int(query.data) < 1:
            await query.message.reply_text("Iltimos, odamlar sonini raqam bilan kiriting (masalan: 7)")
            return
        context.user_data['addroom_capacity'] = int(query.data)
        await query.message.reply_text('Tavsifini kiriting:')
        context.user_data['state'] = 'addroom_desc'
        return
    elif query.data.startswith('addroom_desc'):
        context.user_data['addroom_desc'] = query.data
        await query.message.reply_text('Rasm URL yoki rasm yuboring:')
        context.user_data['state'] = 'addroom_img'
        return
    elif query.data.startswith('addroom_img'):
        if update.message.photo:
            file_id = update.message.photo[-1].file_id
            url = file_id
        else:
            url = query.data
        data = load_data()
        room_id = max([r['id'] for r in data['rooms']], default=0) + 1
        data['rooms'].append({
            'id': room_id,
            'name': context.user_data['addroom_name'],
            'quality': context.user_data['addroom_quality'],
            'price': context.user_data['addroom_price'],
            'desc': context.user_data['addroom_desc'],
            'img': url,
            'capacity': context.user_data.get('addroom_capacity', 7)  # default 7
        })
        save_data(data)
        await query.edit_message_text('Xona qo‘shildi!')
        context.user_data.clear()
        return
    if query.data == 'user_back':
        # Foydalanuvchini category tanlashga qaytarish
        await smart_reply(
            update,
            'Xona turini tanlang:' if lang == 'uz' else 'Выберите категорию номера:',
            reply_markup=room_quality_menu(lang)
        )
        context.user_data['state'] = 'choose_room_quality'
        return
    
    if query.data.startswith('accept_payment_'):
        idx = int(query.data.split('_')[-1])
        data = load_data()
        booking = data['bookings'][idx] if idx < len(data['bookings']) else None
        if booking:
            user_id = booking['user_id']
            await context.bot.send_message(user_id, "To‘lovingiz qabul qilindi va bron tasdiqlandi! Rahmat.")
        await query.edit_message_caption(caption="✅ To‘lov qabul qilindi va bron tasdiqlandi!", reply_markup=None)
        return

    if query.data.startswith('reject_payment_'):
        idx = int(query.data.split('_')[-1])
        data = load_data()
        booking = data['bookings'][idx] if idx < len(data['bookings']) else None
        if booking:
            user_id = booking['user_id']
            await context.bot.send_message(user_id, "Kechirasiz, to‘lov chekingiz qabul qilinmadi. Iltimos, qayta urinib ko‘ring.")
            # Bronni o‘chirish
            del data['bookings'][idx]
            save_data(data)
        await query.edit_message_caption(caption="❌ To‘lov cheki rad etildi.", reply_markup=None)
        return
    elif query.data.startswith('delbooking_'):
        idx = int(query.data.split('_')[-1])
        data = load_data()
        if idx < 0 or idx >= len(data['bookings']):
            await query.edit_message_text('Bron topilmadi.')
            return
        b = data['bookings'][idx]
        room = next((r for r in data['rooms'] if r['id'] == b['room_id']), None)
        msg = f"Shu bronni o‘chirmoqchimisiz?\nFoydalanuvchi: <b>@{b['username']}</b>\nXona: <b>{room['name'] if room else 'Noma’lum'}</b>\nSana: <b>{b['from']} ➡️ {b['to']}</b>" if lang == 'uz' else f"Удалить эту бронь?\nПользователь: <b>{b['username']}</b>\nНомер: <b>{room['name'] if room else 'Неизвестно'}</b>\nДата: <b>{b['from']} ➡️ {b['to']}</b>"
        await query.edit_message_text(msg, parse_mode='HTML', reply_markup=booking_delete_confirm_menu(idx, lang))
        context.user_data['state'] = 'delbooking_confirm'
        context.user_data['delbooking_idx'] = idx
        return
    elif query.data.startswith('confirm_delbooking_yes_'):
        idx = int(query.data.split('_')[-1])
        data = load_data()
        if idx < 0 or idx >= len(data['bookings']):
            await query.edit_message_text('Bron topilmadi.')
            return
        booking = data['bookings'][idx]
        user_id = booking.get('user_id')
        del data['bookings'][idx]
        save_data(data)
        await query.edit_message_text('Bron o‘chirildi!' if lang == 'uz' else 'Бронь удалена!')
        if user_id:
            try:
                await context.bot.send_message(user_id, 'Sizning broningiz o‘chirildi.')
            except Exception:
                pass
        context.user_data.clear()
        return
    elif query.data.startswith('confirm_delbooking_no_'):
        data = load_data()
        await query.edit_message_text('O‘chirmoqchi bo‘lgan bronni tanlang:', reply_markup=booking_delete_menu(data, lang))
        context.user_data['state'] = 'delbooking_choose'
        return
    else:
        await handle_menu(update, context)

async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    user_id = update.effective_user.id
    lang = get_lang(user_id, data)
    is_admin = (user_id == ADMIN_ID)
    text = update.message.text if update.message and update.message.text else ''
    text_clean = clean_text(text)
    print('text:', text)
    print('text_clean:', text_clean)
    # Foydalanuvchi uchun universal 'xonalar' tugmasi
    if 'xonalar' in text_clean:
        await smart_reply(update, 'Xonalar ro‘yxati:' if lang == 'uz' else 'Список номеров:', reply_markup=user_rooms_menu(data, lang))
        context.user_data['state'] = 'user_rooms'
        return
    # Admin uchun universal 'royxat' tugmasi
    if is_admin and 'royxat' in text_clean:
        await rooms(update, context)
        return
    if is_admin and 'xonalarroyxati' in text_clean:
        await rooms(update, context)
        return
    if is_admin and 'xonaqoshish' in text_clean:
        await smart_reply(update, 'Xona nomini kiriting:')
        context.user_data['state'] = 'addroom_name'
        return
    if is_admin and 'xonaochirish' in text_clean:
        if not data['rooms']:
            await smart_reply(update, 'Xonalar yo‘q.')
            return
        await smart_reply(update,
            'O‘chirmoqchi bo‘lgan xonani tanlang:' if lang == 'uz' else 'Выберите номер для удаления:',
            reply_markup=room_delete_menu(data)
        )
        context.user_data['state'] = 'delroom_choose'
        return
    if is_admin and 'bronlarroʻyxati' in text_clean:
        await bookings(update, context)
        return
    if is_admin and 'bronoʻchirish' in text_clean:
        await smart_reply(update, 'Bronni o‘chirish: /delbooking <id>')
        return
    if is_admin and 'bizhaqimizdaoʻzgartirish' in text_clean:
        await smart_reply(update, 'O‘zgartirish: /setabout <uz|ru> <matn>')
        return
    if is_admin and 'lokatsiyayoʻzgartirish' in text_clean:
        await smart_reply(update, 'O‘zgartirish: /setlocation <matn>')
        return
    if is_admin and 'restoranraqaminiyoʻzgartirish' in text_clean:
        await smart_reply(update, 'O‘zgartirish: /setrestaurant <raqam>')
        return
    if is_admin and 'orqaga' in text_clean:
        await smart_reply(update, 'Asosiy menyu' if lang == 'uz' else 'Главное меню', reply_markup=main_menu(lang, is_admin))
        context.user_data.clear()
        return
    if is_admin and ('adminpanelgakirish' in text_clean or 'войтивадинпанель' in text_clean):
        await smart_reply(update, 'Admin paneli:' if lang == 'uz' else 'Админ-панель:', reply_markup=admin_panel_menu(lang))
        context.user_data['state'] = 'admin_panel'
        return
    if text in ['Xonalar', 'Номера']:
        if not data['rooms']:
            await smart_reply(update, 'Xonalar mavjud emas.' if lang == 'uz' else 'Номера отсутствуют.')
            return
        await smart_reply(update, 'Xonalar ro‘yxati:' if lang == 'uz' else 'Список номеров:', reply_markup=user_rooms_menu(data, lang))
        context.user_data['state'] = 'user_rooms'
    elif text in ['Aloqa', 'Связь']:
        await smart_reply(
            update,
            'Nomeringizni kiriting:' if lang == 'uz' else 'Введите свой номер:',
            reply_markup=ReplyKeyboardMarkup(
                [[KeyboardButton('📱 Telefon raqamni yuborish', request_contact=True)]],
                resize_keyboard=True
            )
        )
        context.user_data['state'] = 'contact_phone'
    elif text in ['Lokatsiya', 'Локация']:
        loc = data['location']
        if loc:
            # Agar location lat,long ko‘rinishida bo‘lsa, Telegram location sifatida yubor
            if ',' in loc and all(part.replace('.', '', 1).replace('-', '', 1).isdigit() for part in loc.split(',')):
                lat, lon = loc.split(',')
                try:
                    await update.message.reply_location(latitude=float(lat), longitude=float(lon))
                except Exception:
                    maps_url = f'https://maps.google.com/?q={lat},{lon}'
                    await smart_reply(update, f'<a href="{maps_url}">Lokatsiya (Google xarita)</a>', parse_mode='HTML')
            else:
                await smart_reply(update, loc)
        else:
            await smart_reply(update, 'Lokatsiya mavjud emas.' if lang == 'uz' else 'Локация не добавлена.')
    elif text in ['Biz haqimizda', 'О нас']:
        about = data['about'][lang]
        if about:
            await smart_reply(update, about)
        else:
            await smart_reply(update, 'Ma’lumot mavjud emas.' if lang == 'uz' else 'Информация отсутствует.')
    elif text in ['Restoran', 'Ресторан']:
        rest = data['restaurant']
        if rest:
            await smart_reply(update, rest)
        else:
            await smart_reply(update, 'Restoran raqami mavjud emas.' if lang == 'uz' else 'Номер ресторана не добавлен.')
    elif text in ['Til', 'Язык']:
        await smart_reply(
            update,
            'Tilni tanlang:' if lang == 'uz' else 'Выберите язык:',
            reply_markup=ReplyKeyboardMarkup([['🇺🇿 O‘zbek', '🇷🇺 Русский']], resize_keyboard=True)
        )
        context.user_data['state'] = 'choose_lang'
    elif text in ['🇺🇿 O‘zbek', '🇷🇺 Русский']:
        new_lang = 'uz' if text == '🇺🇿 O‘zbek' else 'ru'
        set_lang(user_id, new_lang, data)
        await smart_reply(
            update,
            'Til o‘zgardi.' if new_lang == 'uz' else 'Язык изменён.',
            reply_markup=main_menu(new_lang, is_admin)
        )
        context.user_data.clear()
        return
    # else:
        # await smart_reply(update,
        #     'Noto‘g‘ri buyruq.' if lang == 'uz' else 'Неверная команда.'
        # )

    if is_admin and text in ['Lokatsiyani o‘zgartirish', 'Изменить локацию', '📍 Lokatsiyani o‘zgartirish', '📍 Изменить локацию']:
        await smart_reply(update, 'Yangi lokatsiya matnini kiriting:')
        context.user_data['state'] = 'setlocation_input'
        return
    if is_admin and context.user_data.get('state') == 'setlocation_input' and text:
        data = load_data()
        data['location'] = text
        save_data(data)
        await smart_reply(update, 'Lokatsiya saqlandi!')
        context.user_data.clear()
        return

def admin_only(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != ADMIN_ID:
            await smart_reply(update, 'Ruxsat yo‘q.')
            return
        await func(update, context)
    return wrapper

@admin_only
async def add_room(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = update.message.text.split(maxsplit=5)
    if len(args) < 6:
        await update.message.reply_text('Foydalanish: /addroom <nomi> <sifati> <narxi> <tavsif> <rasm_url>')
        return
    _, name, quality, price, desc, img_url = args
    data = load_data()
    room_id = max([r['id'] for r in data['rooms']], default=0) + 1
    data['rooms'].append({
        'id': room_id, 'name': name, 'quality': quality, 'price': price, 'desc': desc, 'img': img_url
    })
    save_data(data)
    await update.message.reply_text('Xona qo‘shildi.')

@admin_only
async def del_room(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = update.message.text.split()
    if len(args) < 2:
        await update.message.reply_text('Foydalanish: /delroom <id>')
        return
    room_id = int(args[1])
    data = load_data()
    data['rooms'] = [r for r in data['rooms'] if r['id'] != room_id]
    save_data(data)
    await update.message.reply_text('Xona o‘chirildi.')

@admin_only
async def set_about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = update.message.text.split(maxsplit=2)
    if len(args) < 3:
        await update.message.reply_text('/setabout <uz|ru> <text>')
        return
    _, lang, text = args
    data = load_data()
    data['about'][lang] = text
    save_data(data)
    await update.message.reply_text('Saqlangan.')

@admin_only
async def set_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    loc = update.message.text.split(maxsplit=1)[1]
    data = load_data()
    data['location'] = loc
    save_data(data)
    await update.message.reply_text('Lokatsiya saqlandi.')

@admin_only
async def set_restaurant(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rest = update.message.text.split(maxsplit=1)[1]
    data = load_data()
    data['restaurant'] = rest
    save_data(data)
    await update.message.reply_text('Restoran raqami saqlandi.')

@admin_only
async def rooms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    if not data['rooms']:
        await smart_reply(update, 'Xonalar yo‘q.')
        return
    msg = ''
    for r in data['rooms']:
        msg += (
            f"🏨 <b>{r['name']}</b> (ID: <code>{r['id']}</code>)\n"
            f"🏷️ Sifat: <b>{r['quality']}</b>\n"
            f"💵 Narx: <b>{r['price']}</b>\n"
            f"👥 Odamlar soni: <b>{r.get('capacity', 7)}</b>\n"
            f"📝 {r['desc']}\n"
            "----------------------\n"
        )
    await smart_reply(update, msg, parse_mode='HTML')

@admin_only
async def bookings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    if not data['bookings']:
        await smart_reply(update, 'Bronlar yo‘q.')
        return
    msg = ''
    for i, b in enumerate(data['bookings'], 1):
        room = next((r for r in data['rooms'] if r['id'] == b['room_id']), None)
        room_name = room['name'] if room else 'Noma’lum'
        capacity = room['capacity'] if room and 'capacity' in room else 'Noma’lum'
        msg += (
            f"#{i}\n"
            f"👤 <b>{b['username']}</b>\n"
            f"📞 {b['phone']}\n"
            f"🏨 {room_name} (ID: <code>{b['room_id']}</code>)\n"
            f"🏷️ {b['quality']}\n"
            f"👥 {b['people']} / <b>{capacity}</b>\n"
            f"📅 {b['from']} ➡️ {b['to']}\n"
            "----------------------\n"
        )
    await smart_reply(update, msg, parse_mode='HTML')

def booking_delete_menu(data, lang):
    kb = []
    for i, b in enumerate(data['bookings'], 1):
        room = next((r for r in data['rooms'] if r['id'] == b['room_id']), None)
        room_name = room['name'] if room else 'Noma’lum'
        user_display = b.get('username') or b.get('name') or 'User'
        text = f"#{i} {room_name} ({b['from']} ➡️ {b['to']}) | 👤 {user_display}"
        kb.append([InlineKeyboardButton(text, callback_data=f'delbooking_{i-1}')])
    return InlineKeyboardMarkup(kb)

def booking_delete_confirm_menu(idx, lang):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton('Ha' if lang == 'uz' else 'Да', callback_data=f'confirm_delbooking_yes_{idx}'),
            InlineKeyboardButton('Yo‘q' if lang == 'uz' else 'Нет', callback_data=f'confirm_delbooking_no_{idx}')
        ]
    ])

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('addroom', add_room))
    app.add_handler(CommandHandler('delroom', del_room))
    app.add_handler(CommandHandler('setabout', set_about))
    app.add_handler(CommandHandler('setlocation', set_location))
    app.add_handler(CommandHandler('setrestaurant', set_restaurant))
    app.add_handler(CommandHandler('rooms', rooms))
    app.add_handler(CommandHandler('bookings', bookings))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == '__main__':
    main()