import os
import logging
from flask import Flask, request, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, PollAnswerHandler

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot token और API key
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
PERPLEXITY_API_KEY = os.environ.get("PERPLEXITY_API_KEY")

# Flask app for webhook and health check
app = Flask(__name__)

# Telegram Application
application = None

# Import modules
try:
    import group
    import personal
    logger.info("Successfully imported group and personal modules")
except ImportError as e:
    logger.error(f"Error importing modules: {e}")
    group = None
    personal = None

# Health check endpoint for UptimeRobot
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for UptimeRobot monitoring"""
    return jsonify({
        'status': 'ok',
        'service': 'telegram-quiz-bot',
        'timestamp': int(time.time()),
        'message': 'Bot is running successfully'
    }), 200

@app.route('/', methods=['GET'])
def home():
    """Root endpoint"""
    return jsonify({
        'status': 'active',
        'service': 'Commerce Quiz Bot',
        'message': 'Bot is running on Render.com'
    }), 200

# Webhook endpoint
@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming webhook from Telegram"""
    try:
        json_string = request.get_data().decode('utf-8')
        update = Update.de_json(json.loads(json_string), application.bot)
        
        # Process update asynchronously
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(application.process_update(update))
        loop.close()
        
        return jsonify({'status': 'ok'}), 200
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# Bot handlers
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
        elif data.startswith('group_subject_') and group:
            subject = data.split('_', 2)[2]
            await group.handle_group_subject_selection(update, context, subject)
        else:
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

async def poll_answer_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle poll answers."""
    if group:
        try:
            await group.handle_poll_answer(update, context)
        except Exception as e:
            logger.error(f"Error in poll handler: {e}")
    else:
        logger.error("Group module not available for poll handling.")

def setup_bot():
    """Setup telegram bot application"""
    global application
    
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN environment variable not set!")
        return None
    
    try:
        application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("quiz", quiz_command))
        application.add_handler(CommandHandler("stop", stop_command))
        application.add_handler(CommandHandler("subjects", subjects_command))
        application.add_handler(CallbackQueryHandler(button_handler))
        application.add_handler(PollAnswerHandler(poll_answer_handler))
        
        # Error handler
        async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
            logger.error(f"Exception while handling an update: {context.error}")
        
        application.add_error_handler(error_handler)
        
        logger.info("Bot application setup completed")
        return application
    except Exception as e:
        logger.error(f"Failed to create application: {e}")
        return None

def main():
    """Start the Flask app with webhook"""
    import time
    import json
    
    # Setup bot
    setup_bot()
    
    if not application:
        logger.error("Failed to setup bot application")
        return
    
    # Get port from environment
    PORT = int(os.environ.get("PORT", 10000))
    
    # Set webhook URL
    if "RENDER" in os.environ:
        webhook_url = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME')}/webhook"
        
        # Set webhook asynchronously
        import asyncio
        async def set_webhook():
            try:
                await application.bot.set_webhook(url=webhook_url)
                logger.info(f"Webhook set to: {webhook_url}")
            except Exception as e:
                logger.error(f"Failed to set webhook: {e}")
        
        # Run webhook setup
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(set_webhook())
        loop.close()
    
    logger.info(f"Starting Flask app on port {PORT}")
    
    # Start Flask app
    app.run(host="0.0.0.0", port=PORT, debug=False)

if __name__ == '__main__':
    main()
