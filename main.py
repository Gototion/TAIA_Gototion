# main.py

if __name__ == "__main__":
    from bot.pooling_bot import pooling_bot
    app = pooling_bot()
    app.run_polling()
