# personal.py
import logging
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

# Store user data
user_quizzes = {}

# Commerce subjects instead of Science
fallback_questions = {
    "Accountancy": [
        {
            "question": "What is the basic accounting equation?",
            "options": ["Assets = Liabilities + Equity", "Assets = Liabilities - Equity", "Assets = Revenue - Expenses", "Assets = Income - Expenses"],
            "correct_answer": 0,
            "explanation": "The basic accounting equation is Assets = Liabilities + Equity, which forms the foundation of double-entry bookkeeping."
        },
        {
            "question": "Which financial statement shows a company's financial position at a specific point in time?",
            "options": ["Balance Sheet", "Income Statement", "Cash Flow Statement", "Statement of Retained Earnings"],
            "correct_answer": 0,
            "explanation": "The Balance Sheet shows a company's assets, liabilities, and equity at a specific point in time."
        }
    ],
    "Business Studies": [
        {
            "question": "What is the first step in the planning process?",
            "options": ["Setting objectives", "Identifying alternatives", "Developing premises", "Evaluating alternatives"],
            "correct_answer": 0,
            "explanation": "Setting objectives is the first step in the planning process as it provides direction for all other steps."
        }
    ],
    "Economics": [
        {
            "question": "What does GDP stand for?",
            "options": ["Gross Domestic Product", "Gross Development Product", "General Domestic Product", "General Development Product"],
            "correct_answer": 0,
            "explanation": "GDP stands for Gross Domestic Product, which is the total value of all goods and services produced within a country in a given period."
        }
    ],
    "Mathematics": [
        {
            "question": "What is the derivative of x²?",
            "options": ["x", "2x", "2", "x²"],
            "correct_answer": 1,
            "explanation": "The derivative of x² is 2x, according to the power rule of differentiation."
        }
    ],
    "English": [
        {
            "question": "Which of these is a preposition?",
            "options": ["run", "beautiful", "under", "quickly"],
            "correct_answer": 2,
            "explanation": "A preposition shows the relationship between a noun or pronoun and other words in a sentence. 'Under' is a preposition."
        }
    ],
    "Information Practices": [
        {
            "question": "What does SQL stand for?",
            "options": ["Structured Query Language", "Simple Query Language", "System Query Language", "Standard Query Language"],
            "correct_answer": 0,
            "explanation": "SQL stands for Structured Query Language, used for managing and manipulating relational databases."
        }
    ]
}

# Different topics for each subject to ensure variety
quiz_topics = {
    "Accountancy": ["Accounting Principles", "Journal Entries", "Financial Statements", "Ratio Analysis", "Partnership Accounts", "Company Accounts"],
    "Business Studies": ["Management Principles", "Marketing", "Finance", "Human Resources", "Business Environment", "Planning"],
    "Economics": ["Microeconomics", "Macroeconomics", "Demand and Supply", "Market Structures", "National Income", "Government Budget"],
    "Mathematics": ["Calculus", "Algebra", "Probability", "Statistics", "Matrices", "Linear Programming"],
    "English": ["Grammar", "Vocabulary", "Comprehension", "Writing Skills", "Literature", "Poetry"],
    "Information Practices": ["Database Concepts", "SQL", "Python Programming", "Networking", "Web Development", "Data Visualization"]
}

# Start command with welcome message and buttons
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message with main menu buttons."""
    keyboard = [
        [InlineKeyboardButton("➕ Add me in Group", url="https://t.me/Quizonomics_bot?startgroup=true")],
        [InlineKeyboardButton("❓ Help", callback_data='main_help')],
        [InlineKeyboardButton("📊 Bot Status", callback_data='main_status')],
        [InlineKeyboardButton("👤 Owner", url="https://t.me/komresu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = (
        "👋 Welcome to the *Enhanced Quiz Bot!*\n\n"
        "🌟 *New Features:*\n"
        "• 12th Board Commerce & UPSC CSE Exams\n"
        "• Admin-only quiz control\n"
        "• Multi-group support\n"
        "• Real-time logging\n\n"
        "I'm designed to provide quizzes in groups only with admin privileges. "
        "Add me to your group and make me admin to start quizzing!\n\n"
        "Select an option below:"
    )
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, action: str):
    """Handle main menu button clicks."""
    query = update.callback_query
    await query.answer()
    
    if action == 'add_group':
        # Add to group information
        bot_username = context.bot.username
        text = (
            f"📋 *How to Add Bot to Group:*\n\n"
            f"1. Go to your group's settings\n"
            f"2. Select 'Add members'\n"
            f"3. Search for @{bot_username}\n"
            f"4. Add me to the group\n"
            f"5. *Important:* Make me an *admin* with post permissions\n\n"
            f"⚡ I'll then be available to provide quizzes for all group members with admin-only control!"
        )
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data='main_back')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode='Markdown')
    
    elif action == 'help':
        # Help information
        text = (
            "🤖 *Enhanced Quiz Bot Help*\n\n"
            "🌟 *Available Examinations:*\n"
            "• 12th Board Commerce\n"
            "• UPSC Civil Services (CSE)\n\n"
            "*New Security Features:*\n"
            "• Admin-only quiz control\n"
            "• Multi-group support\n"
            "• Real-time activity logging\n\n"
            "*How to use:*\n"
            "• Add me to your group using the 'Add me in Group' button\n"
            "• Make me admin in your group\n"
            "• Use /quiz in the group (Admin only)\n"
            "• Select examination type (12th Board/UPSC)\n"
            "• Choose subject and start quiz\n"
            "• Answer questions and track scores\n\n"
            "*Commands:*\n"
            "/quiz - Start a new quiz in a group (Admin only)\n"
            "/stop - Stop ongoing quiz (Admin only)\n"
            "/help - Show this help message\n"
            "/status - Check bot status\n\n"
            "⚡ *Note:* I work in multiple groups simultaneously with enhanced security."
        )
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data='main_back')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode='Markdown')
    
    elif action == 'status':
        # Status information
        try:
            from group import get_active_quizzes_count
            active_quizzes = get_active_quizzes_count()
        except ImportError:
            active_quizzes = 0
            
        text = (
            "📊 *Bot Status Report*\n\n"
            f"• Active quizzes: {active_quizzes}\n"
            f"• Multi-group support: ✅ Enabled\n"
            f"• Admin-only mode: ✅ Enabled\n"
            f"• Available Exams: ✅ 12th Board & UPSC CSE\n"
            f"• Logging system: ✅ Active\n"
            f"• Security: ✅ Enhanced\n\n"
            "🤖 Bot is running smoothly with all enhanced features!"
        )
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data='main_back')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode='Markdown')
    
    elif action == 'owner':
        # Owner information with direct link
        text = (
            "👤 *Bot Owner Information:*\n\n"
            "Name: Quiz Bot Administrator\n"
            "Contact: @komresu\n\n"
            "For questions, suggestions, or support regarding the enhanced features, please contact the owner directly."
        )
        keyboard = [
            [InlineKeyboardButton("📞 Contact Owner", url="https://t.me/komresu")],
            [InlineKeyboardButton("🔙 Back", callback_data='main_back')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode='Markdown')
    
    elif action == 'back':
        # Return to main menu
        keyboard = [
            [InlineKeyboardButton("➕ Add me in Group", url="https://t.me/Quizonomics_bot?startgroup=true")],
            [InlineKeyboardButton("❓ Help", callback_data='main_help')],
            [InlineKeyboardButton("📊 Bot Status", callback_data='main_status')],
            [InlineKeyboardButton("👤 Owner", url="https://t.me/komresu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text="*Main Menu:*",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all callback queries."""
    query = update.callback_query
    data = query.data
    
    if data.startswith('main_'):
        action = data[5:]
        await handle_main_menu(update, context, action)
    
    elif data.startswith('exam_'):
        exam = data[5:]
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data='main_back')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text=f"{exam.upper()} exam preparation is fully supported! Use /quiz in a group to start.",
            reply_markup=reply_markup
        )
