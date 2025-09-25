# upsc.py
import logging
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Poll
from telegram.ext import ContextTypes
from telegram.error import BadRequest, Forbidden

logger = logging.getLogger(__name__)

# UPSC Subjects and topics
upsc_subjects = {
    "History": ["Ancient History", "Medieval History", "Modern History", "World History", "Art & Culture"],
    "Geography": ["Physical Geography", "Human Geography", "Indian Geography", "World Geography", "Environmental Geography"],
    "Polity": ["Indian Constitution", "Political System", "Governance", "Public Policy", "International Relations"],
    "Economy": ["Indian Economy", "Economic Development", "Budget & Planning", "International Economics", "Agriculture & Industry"],
    "Science_Tech": ["Science & Technology", "IT & Computers", "Space Technology", "Biotechnology", "Defence Technology"],
    "Environment": ["Ecology", "Biodiversity", "Climate Change", "Environmental Policies", "Conservation"],
    "Current_Affairs": ["National Events", "International Events", "Government Schemes", "Awards & Honors", "Sports"]
}

upsc_fallback_questions = {
    "History": [
        {
            "question": "Who was the first Governor-General of independent India?",
            "options": ["Lord Mountbatten", "C. Rajagopalachari", "Jawaharlal Nehru", "Rajendra Prasad"],
            "correct_answer": 0,
            "explanation": "Lord Mountbatten served as the first Governor-General of independent India from 1947 to 1948."
        },
        {
            "question": "The Indus Valley Civilization was discovered in which year?",
            "options": ["1921", "1901", "1931", "1941"],
            "correct_answer": 0,
            "explanation": "The Indus Valley Civilization was discovered in 1921 by Dayaram Sahni at Harappa."
        }
    ],
    "Geography": [
        {
            "question": "Which is the longest river in India?",
            "options": ["Ganga", "Yamuna", "Brahmaputra", "Godavari"],
            "correct_answer": 0,
            "explanation": "The Ganga is the longest river in India with a length of 2,525 km."
        }
    ],
    "Polity": [
        {
            "question": "How many fundamental rights are there in the Indian Constitution?",
            "options": ["6", "7", "5", "8"],
            "correct_answer": 0,
            "explanation": "There are 6 fundamental rights in the Indian Constitution."
        }
    ],
    "Economy": [
        {
            "question": "What is the currency of India?",
            "options": ["Indian Rupee", "Taka", "Rupiah", "Yuan"],
            "correct_answer": 0,
            "explanation": "The Indian Rupee (INR) is the official currency of India."
        }
    ],
    "Science_Tech": [
        {
            "question": "Which Indian mission was launched to Mars?",
            "options": ["Mangalyaan", "Chandrayaan", "Aryabhata", "Bhaskara"],
            "correct_answer": 0,
            "explanation": "Mangalyaan (Mars Orbiter Mission) was India's first interplanetary mission."
        }
    ],
    "Environment": [
        {
            "question": "Which is the first national park established in India?",
            "options": ["Jim Corbett National Park", "Kaziranga National Park", "Gir National Park", "Sunderbans National Park"],
            "correct_answer": 0,
            "explanation": "Jim Corbett National Park was established in 1936 as Hailey National Park."
        }
    ],
    "Current_Affairs": [
        {
            "question": "Who is the current President of India?",
            "options": ["Droupadi Murmu", "Ram Nath Kovind", "Pratibha Patil", "A.P.J. Abdul Kalam"],
            "correct_answer": 0,
            "explanation": "Droupadi Murmu is the 15th and current President of India since 2022."
        }
    ]
}

async def start_upsc_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start UPSC quiz by asking for subject."""
    query = update.callback_query
    
    keyboard = [
        [
            InlineKeyboardButton("History", callback_data='upsc_subject_History'),
            InlineKeyboardButton("Geography", callback_data='upsc_subject_Geography'),
        ],
        [
            InlineKeyboardButton("Polity", callback_data='upsc_subject_Polity'),
            InlineKeyboardButton("Economy", callback_data='upsc_subject_Economy'),
        ],
        [
            InlineKeyboardButton("Science & Tech", callback_data='upsc_subject_Science_Tech'),
            InlineKeyboardButton("Environment", callback_data='upsc_subject_Environment'),
        ],
        [
            InlineKeyboardButton("Current Affairs", callback_data='upsc_subject_Current_Affairs'),
        ],
        [InlineKeyboardButton("🔙 Back to Exam Selection", callback_data='exam_back')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "📚 *UPSC CSE Quiz*\n\n"
        "Select a subject for UPSC Civil Services Examination preparation:",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def handle_upsc_subject_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, subject: str):
    """Handle UPSC subject selection and start quiz."""
    query = update.callback_query
    chat_id = query.message.chat_id
    group_name = query.message.chat.title or f"Group {chat_id}"
    
    await query.answer()
    
    # Import group module functions
    from group import group_quizzes, active_group_quizzes, user_scores, poll_answers
    from group import is_group_admin, send_leaderboard
    
    # Check if user is admin
    if not await is_group_admin(update, context):
        await query.edit_message_text("❌ Only group admins can start quizzes!")
        return
    
    # Check if quiz already running
    if chat_id in group_quizzes and group_quizzes[chat_id].get('active', False):
        await query.edit_message_text("⚠️ A quiz is already running in this group! Use /stop to stop it first.")
        return
    
    # Initialize UPSC quiz
    group_quizzes[chat_id] = {
        'exam_type': 'UPSC CSE',
        'subject': subject,
        'questions': [],
        'current_question': 0,
        'active': True,
        'poll_ids': [],
        'started_by': update.effective_user.id,
        'group_name': group_name
    }
    
    # Add to active quizzes
    active_group_quizzes.add(chat_id)
    
    await query.edit_message_text(text=f"🔄 Generating UPSC {subject} quiz...")
    
    # Generate UPSC questions
    quiz = await generate_upsc_questions(subject, "advanced", 20)
    
    if quiz:
        group_quizzes[chat_id]['questions'] = quiz
        
        # Log quiz start
        try:
            import log
            await log.log_group_quiz_started(update, context, f"UPSC {subject}", group_name)
            await log.log_admin_action(update, context, f"Started UPSC {subject} quiz", group_name)
        except ImportError:
            pass
        
        # Start posting questions every 30 seconds
        context.job_queue.run_repeating(
            post_upsc_question, 
            interval=30, 
            first=1, 
            data=chat_id, 
            name=str(chat_id)
        )
        await query.edit_message_text(
            text=f"✅ **UPSC {subject} Quiz Started!**\n\n"
                 f"• UPSC-level questions will be posted every 30 seconds\n"
                 f"• Each poll stays open for 25 seconds\n"
                 f"• Use /stop to end quiz early\n"
                 f"• Leaderboard at the end!",
            parse_mode='Markdown'
        )
    else:
        # Use fallback questions
        if subject in upsc_fallback_questions:
            questions = []
            for i in range(20):
                base_q = upsc_fallback_questions[subject][i % len(upsc_fallback_questions[subject])]
                new_q = base_q.copy()
                new_q['question'] = f"{i+1}. {base_q['question']}"
                questions.append(new_q)
            
            group_quizzes[chat_id]['questions'] = questions
            
            # Log quiz start
            try:
                import log
                await log.log_group_quiz_started(update, context, f"UPSC {subject}", group_name)
                await log.log_admin_action(update, context, f"Started UPSC {subject} quiz (Fallback)", group_name)
            except ImportError:
                pass
            
            # Start posting questions
            context.job_queue.run_repeating(
                post_upsc_question, 
                interval=30, 
                first=1, 
                data=chat_id, 
                name=str(chat_id)
            )
            await query.edit_message_text(
                text=f"✅ **UPSC {subject} Quiz Started!**\n\n"
                     f"• UPSC-level questions will be posted every 30 seconds\n"
                     f"• Each poll stays open for 25 seconds\n"
                     f"• Use /stop to end quiz early\n"
                     f"• Leaderboard at the end!",
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text(
                text="❌ Sorry, I couldn't generate UPSC questions right now. Please try again later."
            )

async def post_upsc_question(context: ContextTypes.DEFAULT_TYPE):
    """Post UPSC question as poll to group."""
    from group import group_quizzes, active_group_quizzes, user_scores, poll_answers
    import log
    
    chat_id = context.job.data
    
    if chat_id not in group_quizzes or not group_quizzes[chat_id]['active']:
        if chat_id in active_group_quizzes:
            active_group_quizzes.remove(chat_id)
        context.job.schedule_removal()
        return
    
    quiz_data = group_quizzes[chat_id]
    current_index = quiz_data['current_question']
    
    if current_index >= len(quiz_data['questions']):
        # End of quiz
        if chat_id in active_group_quizzes:
            active_group_quizzes.remove(chat_id)
        context.job.schedule_removal()
        
        await context.bot.send_message(
            chat_id=chat_id,
            text="🎉 UPSC Quiz completed! Use /quiz to start a new one."
        )
        
        # Send leaderboard
        from group import send_leaderboard
        await send_leaderboard(context, chat_id, quiz_data['group_name'])
        
        # Log completion
        try:
            from telegram import Update
            class MinimalUpdate:
                def __init__(self, chat_id, user_id):
                    self.effective_chat = type('Chat', (), {'id': chat_id, 'title': quiz_data['group_name']})()
                    self.effective_user = type('User', (), {'id': user_id, 'first_name': 'System', 'username': None})()
            
            minimal_update = MinimalUpdate(chat_id, quiz_data['started_by'])
            await log.log_quiz_stopped(minimal_update, context, quiz_data['group_name'], chat_id, user_scores.get(chat_id, {}))
        except ImportError:
            pass
        
        # Clean up
        if chat_id in group_quizzes:
            del group_quizzes[chat_id]
        return
    
    question = quiz_data['questions'][current_index]
    
    try:
        poll_question = f"🎯 UPSC {current_index + 1}/{len(quiz_data['questions'])}: {question['question']}"
        poll_options = question['options']
        
        message = await context.bot.send_poll(
            chat_id=chat_id,
            question=poll_question,
            options=poll_options,
            type=Poll.QUIZ,
            correct_option_id=question['correct_answer'],
            is_anonymous=False,
            open_period=25
        )
        
        # Store poll info
        poll_id = message.poll.id
        quiz_data['poll_ids'].append(poll_id)
        poll_answers[poll_id] = {
            'chat_id': chat_id,
            'question_index': current_index,
            'correct': False,
            'explanation': question.get('explanation', '')
        }
        
        quiz_data['current_question'] += 1
        
    except (BadRequest, Forbidden) as e:
        logger.error(f"Error sending UPSC poll to group {chat_id}: {e}")
        quiz_data['current_question'] += 1

async def generate_upsc_questions(subject: str, difficulty: str, num_questions: int = 20):
    """Generate UPSC-level questions using Perplexity AI."""
    try:
        topic = random.choice(upsc_subjects[subject])
        
        url = "https://api.perplexity.ai/chat/completions"
        
        prompt = f"""
        Create {num_questions} UPSC Civil Services Examination level multiple choice questions on {subject}.
        Focus on: {topic}
        Difficulty: {difficulty} (UPSC CSE level)
        
        Question requirements:
        - UPSC CSE examination pattern
        - Current affairs relevance where applicable
        - Analytical and conceptual understanding
        - Options should be close and challenging
        
        For each question, provide:
        1. Question text (challenging, UPSC level)
        2. Four options (labeled a, b, c, d)
        3. Correct answer (0-indexed)
        4. Brief explanation with UPSC context
        
        Return JSON array:
        [
          {{
            "question": "question text",
            "options": ["option1", "option2", "option3", "option4"],
            "correct_answer": 0,
            "explanation": "UPSC-relevant explanation"
          }}
        ]
        """
        
        from main import PERPLEXITY_API_KEY
        headers = {
            "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "sonar",
            "messages": [
                {"role": "system", "content": "You are an expert UPSC CSE examination coach creating high-quality questions."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 4000,
            "temperature": 0.7
        }
        
        import requests
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            response_data = response.json()
            content = response_data['choices'][0]['message']['content']
            
            import json
            try:
                start_idx = content.find('[')
                end_idx = content.rfind(']') + 1
                json_str = content[start_idx:end_idx]
                quiz_data = json.loads(json_str)
                return quiz_data
            except (json.JSONDecodeError, KeyError, IndexError):
                logger.error("Failed to parse JSON from Perplexity for UPSC")
                return None
        else:
            logger.error(f"Perplexity API error for UPSC: {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"Error generating UPSC questions: {e}")
        return None

async def handle_exam_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle back button to exam selection."""
    query = update.callback_query
    await query.answer()
    
    # Show exam selection again
    keyboard = [
        [InlineKeyboardButton("12th Board Commerce", callback_data='exam_12th')],
        [InlineKeyboardButton("UPSC CSE", callback_data='exam_upsc')],
        [InlineKeyboardButton("❌ Cancel", callback_data='group_cancel')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "📝 *Select Examination Type:*\n\n"
        "Choose the type of quiz you want to start:",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )
