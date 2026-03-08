import logging
import os
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

# إعداد السجلات (Logging)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# استخدام متغيرات البيئة (Environment Variables) للأمان
# يجب ضبط هذه المتغيرات في إعدادات المنصة المستضيفة (Render/Railway)
TOKEN = os.getenv('TELEGRAM_TOKEN', '6149689240:AAGG5lPvu0ay9OvuP2fxzduJKLBzWzt7Ppc')
OWNER_ID = int(os.getenv('OWNER_ID', '5024327891'))
USERS_FILE = 'users.txt'

# قواميس النصوص للغات المختلفة
MESSAGES = {
    'ar': (
        "👤 **الاسم:** محمد شعبان سليمان النجار\n"
        "🛠 **النشاط:** صناعة الأخشاب\n"
        "📍 **الموقع:** دمياط، مصر\n\n"
        "💰 **سعر الخدمة:**\n"
        "500 جنيه مصري لمدة 12 ساعة يومياً\n\n"
        "💳 **أرقام سويفت النقدي للدفع:**\n"
        "1. +201024187101 - ڤوداڤون\n"
        "2. +201121922599 - إتصالات\n"
        "3. +201270145239 - ORANGE EGY\n"
        "4. +201550279020 - WE PAY\n"
        "5. +201550289020 - CIB Egypt\n\n"
        "يمكنك التواصل معنا عبر هذه الأرقام للطلب أو الاستفسار."
    ),
    'en': (
        "👤 **Name:** Mohamed Shaban Soliman El-Naggar\n"
        "🛠 **Activity:** Wood Industry\n"
        "📍 **Location:** Damietta, Egypt\n\n"
        "💰 **Service Price:**\n"
        "500 EGP for 12 hours daily\n\n"
        "💳 **Swift Cash Payment Numbers:**\n"
        "1. +201024187101 - Vodafone\n"
        "2. +201121922599 - Etisalat\n"
        "3. +201270145239 - ORANGE EGY\n"
        "4. +201550279020 - WE PAY\n"
        "5. +201550289020 - CIB Egypt\n\n"
        "You can contact us via these numbers for orders or inquiries."
    ),
    'ru': (
        "👤 **Имя:** Мохамед Шабан Солиман Эль-Наггар\n"
        "🛠 **Деятельность:** Деревообрабатывающая промышленность\n"
        "📍 **Местоположение:** Дамиетта, Египет\n\n"
        "💰 **Стоимость услуги:**\n"
        "500 египетских фунтов за 12 часов в день\n\n"
        "💳 **Номера для оплаты Swift Cash:**\n"
        "1. +201024187101 - Vodafone\n"
        "2. +201121922599 - Etisalat\n"
        "3. +201270145239 - ORANGE EGY\n"
        "4. +201550279020 - WE PAY\n"
        "5. +201550289020 - CIB Egypt\n\n"
        "Вы можете связаться с нами по этим номерам для заказов или справок."
    )
}

def save_user(user_id):
    """حفظ معرف المستخدم في ملف نصي لضمان عمل ميزة الإذاعة"""
    try:
        user_id_str = str(user_id)
        if not os.path.exists(USERS_FILE):
            with open(USERS_FILE, 'w') as f:
                f.write(user_id_str + '\n')
            return
        
        with open(USERS_FILE, 'r') as f:
            users = f.read().splitlines()
        
        if user_id_str not in users:
            with open(USERS_FILE, 'a') as f:
                f.write(user_id_str + '\n')
    except Exception as e:
        logger.error(f"Error saving user: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التعامل مع أمر /start وعرض خيارات اللغة"""
    user = update.effective_user
    save_user(user.id)
    
    notification = (
        f"🔔 **مستخدم جديد تفاعل مع البوت!**\n\n"
        f"👤 الاسم: {user.full_name}\n"
        f"🆔 المعرف (ID): `{user.id}`\n"
        f"🔗 اليوزر: @{user.username if user.username else 'لا يوجد'}"
    )
    
    try:
        await context.bot.send_message(chat_id=OWNER_ID, text=notification, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Failed to notify owner: {e}")

    keyboard = [
        [
            InlineKeyboardButton("عربي 🇪🇬", callback_data='ar'),
            InlineKeyboardButton("English 🇺🇸", callback_data='en'),
            InlineKeyboardButton("Русский 🇷🇺", callback_data='ru'),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_msg = "يرجى اختيار اللغة / Please choose a language / Пожалуйста, выберите язык:"
    await update.message.reply_text(welcome_msg, reply_markup=reply_markup)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التعامل مع اختيار اللغة من الأزرار"""
    query = update.callback_query
    await query.answer()
    
    lang = query.data
    text = MESSAGES.get(lang, MESSAGES['ar'])
    
    await query.edit_message_text(text=text, parse_mode='Markdown')

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إرسال رسالة إذاعية لجميع المستخدمين (للمالك فقط)"""
    if update.effective_user.id != OWNER_ID:
        return

    if not context.args:
        await update.message.reply_text("❌ يرجى كتابة الرسالة بعد الأمر. مثال:\n`/broadcast السلام عليكم`", parse_mode='Markdown')
        return

    message_to_send = " ".join(context.args)
    
    if not os.path.exists(USERS_FILE):
        await update.message.reply_text("❌ لا يوجد مستخدمون مسجلون حالياً.")
        return

    with open(USERS_FILE, 'r') as f:
        users = f.read().splitlines()

    count = 0
    for user_id in users:
        try:
            await context.bot.send_message(chat_id=int(user_id), text=message_to_send)
            count += 1
        except Exception as e:
            logger.error(f"Failed to send to {user_id}: {e}")

    await update.message.reply_text(f"✅ تم إرسال الرسالة إلى {count} مستخدم.")

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الرسائل الصادرة والواردة بين المالك والمستخدمين"""
    user = update.effective_user
    text = update.message.text

    if user.id == OWNER_ID and update.message.reply_to_message:
        original_msg = update.message.reply_to_message.text or update.message.reply_to_message.caption
        if original_msg:
            match = re.search(r"🆔 المعرف \(ID\): `(\d+)`", original_msg)
            if match:
                target_id = int(match.group(1))
                try:
                    await context.bot.send_message(chat_id=target_id, text=f"💬 **رد من الإدارة:**\n\n{text}", parse_mode='Markdown')
                    await update.message.reply_text(f"✅ تم إرسال الرد للمستخدم `{target_id}`.")
                except Exception as e:
                    await update.message.reply_text(f"❌ فشل الرد: {e}")
                return
        return

    if user.id == OWNER_ID:
        return

    forward_msg = (
        f"📩 **رسالة جديدة من مستخدم:**\n\n"
        f"👤 الاسم: {user.full_name}\n"
        f"🆔 المعرف (ID): `{user.id}`\n"
        f"💬 الرسالة: {text}"
    )
    
    try:
        await context.bot.send_message(chat_id=OWNER_ID, text=forward_msg, parse_mode='Markdown')
        await update.message.reply_text("✅ تم استلام رسالتك، وسنقوم بالرد عليك في أقرب وقت.")
    except Exception as e:
        logger.error(f"Failed to forward message to owner: {e}")

async def reply_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر الرد اليدوي للمالك: /reply [user_id] [message]"""
    if update.effective_user.id != OWNER_ID:
        return

    if len(context.args) < 2:
        await update.message.reply_text("❌ الاستخدام الصحيح: `/reply [user_id] [message]`", parse_mode='Markdown')
        return

    try:
        target_id = int(context.args[0])
        reply_text = " ".join(context.args[1:])
        await context.bot.send_message(chat_id=target_id, text=f"💬 **رد من الإدارة:**\n\n{reply_text}", parse_mode='Markdown')
        await update.message.reply_text(f"✅ تم إرسال الرد إلى `{target_id}`.")
    except ValueError:
        await update.message.reply_text("❌ معرف المستخدم يجب أن يكون رقماً.")
    except Exception as e:
        await update.message.reply_text(f"❌ فشل الإرسال: {e}")

if __name__ == '__main__':
    application = ApplicationBuilder().token(TOKEN).build()
    
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('broadcast', broadcast))
    application.add_handler(CommandHandler('reply', reply_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_messages))
    
    print("البوت جاهز للنشر...")
    application.run_polling()
