import os
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from bot.handlers import PhotoEncryptBot
from dotenv import load_dotenv

load_dotenv()

async def post_init(application: Application) -> None:
    await application.bot.set_my_commands([
        ("start", "Start the bot"),
        ("init_group", "Initialize group encryption"),
    ])

def main():
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        raise ValueError("Please set TELEGRAM_BOT_TOKEN in .env file")
    
    app = Application.builder().token(TOKEN).post_init(post_init).build()
    
    bot = PhotoEncryptBot(app)
    
    app.run_polling(allowed_updates=["message", "callback_query"])

if __name__ == "__main__":
    main()