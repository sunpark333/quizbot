import logging
import random
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext

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
async def start_command(update: Update, context: CallbackContext):
    """Send welcome message with main menu buttons."""
    keyboard = [
        [InlineKeyboardButton("➕ Add me in Group", url="https://t.me/Quizonomics_bot?startgroup=true")],
        [InlineKeyboardButton("❓ Help", callback_data='main_help')],
        [InlineKeyboardButton("👤 Owner", url="https://t.me/komresu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = (
        "👋 Welcome to the Quiz Bot!\n\n"
        "I'm designed to provide quizzes in groups only. "
        "Add me to your group to start quizzing with your friends!\n\n"
        "Select an option below:"
    )
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

async def handle_main_menu(update: Update, context: CallbackContext, action: str):
    """Handle main menu button clicks."""
    query = update.callback_query
    await query.answer()
    
    if action == 'add_group':
        # Add to group information
        bot_username = context.bot.username
        text = (
            f"To add me to a group:\n\n"
            f"1. Go to your group's settings\n"
            f"2. Select 'Add members'\n"
            f"3. Search for @{bot_username}\n"
            f"4. Add me to the group\n\n"
            f"I'll then be available to provide quizzes for all group members!"
        )
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data='main_back')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=text, reply_markup=reply_markup)
    
    elif action == 'help':
        # Help information
        text = (
            "🤖 How to use this bot:\n\n"
            "• Add me to your group using the 'Add me in Group' button\n"
            "• Use /quiz in the group to start a quiz\n"
            "• Answer questions and get explanations\n"
            "• Track your progress and scores\n\n"
            "Commands:\n"
            "/quiz - Start a new quiz in a group\n"
            "/help - Show this help message\n\n"
            "Note: I only work in groups, not in private chats."
        )
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data='main_back')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=text, reply_markup=reply_markup)
    
    elif action == 'owner':
        # Owner information with direct link
        text = (
            "👤 Bot Owner Information:\n\n"
            "Name: Quiz Bot Administrator\n"
            "Contact: @quizadmin\n\n"
            "For questions, suggestions, or support, please contact the owner directly."
        )
        keyboard = [
            [InlineKeyboardButton("📞 Contact Owner", url="https://t.me/quizadmin")],
            [InlineKeyboardButton("🔙 Back", callback_data='main_back')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=text, reply_markup=reply_markup)
    
    elif action == 'back':
        # Return to main menu
        keyboard = [
            [InlineKeyboardButton("➕ Add me in Group", url="https://t.me/your_bot_username?startgroup=true")],
            [InlineKeyboardButton("❓ Help", callback_data='main_help')],
            [InlineKeyboardButton("👤 Owner", url="https://t.me/quizadmin")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text="Main menu:",
            reply_markup=reply_markup
        )

async def handle_callback_query(update: Update, context: CallbackContext):
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
            text=f"{exam.upper()} exam preparation is coming soon! Check back later for updates.",
            reply_markup=reply_markup
        )
