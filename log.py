# log.py
import logging
from telegram import Update
from telegram.ext import ContextTypes
import os
from datetime import datetime

logger = logging.getLogger(__name__)

# Log channel ID - Environment variable से लें
LOG_CHANNEL_ID = os.environ.get("LOG_CHANNEL_ID")

async def send_log_to_channel(context: ContextTypes.DEFAULT_TYPE, message: str, message_type: str = "INFO"):
    """Send logs to the log channel"""
    try:
        if LOG_CHANNEL_ID:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            formatted_message = f"📊 **{message_type}** - `{current_time}`\n\n{message}"
            await context.bot.send_message(
                chat_id=LOG_CHANNEL_ID,
                text=formatted_message,
                parse_mode='Markdown'
            )
    except Exception as e:
        logger.error(f"Error sending log to channel: {e}")

async def log_bot_started(context: ContextTypes.DEFAULT_TYPE):
    """Log when bot is started"""
    message = "🤖 *Bot Started Successfully!*\n\nBot is now active and ready to serve multiple groups."
    await send_log_to_channel(context, message, "BOT STATUS")

async def log_group_quiz_started(update: Update, context: ContextTypes.DEFAULT_TYPE, subject: str, group_name: str):
    """Log when a group quiz is started"""
    try:
        user = update.effective_user
        
        message = (
            f"🎯 *New Group Quiz Started*\n\n"
            f"**Group:** {group_name}\n"
            f"**Group ID:** {update.effective_chat.id}\n"
            f"**Started by:** {user.first_name} (@{user.username if user.username else 'N/A'}) - {user.id}\n"
            f"**Subject:** {subject}\n"
            f"**Time:** {update.message.date if update.message else 'N/A'}"
        )
        await send_log_to_channel(context, message, "QUIZ STARTED")
    except Exception as e:
        logger.error(f"Error logging quiz start: {e}")

async def log_quiz_stopped(update: Update, context: ContextTypes.DEFAULT_TYPE, group_name: str, chat_id: int, scores: dict = None):
    """Log when a quiz is stopped"""
    try:
        user = update.effective_user
        
        participants_info = ""
        if scores:
            participants = len(scores)
            if participants > 0:
                top_scorer = max(scores.items(), key=lambda x: x[1])
                participants_info = f"\n**Participants:** {participants}\n**Top Score:** {top_scorer[1]}"
            else:
                participants_info = f"\n**Participants:** 0"
        
        message = (
            f"🛑 *Quiz Stopped*\n\n"
            f"**Group:** {group_name}\n"
            f"**Group ID:** {chat_id}\n"
            f"**Stopped by:** {user.first_name} (@{user.username if user.username else 'N/A'}) - {user.id}"
            f"{participants_info}"
        )
        await send_log_to_channel(context, message, "QUIZ STOPPED")
    except Exception as e:
        logger.error(f"Error logging quiz stop: {e}")

async def log_user_activity(update: Update, context: ContextTypes.DEFAULT_TYPE, activity: str):
    """Log user activities"""
    try:
        user = update.effective_user
        chat = update.effective_chat
        
        group_name = chat.title if chat.type != 'private' else 'Private Chat'
        
        message = (
            f"👤 *User Activity*\n\n"
            f"**User:** {user.first_name} (@{user.username if user.username else 'N/A'}) - {user.id}\n"
            f"**Group:** {group_name}\n"
            f"**Group ID:** {chat.id}\n"
            f"**Activity:** {activity}\n"
            f"**Time:** {update.message.date if update.message else 'N/A'}"
        )
        await send_log_to_channel(context, message, "USER ACTIVITY")
    except Exception as e:
        logger.error(f"Error logging user activity: {e}")

async def log_error(context: ContextTypes.DEFAULT_TYPE, error: str, update: Update = None):
    """Log errors to channel"""
    try:
        error_info = ""
        if update:
            user = update.effective_user
            chat = update.effective_chat
            group_name = chat.title if chat and chat.type != 'private' else 'Private Chat'
            error_info = (
                f"\n**User:** {user.first_name if user else 'Unknown'} (@{user.username if user and user.username else 'N/A'}) - {user.id if user else 'N/A'}\n"
                f"**Group:** {group_name}\n"
                f"**Group ID:** {chat.id if chat else 'N/A'}"
            )
        
        message = (
            f"❌ *Error Occurred*\n\n"
            f"**Error:** `{error}`"
            f"{error_info}"
        )
        await send_log_to_channel(context, message, "ERROR")
    except Exception as e:
        logger.error(f"Error logging error: {e}")

async def log_admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE, action: str, target_group: str = ""):
    """Log admin actions"""
    try:
        user = update.effective_user
        chat = update.effective_chat
        
        group_info = f"**Target Group:** {target_group}\n" if target_group else ""
        
        message = (
            f"⚡ *Admin Action*\n\n"
            f"**Admin:** {user.first_name} (@{user.username if user.username else 'N/A'}) - {user.id}\n"
            f"**Action:** {action}\n"
            f"{group_info}"
            f"**Time:** {update.message.date if update.message else 'N/A'}"
        )
        await send_log_to_channel(context, message, "ADMIN ACTION")
    except Exception as e:
        logger.error(f"Error logging admin action: {e}")

async def log_multi_group_activity(activity: str, groups_count: int, active_quizzes: int):
    """Log multi-group activity"""
    try:
        message = (
            f"🌐 *Multi-Group Activity*\n\n"
            f"**Activity:** {activity}\n"
            f"**Total Groups:** {groups_count}\n"
            f"**Active Quizzes:** {active_quizzes}\n"
            f"**Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        # We need to get context from somewhere, so this will be called from main.py with context
        # This function signature will be updated when called
    except Exception as e:
        logger.error(f"Error logging multi-group activity: {e}")
