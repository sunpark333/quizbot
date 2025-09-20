import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, PollAnswerHandler

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Bot token and API key - Environment variables से लें
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
PERPLEXITY_API_KEY = os.environ.get("PERPLEXITY_API_KEY")

# Health check endpoint for UptimeRobot
async def health_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot is active and running!")

# Import group and personal modules
import group
import personal

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    user = update.effective_user
    chat_type = update.effective_chat.type
    
    if chat_type == "private":
        await personal.start_command(update, context)
    else:
        await update.message.reply_text(
            f"👋 Hello everyone! Welcome to the 12th Grade Commerce Quiz Bot.\n\n"
            "I will post quiz questions as polls in this group every 30 seconds.\n\n"
            "Use /quiz to start a quiz session in this group!\n"
            "Use /stop to stop an ongoing quiz\n"
            "Use /subjects to see available subjects\n"
            "Use /help for more information"
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /help is issued."""
    chat_type = update.effective_chat.type
    
    if chat_type == "private":
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
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def subjects_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show available subjects."""
    subjects = [
        "Accountancy", "Business Studies", "Economics",
        "Mathematics", "English", "Information Practices"
    ]
    
    text = "📖 *Available Subjects:*\n\n" + "\n".join([f"• {subject}" for subject in subjects])
    await update.message.reply_text(text, parse_mode='Markdown')

async def quiz_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /quiz command based on chat type."""
    chat_type = update.effective_chat.type
    
    if chat_type == "private":
        await update.message.reply_text(
            "❌ Quizzes are only available in groups!\n\n"
            "Please add me to a group using the 'Add me in Group' button from the main menu, "
            "then use /quiz in the group to start quizzes."
        )
    else:
        await group.group_quiz_command(update, context)

async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stop command for group quizzes."""
    await group.stop_command(update, context)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks."""
    query = update.callback_query
    data = query.data
    
    if data.startswith('main_'):
        action = data[5:]
        await personal.handle_main_menu(update, context, action)
    elif data.startswith('category_'):
        category = data[9:]
        if category == 'back':
            await personal.handle_main_menu(update, context, 'back')
        else:
            keyboard = [
                [InlineKeyboardButton("➕ Add me in Group", url=f"https://t.me/{context.bot.username}?startgroup=true")],
                [InlineKeyboardButton("🔙 Back", callback_data='main_back')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                text="❌ Quizzes are only available in groups!\n\n"
                "Please add me to a group using the 'Add me in Group' button below to start quizzes.",
                reply_markup=reply_markup
            )
    elif data.startswith('subject_'):
        keyboard = [
            [InlineKeyboardButton("➕ Add me in Group", url=f"https://t.me/{context.bot.username}?startgroup=true")],
            [InlineKeyboardButton("🔙 Back", callback_data='main_back')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text="❌ Quizzes are only available in groups!\n\n"
            "Please add me to a group using the 'Add me in Group' button below to start quizzes.",
            reply_markup=reply_markup
        )
    elif data.startswith('group_subject_'):
        subject = data.split('_', 2)[2]
        await group.handle_group_subject_selection(update, context, subject)
    elif data.startswith('diff_'):
        keyboard = [
            [InlineKeyboardButton("➕ Add me in Group", url=f"https://t.me/{context.bot.username}?startgroup=true")],
            [InlineKeyboardButton("🔙 Back", callback_data='main_back')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text="❌ Quizzes are only available in groups!\n\n"
            "Please add me to a group using the 'Add me in Group' button below to start quizzes.",
            reply_markup=reply_markup
        )
    elif data.startswith('answer_'):
        keyboard = [
            [InlineKeyboardButton("➕ Add me in Group", url=f"https://t.me/{context.bot.username}?startgroup=true")],
            [InlineKeyboardButton("🔙 Back", callback_data='main_back')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text="❌ Quizzes are only available in groups!\n\n"
            "Please add me to a group using the 'Add me in Group' button below to start quizzes.",
            reply_markup=reply_markup
        )
    elif data == 'continue':
        keyboard = [
            [InlineKeyboardButton("➕ Add me in Group", url=f"https://t.me/{context.bot.username}?startgroup=true")],
            [InlineKeyboardButton("🔙 Back", callback_data='main_back')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text="❌ Quizzes are only available in groups!\n\n"
            "Please add me to a group using the 'Add me in Group' button below to start quizzes.",
            reply_markup=reply_markup
        )
    elif data == 'new_quiz':
        await quiz_command(update, context)
    elif data.startswith('exam_'):
        keyboard = [
            [InlineKeyboardButton("➕ Add me in Group", url=f"https://t.me/{context.bot.username}?startgroup=true")],
            [InlineKeyboardButton("🔙 Back", callback_data='main_back')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text="❌ Quizzes are only available in groups!\n\n"
            "Please add me to a group using the 'Add me in Group' button below to start quizzes.",
            reply_markup=reply_markup
        )

def main():
    """Start the bot."""
    # Get PORT from environment variable for Render deployment
    PORT = int(os.environ.get("PORT", 8443))
    
    # Create the Application and pass it your bot's token
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("quiz", quiz_command))
    application.add_handler(CommandHandler("stop", stop_command))
    application.add_handler(CommandHandler("subjects", subjects_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(PollAnswerHandler(group.handle_poll_answer))
    application.add_handler(CommandHandler("health", health_check))
    
    # For Render deployment, use webhooks instead of polling
    if "RENDER" in os.environ:
        # Webhook mode for production
        WEBHOOK_URL = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME')}"
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            webhook_url=f"{WEBHOOK_URL}/webhook",
            url_path="/webhook"
        )
    else:
        # Polling mode for development
        print("Commerce Quiz Bot is running with Perplexity AI...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
