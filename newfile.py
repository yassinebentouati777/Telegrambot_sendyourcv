import os
import smtplib
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, ConversationHandler
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# بيانات البريد الإلكتروني
EMAIL_SENDER = os.getenv("EMAIL_SENDER")  
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")  # كلمة مرور التطبيقات
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# توكن بوت تيليجرام
TOKEN = os.getenv("TOKEN")

# حالات المحادثة
GET_EMAIL, GET_CV, GET_LANGUAGE = range(3)

async def start(update: Update, context: CallbackContext):
    """يتم تشغيله عند بدء المحادثة"""
    await update.message.reply_text("👋 مرحبًا! \nمن فضلك، أرسل لي البريد الإلكتروني للشركة التي تريد التقديم عليها.")
    return GET_EMAIL

async def get_email(update: Update, context: CallbackContext):
    """استقبال البريد الإلكتروني للشركة"""
    context.user_data["company_email"] = update.message.text
    await update.message.reply_text("📎 الآن، أرسل لي ملف السيرة الذاتية بصيغة PDF.")
    return GET_CV

async def get_cv(update: Update, context: CallbackContext):
    """استقبال وتحميل ملف السيرة الذاتية"""
    document = update.message.document

    if document.mime_type != "application/pdf":
        await update.message.reply_text("❌ يرجى إرسال ملف بصيغة PDF فقط.")
        return GET_CV

    file_id = document.file_id
    file_path = f"{document.file_name}"  # حفظ الملف بنفس اسمه
    new_file = await context.bot.get_file(file_id)
    
    await new_file.download_to_drive(file_path)  # تحميل الملف
    context.user_data["cv_path"] = file_path

    await update.message.reply_text("🌍 اختر لغة الرسالة:\n1️⃣ الإنجليزية \n2️⃣ الفرنسية")
    return GET_LANGUAGE

async def get_language(update: Update, context: CallbackContext):
    """اختيار اللغة"""
    choice = update.message.text.strip()
    if choice == "1":
        context.user_data["language"] = "english"
        subject = "Job Application - Instrumentation Engineer"
        body = "Dear Hiring Manager,\n\nI am interested in applying for an Instrumentation Engineer position. Please find my attached resume.\n\nBest regards,\nBEBTOUATI Yassine"
    elif choice == "2":
        context.user_data["language"] = "french"
        subject = "Candidature - Ingénieur en instrumentation"
        body = "Cher Responsable du recrutement,\n\nJe souhaite postuler pour un poste d'Ingénieur en instrumentation. Vous trouverez ci-joint mon CV.\n\nCordialement,\nBENTOUATI Yassine"
    else:
        await update.message.reply_text("❌ يرجى اختيار 1 أو 2 فقط.")
        return GET_LANGUAGE

    company_email = context.user_data["company_email"]
    cv_path = context.user_data["cv_path"]

    result = await send_email(company_email, cv_path, subject, body)
    await update.message.reply_text(result)

    # حذف الملف بعد الإرسال
    if os.path.exists(cv_path):
        os.remove(cv_path)

    return ConversationHandler.END

async def send_email(company_email, cv_path, subject, body):
    """إرسال البريد الإلكتروني"""
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_SENDER
        msg["To"] = company_email
        msg["Subject"] = subject  # ✅ تغيير عنوان البريد بناءً على اللغة المختارة

        msg.attach(MIMEText(body, "plain"))

        with open(cv_path, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename={os.path.basename(cv_path)}")
            msg.attach(part)

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        text = msg.as_string()
        server.sendmail(EMAIL_SENDER, company_email, text)
        server.quit()

        return "✅ تم إرسال البريد بنجاح!"
    except Exception as e:
        return f"❌ فشل الإرسال: {str(e)}"

async def cancel(update: Update, context: CallbackContext):
    """إلغاء المحادثة"""
    await update.message.reply_text("🚫 تم إلغاء العملية.")
    return ConversationHandler.END

# إعداد البوت
app = Application.builder().token(TOKEN).build()

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        GET_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)],
        GET_CV: [MessageHandler(filters.Document.PDF, get_cv)],
        GET_LANGUAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_language)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

app.add_handler(conv_handler)

print("✅ البوت يعمل الآن...")
app.run_polling()
