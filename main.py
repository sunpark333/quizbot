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

# Bot token और API key - Environment variables से लें
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
PERPLEXITY_API_KEY = os.environ.get("PERPLEXITY_API_KEY")

# Webhook configuration
WEBHOOK_URL = os.environ.get("RENDER_EXTERNAL_HOSTNAME", "localhost")
WEBHOOK_PATH = "/webhook"

# Health check endpoint for UptimeRobot
async def health_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot is active and running!")

# Import group और personal modules with error handling
try:
    import group
    import personal
    logger.info("Successfully imported group and personal modules")
except ImportError as e:
    logger.error(f"Error importing modules: {e}")
    group = None
    personal = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    user = update.effective_user
    chat_type = update.effective_chat.type
    
    if chat_type == "private":
        if personal:
            try:
                await personal.start_command(update, context)
            except Exception as e:
                logger.error(f"Error in personal.start_command: {e}")
                await update.message.reply_text("Personal module error occurred.")
        else:
            # Basic welcome message if personal module is not available
            keyboard = [
                [InlineKeyboardButton("➕ Add me in Group", url=f"https://t.me/{context.bot.username}?startgroup=true")],
                [InlineKeyboardButton("📚 Help", callback_data='help')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "🤖 *Welcome to 12th Grade Commerce Quiz Bot!*\n\n"
                "This bot provides quiz functionality in groups.\n\n"
                "Please add me to a group to start quizzes!",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
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
        if group:
            try:
                await group.group_quiz_command(update, context)
            except Exception as e:
                logger.error(f"Error in group.group_quiz_command: {e}")
                await update.message.reply_text("Group quiz functionality temporarily unavailable. Please try again later.")
        else:
            await update.message.reply_text("Group module not available.")

async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stop command for group quizzes."""
    if group:
        try:
            await group.stop_command(update, context)
        except Exception as e:
            logger.error(f"Error in group.stop_command: {e}")
            await update.message.reply_text("Stop command error occurred. Quiz may continue running.")
    else:
        await update.message.reply_text("Group module not available.")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks."""
    query = update.callback_query
    
    # Always answer the callback query first to prevent timeout
    try:
        await query.answer()
    except Exception as e:
        logger.error(f"Error answering callback query: {e}")
    
    data = query.data
    
    try:
        if data == 'help':
            await help_command(update, context)
        elif data.startswith('main_') and personal:
            action = data[5:]
            await personal.handle_main_menu(update, context, action)
        elif data.startswith('category_') and personal:
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
        elif data.startswith('group_subject_') and group:
            subject = data.split('_', 2)[2]
            await group.handle_group_subject_selection(update, context, subject)
        else:
            # Default response for unavailable modules
            keyboard = [
                [InlineKeyboardButton("➕ Add me in Group", url=f"https://t.me/{context.bot.username}?startgroup=true")],
                [InlineKeyboardButton("🔙 Back", callback_data='main_back')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                text="❌ Module not available or Quizzes are only available in groups!\n\n"
                "Please add me to a group using the 'Add me in Group' button below to start quizzes.",
                reply_markup=reply_markup
            )
    except Exception as e:
        logger.error(f"Error in button handler: {e}")
        # Don't try to answer callback query again here

async def poll_answer_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle poll answers."""
    if group:
        try:
            await group.handle_poll_answer(update, context)
        except Exception as e:
            logger.error(f"Error in poll handler: {e}")
    else:
        logger.error("Group module not available for poll handling.")

def main():
    """Start the bot."""
    # Bot token check करें
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN environment variable not set!")
        return
    
    # Get PORT from environment variable for Render deployment
    PORT = int(os.environ.get("PORT", 8443))
    
    # Create the Application with JobQueue enabled
    try:
        from telegram.ext import JobQueue
        application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        logger.info("Application created successfully with JobQueue support")
    except Exception as e:
        logger.error(f"Failed to create application: {e}")
        return
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("quiz", quiz_command))
    application.add_handler(CommandHandler("stop", stop_command))
    application.add_handler(CommandHandler("subjects", subjects_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(PollAnswerHandler(poll_answer_handler))
    application.add_handler(CommandHandler("health", health_check))
    
    # Add error handler
    async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
        """Log the error and send a telegram message to notify the developer."""
        logger.error(f"Exception while handling an update: {context.error}")
    
    application.add_error_handler(error_handler)
    
    # For Render deployment, use webhooks
    if "RENDER" in os.environ:
        # Webhook mode for production
        try:
            webhook_url = f"https://{WEBHOOK_URL}"
            logger.info(f"Starting webhook at {webhook_url}")
            
            # Set webhook
            application.run_webhook(
                listen="0.0.0.0",
                port=PORT,
                url_path=WEBHOOK_PATH,
                webhook_url=f"{webhook_url}{WEBHOOK_PATH}",
                secret_token=os.environ.get("WEBHOOK_SECRET", "your-secret-token")
            )
        except Exception as e:
            logger.error(f"Failed to start webhook: {e}")
            # Fallback to polling if webhook fails
            logger.info("Falling back to polling mode...")
            application.run_polling(allowed_updates=Update.ALL_TYPES)
    else:
        # Polling mode for development
        try:
            logger.info("Commerce Quiz Bot is running with Perplexity AI in polling mode...")
            application.run_polling(allowed_updates=Update.ALL_TYPES)
        except Exception as e:
            logger.error(f"Failed to start polling: {e}")

if __name__ == '__main__':
    main()
