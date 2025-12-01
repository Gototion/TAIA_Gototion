# main.py

if __name__ == "__main__":
    # Load environment variables FIRST, before any other imports
    import os
    if os.path.exists(".env"):
        try:
            from dotenv import load_dotenv
            load_dotenv()
            print("✓ .env file loaded successfully")
        except ImportError:
            print("⚠ dotenv not installed; using system environment variables")

    from bot.pooling_bot import pooling_bot
    app = pooling_bot()
    app.run_polling()
