
if __name__ == "__main__":
    from bot import bot
    bot_app = bot.create_bot()
    bot_app.run_polling()
