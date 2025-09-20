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

# Import group and personal modules
import group
import personal

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    user = update.effective_user
    chat_type = update.effective_chat.type
    
    if chat_type == "private":
        # Use the new start command with buttons from personal.py
        await personal.start_command(update, context)
    else:
        # Group chat
        await update.message.reply_text(
            "👋 Hello everyone! Welcome to the 12th Grade Commerce Quiz Bot.\n\n"
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
        # Private chat - inform user that quizzes are only for groups
        await update.message.reply_text(
            "❌ Quizzes are only available in groups!\n\n"
            "Please add me to a group using the 'Add me in Group' button from the main menu, "
            "then use /quiz in the group to start quizzes."
        )
    else:
        # Group chat - proceed with group quiz
        await group.group_quiz_command(update, context)

async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stop command for group quizzes."""
    await group.stop_command(update, context)

async def health_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Health check endpoint for UptimeRobot"""
    await update.message.reply_text("✅ Bot is active and running!")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks."""
    query = update.callback_query
    data = query.data
    
    # Handle main menu buttons
    if data.startswith('main_'):
        action = data[5:]
        await personal.handle_main_menu(update, context, action)
    
    # Handle category selection (for backward compatibility)
    elif data.startswith('category_'):
        category = data[9:]
        if category == 'back':
            await personal.handle_main_menu(update, context, 'back')
        else:
            # Inform user that quizzes are group-only
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
    
    # Handle subject selection (for backward compatibility)
    elif data.startswith('subject_'):
        # Inform user that quizzes are group-only
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
    
    # Handle group subject selection
    elif data.startswith('group_subject_'):
        subject = data.split('_', 2)[2]
        await group.handle_group_subject_selection(update, context, subject)
    
    # Handle difficulty selection (for backward compatibility)
    elif data.startswith('diff_'):
        # Inform user that quizzes are group-only
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
    
    # Handle answer selection (for backward compatibility)
    elif data.startswith('answer_'):
        # Inform user that quizzes are group-only
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
    
    # Handle continue button (for backward compatibility)
    elif data == 'continue':
        # Inform user that quizzes are group-only
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
    
    # Handle new quiz button
    elif data == 'new_quiz':
        await quiz_command(update, context)
    
    # Handle exam buttons (for backward compatibility)
    elif data.startswith('exam_'):
        # Inform user that quizzes are group-only
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
    # Check if token is available
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN environment variable is not set!")
        return
    
    # Create the Application and pass it your bot's token
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("quiz", quiz_command))
    application.add_handler(CommandHandler("stop", stop_command))
    application.add_handler(CommandHandler("subjects", subjects_command))
    application.add_handler(CommandHandler("health", health_check))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(PollAnswerHandler(group.handle_poll_answer))

    # Start the Bot
    logger.info("Commerce Quiz Bot is running with Perplexity AI...")
    print("Bot is starting...")
    application.run_polling()

if __name__ == '__main__':
    main()
