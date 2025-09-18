import os
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext, PollAnswerHandler

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot token and API key - Environment variables से लें
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
PERPLEXITY_API_KEY = os.environ.get("PERPLEXITY_API_KEY")

# Import group and personal modules
import group
import personal

def start(update: Update, context: CallbackContext):
    """Send a message when the command /start is issued."""
    user = update.effective_user
    chat_type = update.effective_chat.type
    
    if chat_type == "private":
        # Use the new start command with buttons from personal.py
        asyncio.run(personal.start_command(update, context))
    else:
        # Group chat
        update.message.reply_text(
            f"👋 Hello everyone! Welcome to the 12th Grade Commerce Quiz Bot.\n\n"
            "I will post quiz questions as polls in this group every 30 seconds.\n\n"
            "Use /quiz to start a quiz session in this group!\n"
            "Use /stop to stop an ongoing quiz\n"
            "Use /subjects to see available subjects\n"
            "Use /help for more information"
        )

def help_command(update: Update, context: CallbackContext):
    """Send a message when the command /help is issued."""
    chat_type = update.effective_chat.type
    
    if chat_type == "private":
        # Private chat help
        help_text = """
🤖 *Quiz Bot Help - Private Chat* 🤖

This bot works only in groups. Here's what you can do:

*Available Commands:*
/start - Show main menu with options
/help - Show this help message

*How to use:*
1. Add me to your group using the 'Add me in Group' button
2. Use /quiz in the group to start quizzes
3. Answer poll questions in the group

*Note:* I don't provide quizzes in private chats, only in groups.
"""
    else:
        # Group chat help
        help_text = """
📚 *12th Grade Commerce Quiz Bot Help* 📚

*Available Commands:*
/start - Start the bot
/quiz - Start a new quiz
/stop - Stop an ongoing group quiz
/subjects - Show available subjects
/help - Show this help message

*How to use:*
1. Use /quiz to start a new quiz
2. Select your subject and difficulty level
3. Answer multiple-choice questions by clicking a, b, c, or d
4. Get your score at the end with explanations

*Subjects Available:*
- Accountancy
- Business Studies
- Economics
- Mathematics
- English
- Information Practices
"""
    update.message.reply_text(help_text, parse_mode='Markdown')

def subjects_command(update: Update, context: CallbackContext):
    """Show available subjects."""
    subjects = [
        "Accountancy", "Business Studies", "Economics", 
        "Mathematics", "English", "Information Practices"
    ]
    
    text = "📖 *Available Subjects:*\n\n" + "\n".join([f"• {subject}" for subject in subjects])
    update.message.reply_text(text, parse_mode='Markdown')

def quiz_command(update: Update, context: CallbackContext):
    """Handle /quiz command based on chat type."""
    chat_type = update.effective_chat.type
    
    if chat_type == "private":
        # Private chat - inform user that quizzes are only for groups
        update.message.reply_text(
            "❌ Quizzes are only available in groups!\n\n"
            "Please add me to a group using the 'Add me in Group' button from the main menu, "
            "then use /quiz in the group to start quizzes."
        )
    else:
        # Group chat - proceed with group quiz
        asyncio.run(group.group_quiz_command(update, context))

def stop_command(update: Update, context: CallbackContext):
    """Handle /stop command for group quizzes."""
    asyncio.run(group.stop_command(update, context))

def button_handler(update: Update, context: CallbackContext):
    """Handle button callbacks."""
    query = update.callback_query
    query.answer()
    data = query.data
    
    # Handle main menu buttons
    if data.startswith('main_'):
        action = data[5:]
        asyncio.run(personal.handle_main_menu(update, context, action))
    
    # Handle group subject selection
    elif data.startswith('group_subject_'):
        subject = data.split('_', 2)[2]
        asyncio.run(group.handle_group_subject_selection(update, context, subject))
    
    # Handle other buttons
    elif data == 'new_quiz':
        quiz_command(update, context)
    else:
        # For other buttons, show group-only message
        keyboard = [
            [InlineKeyboardButton("➕ Add me in Group", url=f"https://t.me/{context.bot.username}?startgroup=true")],
            [InlineKeyboardButton("🔙 Back", callback_data='main_back')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(
            text="❌ Quizzes are only available in groups!\n\n"
                 "Please add me to a group using the 'Add me in Group' button below to start quizzes.",
            reply_markup=reply_markup
        )

def main():
    """Start the bot."""
    # Check if environment variables are set
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN environment variable is not set!")
        return
    
    if not PERPLEXITY_API_KEY:
        logger.error("PERPLEXITY_API_KEY environment variable is not set!")
        return
    
    try:
        # Create the Updater and pass it your bot's token
        updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
        
        # Get the dispatcher to register handlers
        dispatcher = updater.dispatcher

        # Add handlers
        dispatcher.add_handler(CommandHandler("start", start))
        dispatcher.add_handler(CommandHandler("help", help_command))
        dispatcher.add_handler(CommandHandler("quiz", quiz_command))
        dispatcher.add_handler(CommandHandler("stop", stop_command))
        dispatcher.add_handler(CommandHandler("subjects", subjects_command))
        dispatcher.add_handler(CallbackQueryHandler(button_handler))
        dispatcher.add_handler(PollAnswerHandler(group.handle_poll_answer))

        # Start the Bot
        print("Commerce Quiz Bot is running with Perplexity AI...")
        updater.start_polling()
        updater.idle()
        
    except Exception as e:
        logger.error(f"Error starting bot: {e}")

if __name__ == '__main__':
    main()
