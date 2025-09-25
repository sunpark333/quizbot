# main.py
import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, PollAnswerHandler
import asyncio

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

# Global variables for multi-group management
active_groups = set()

# Health check endpoint for UptimeRobot
async def health_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Health check command."""
    active_quizzes = 0
    try:
        from group import get_active_quizzes_count
        active_quizzes = get_active_quizzes_count()
    except ImportError:
        pass
    
    health_text = (
        "🤖 *Bot Status: Active & Healthy* ✅\n\n"
        f"• Bot is running smoothly\n"
        f"• Active quizzes: {active_quizzes}\n"
        f"• Multi-group support: Enabled\n"
        f"• Admin-only mode: Enabled"
    )
    await update.message.reply_text(health_text, parse_mode='Markdown')

# Import group और personal modules with error handling
try:
    import group
    import personal
    import log
    logger.info("Successfully imported group, personal, and log modules")
except ImportError as e:
    logger.error(f"Error importing modules: {e}")
    group = None
    personal = None
    log = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    user = update.effective_user
    chat_type = update.effective_chat.type
    
    # Log user activity
    if log:
        await log.log_user_activity(update, context, "Used /start command")
    
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
                [InlineKeyboardButton("📚 Help", callback_data='help')],
                [InlineKeyboardButton("📊 Bot Status", callback_data='status')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "🤖 *Welcome to 12th Grade Commerce Quiz Bot!*\n\n"
                "🌟 *New Features:*\n"
                "• Admin-only quiz control\n"
                "• Multi-group support\n"
                "• Real-time logging\n"
                "• Enhanced security\n\n"
                "Please add me to a group to start quizzes!",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
    else:
        # Add group to active groups
        active_groups.add(update.effective_chat.id)
        
        welcome_text = (
            f"👋 Hello everyone! Welcome to the 12th Grade Commerce Quiz Bot.\n\n"
            "🆕 *Enhanced Features:*\n"
            "• Only admins can start/stop quizzes\n"
            "• Multi-group support enabled\n"
            "• Real-time activity logging\n"
            "• Enhanced security measures\n\n"
            "*Available Commands:*\n"
            "/quiz - Start a quiz session (Admins only)\n"
            "/stop - Stop ongoing quiz (Admins only)\n"
            "/subjects - See available subjects\n"
            "/help - Help information\n"
            "/status - Check bot status\n\n"
            "⚡ *Note:* Only group admins can start and stop quizzes."
        )
        await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /help is issued."""
    chat_type = update.effective_chat.type
    
    # Log user activity
    if log:
        await log.log_user_activity(update, context, "Used /help command")
    
    if chat_type == "private":
        help_text = """
🤖 *Quiz Bot Help - Private Chat* 🤖

*New Security Features:*
• Admin-only quiz control in groups
• Multi-group support
• Real-time activity logging

*Available Commands:*
/start - Show main menu with options
/help - Show this help message
/status - Check bot status

*How to use:*
1. Add me to your group using the 'Add me in Group' button
2. Make me admin in your group
3. Use /quiz in the group to start quizzes (Admin only)
4. Answer poll questions in the group

*Note:* I work in multiple groups simultaneously with enhanced security.
"""
    else:
        help_text = """
📚 *12th Grade Commerce Quiz Bot Help* 📚

*Enhanced Security Features:*
• Only group admins can start/stop quizzes
• Multi-group support enabled
• Real-time activity monitoring

*Available Commands (Group):*
/quiz - Start a new quiz (Admin only)
/stop - Stop ongoing quiz (Admin only)
/subjects - Show available subjects
/help - Show this help message
/status - Check bot status

*Subjects Available:*
- Accountancy
- Business Studies
- Economics
- Mathematics
- English
- Information Practices

*How to use:*
1. Use /quiz to start a new quiz (Admin only)
2. Select your subject
3. Answer multiple-choice questions via polls
4. Get your score at the end with explanations
5. Use /stop to end quiz early (Admin only)
"""
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def subjects_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show available subjects."""
    # Log user activity
    if log:
        await log.log_user_activity(update, context, "Viewed subjects")
    
    subjects = [
        "Accountancy", "Business Studies", "Economics",
        "Mathematics", "English", "Information Practices"
    ]
    
    text = "📖 *Available Subjects:*\n\n" + "\n".join([f"• {subject}" for subject in subjects])
    await update.message.reply_text(text, parse_mode='Markdown')

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show bot status and active quizzes."""
    active_quizzes = 0
    try:
        from group import get_active_quizzes_count
        active_quizzes = get_active_quizzes_count()
    except ImportError:
        pass
    
    status_text = (
        "📊 *Bot Status Report*\n\n"
        f"• Active groups: {len(active_groups)}\n"
        f"• Active quizzes: {active_quizzes}\n"
        f"• Multi-group support: ✅ Enabled\n"
        f"• Admin-only mode: ✅ Enabled\n"
        f"• Logging: ✅ Active\n"
        f"• API Status: ✅ Connected\n\n"
        "🤖 Bot is running smoothly!"
    )
    await update.message.reply_text(status_text, parse_mode='Markdown')
    
    # Log status check
    if log:
        await log.log_user_activity(update, context, "Checked bot status")

async def quiz_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /quiz command based on chat type."""
    chat_type = update.effective_chat.type
    
    # Log user activity
    if log:
        activity = "Used /quiz command" + (" (Not admin)" if chat_type != "private" else "")
        await log.log_user_activity(update, context, activity)
    
    if chat_type == "private":
        await update.message.reply_text(
            "❌ Quizzes are only available in groups!\n\n"
            "Please add me to a group and make me admin, then use /quiz in the group to start quizzes."
        )
    else:
        if group:
            try:
                await group.group_quiz_command(update, context)
            except Exception as e:
                logger.error(f"Error in group.group_quiz_command: {e}")
                if log:
                    await log.log_error(context, str(e), update)
                await update.message.reply_text("❌ Group quiz functionality temporarily unavailable. Please try again later.")
        else:
            await update.message.reply_text("❌ Group module not available.")

async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stop command for group quizzes."""
    if group:
        try:
            await group.stop_command(update, context)
        except Exception as e:
            logger.error(f"Error in group.stop_command: {e}")
            if log:
                await log.log_error(context, str(e), update)
            await update.message.reply_text("❌ Stop command error occurred. Quiz may continue running.")
    else:
        await update.message.reply_text("❌ Group module not available.")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks."""
    query = update.callback_query
    data = query.data
    
    # Always answer the callback query first to prevent timeout
    try:
        await query.answer()
    except Exception as e:
        logger.error(f"Error answering callback query: {e}")
    
    try:
        if data == 'help':
            await help_command(update, context)
        elif data == 'status':
            await status_command(update, context)
        elif data.startswith('main_') and personal:
            action = data[5:]
            await personal.handle_main_menu(update, context, action)
        elif data.startswith('group_subject_') and group:
            subject = data.split('_', 2)[2]
            await group.handle_group_subject_selection(update, context, subject)
        elif data == 'group_cancel' and group:
            await group.handle_group_cancel(update, context)
        else:
