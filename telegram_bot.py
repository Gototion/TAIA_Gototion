import os
from dotenv import load_dotenv
from typing import Final
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Credentials
load_dotenv()
TOKEN : Final = os.getenv('TOKEN')
BOT_USERNAME : Final = os.getenv('BOT_USERNAME')

# Comands (/start, /help, etc)
async def start_command(update : Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = "Bienvenido!"
    await update.message.reply_text(msg)

# Reponses    
def handle_response(text : str) -> str:
    return "Aqui falta implementar el LLM."

# Messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type : str = update.message.chat.type # Public chat or Private chat
    text : str = update.message.text
    user : int = update.message.chat.id

    print(f'Usuario {user} en {message_type}: "{text}"')

    if message_type == 'group':
        if not BOT_USERNAME in text: return 
        new_text : str = text.replace(BOT_USERNAME, '').strip()
        response : str = handle_response(new_text)
    else:
        response : str = handle_response(text)
        print('Bot:', response)
        await update.message.reply_text(response)

# Errors        
async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} causo el siguiente error: {context.error}')
            

# Main Program
if __name__ == '__main__':
    print("Iniciando Gototion...\n")
    app = Application.builder().token(TOKEN).build()

    # Comands
    app.add_handler(CommandHandler('start', start_command))

    # Messages
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    # Errors
    app.add_error_handler(error)

    print("Esperando respuestas...\n")
    app.run_polling(poll_interval=3)
