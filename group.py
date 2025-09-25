# group.py
import logging
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Poll
from telegram.ext import ContextTypes
from telegram.error import BadRequest, Forbidden

logger = logging.getLogger(__name__)

# Store group quizzes and user scores with multi-group support
group_quizzes = {}
poll_answers = {}
user_scores = {}
active_group_quizzes = set()  # Track active quizzes across groups

# Admin permissions check
async def is_group_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check if the user is admin in the group"""
    try:
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        
        # Get chat member information
        chat_member = await context.bot.get_chat_member(chat_id, user_id)
        
        # Check if user is admin or creator
        return chat_member.status in ['administrator', 'creator']
    except Exception as e:
        logger.error(f"Error checking admin status: {e}")
        return False

async def group_quiz_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start a new group quiz by asking for exam type first."""
    chat_id = update.effective_chat.id
    
    # Check if user is admin
    if not await is_group_admin(update, context):
        await update.message.reply_text("❌ Only group admins can start quizzes!")
        
        # Log unauthorized access attempt
        try:
            import log
            await log.log_user_activity(update, context, "Tried to start quiz without admin rights")
        except ImportError:
            pass
            
        return
    
    # Log user activity
    try:
        import log
        await log.log_user_activity(update, context, "Started quiz selection (Admin)")
    except ImportError:
        pass
    
    if chat_id in group_quizzes and group_quizzes[chat_id].get('active', False):
        await update.message.reply_text("⚠️ A quiz is already running in this group! Use /stop to stop it first.")
        return
        
    # Clear previous user scores for this group
    user_scores[chat_id] = {}
        
    # Ask for exam type first
    keyboard = [
        [InlineKeyboardButton("12th Board Commerce", callback_data='exam_12th')],
        [InlineKeyboardButton("UPSC CSE", callback_data='exam_upsc')],
        [InlineKeyboardButton("❌ Cancel", callback_data='group_cancel')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "📝 *Select Examination Type:*\n\n"
        "Choose the type of quiz you want to start:",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def handle_exam_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, exam_type: str):
    """Handle exam type selection."""
    query = update.callback_query
    await query.answer()
    
    if exam_type == '12th':
        # Show 12th board subjects
        keyboard = [
            [
                InlineKeyboardButton("Accountancy", callback_data='group_subject_Accountancy'),
                InlineKeyboardButton("Business Studies", callback_data='group_subject_Business Studies'),
            ],
            [
                InlineKeyboardButton("Economics", callback_data='group_subject_Economics'),
                InlineKeyboardButton("Mathematics", callback_data='group_subject_Mathematics'),
            ],
            [
                InlineKeyboardButton("English", callback_data='group_subject_English'),
                InlineKeyboardButton("Info Practices", callback_data='group_subject_Information Practices'),
            ],
            [InlineKeyboardButton("🔙 Back to Exam Selection", callback_data='exam_back')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text="📚 *12th Board Commerce Quiz*\n\nSelect a subject:",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    elif exam_type == 'upsc':
        # Import and use UPSC module
        try:
            import upsc
            await upsc.start_upsc_quiz(update, context)
        except ImportError as e:
            logger.error(f"UPSC module import error: {e}")
            await query.edit_message_text(
                text="❌ UPSC module not available. Please contact administrator."
            )
    
    elif exam_type == 'back':
        # Go back to exam selection
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

async def handle_group_subject_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, subject: str):
    """Handle group subject selection."""
    query = update.callback_query
    chat_id = query.message.chat_id
    group_name = query.message.chat.title or f"Group {chat_id}"
    
    await query.answer()
    
    # Check if user is admin
    if not await is_group_admin(update, context):
        await query.edit_message_text("❌ Only group admins can start quizzes!")
        return
    
    # Initialize group quiz
    group_quizzes[chat_id] = {
        'exam_type': '12th Board',
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
    
    await query.edit_message_text(text=f"🔄 Generating {subject} quiz for the group...")
    
    # Generate questions for the group quiz
    quiz = await generate_quiz_with_perplexity(subject, "medium", 20)
    
    if quiz:
        group_quizzes[chat_id]['questions'] = quiz
        
        # Log quiz start
        try:
            import log
            await log.log_group_quiz_started(update, context, subject, group_name)
            await log.log_admin_action(update, context, f"Started {subject} quiz", group_name)
        except ImportError:
            pass
        
        # Start posting questions every 30 seconds
        context.job_queue.run_repeating(
            post_group_question, 
            interval=30, 
            first=1, 
            data=chat_id, 
            name=str(chat_id)
        )
        await query.edit_message_text(
            text=f"✅ **{subject} Quiz Started!**\n\n"
                 f"• Questions will be posted every 30 seconds\n"
                 f"• Each poll stays open for 25 seconds\n"
                 f"• Use /stop to end quiz early\n"
                 f"• Leaderboard at the end!",
            parse_mode='Markdown'
        )
    else:
        # Use fallback questions if API fails
        from personal import fallback_questions
        if subject in fallback_questions:
            # Create questions by repeating and modifying fallback questions
            questions = []
            for i in range(20):
                base_q = fallback_questions[subject][i % len(fallback_questions[subject])]
                new_q = base_q.copy()
                new_q['question'] = f"{i+1}. {base_q['question']}"
                questions.append(new_q)
            
            group_quizzes[chat_id]['questions'] = questions
            
            # Log quiz start with fallback
            try:
                import log
                await log.log_group_quiz_started(update, context, subject, group_name)
                await log.log_admin_action(update, context, f"Started {subject} quiz (Fallback)", group_name)
            except ImportError:
                pass
            
            # Start posting questions every 30 seconds
            context.job_queue.run_repeating(
                post_group_question, 
                interval=30, 
                first=1, 
                data=chat_id, 
                name=str(chat_id)
            )
            await query.edit_message_text(
                text=f"✅ **{subject} Quiz Started!**\n\n"
                     f"• Questions will be posted every 30 seconds\n"
                     f"• Each poll stays open for 25 seconds\n"
                     f"• Use /stop to end quiz early\n"
                     f"• Leaderboard at the end!",
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text(
                text="❌ Sorry, I couldn't generate a quiz right now. Please try again later."
            )

async def handle_group_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle quiz cancellation."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("❌ Quiz setup cancelled.")

async def post_group_question(context: ContextTypes.DEFAULT_TYPE):
    """Post a question as a poll to the group every 30 seconds."""
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
        
        # Send quiz completion message
        await context.bot.send_message(
            chat_id=chat_id,
            text="🎉 Group quiz completed! Use /quiz to start a new one."
        )
        
        # Send leaderboard
        await send_leaderboard(context, chat_id, quiz_data['group_name'])
        
        # Log quiz completion
        try:
            import log
            from telegram import Update
            # Create a minimal update object for logging
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
        # Create poll with the question
        poll_question = f"❓ {current_index + 1}/{len(quiz_data['questions'])}: {question['question']}"
        poll_options = question['options']
        
        # Send the poll
        message = await context.bot.send_poll(
            chat_id=chat_id,
            question=poll_question,
            options=poll_options,
            type=Poll.QUIZ,
            correct_option_id=question['correct_answer'],
            is_anonymous=False,
            open_period=25  # Poll stays open for 25 seconds
        )
        
        # Store poll information
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
        logger.error(f"Error sending poll to group {chat_id}: {e}")
        # Skip this question and continue
        quiz_data['current_question'] += 1

async def handle_poll_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle when a user answers a poll."""
    answer = update.poll_answer
    poll_id = answer.poll_id
    user_id = answer.user.id
    selected_option = answer.option_ids[0] if answer.option_ids else None
    
    if poll_id not in poll_answers:
        return
    
    poll_data = poll_answers[poll_id]
    chat_id = poll_data['chat_id']
    
    if chat_id not in group_quizzes:
        return
    
    quiz_data = group_quizzes[chat_id]
    question_index = poll_data['question_index']
    question = quiz_data['questions'][question_index]
    
    # Check if answer is correct
    if selected_option == question['correct_answer']:
        poll_data['correct'] = True
        
        # Update user score
        if chat_id not in user_scores:
            user_scores[chat_id] = {}
        
        if user_id not in user_scores[chat_id]:
            user_scores[chat_id][user_id] = 0
        
        user_scores[chat_id][user_id] += 1
        
        # 🚫 REMOVED: DM explanation sending
        # Now only score is updated, no DM is sent to user

async def send_leaderboard(context, chat_id, group_name):
    """Send the leaderboard with all participants' scores."""
    if chat_id not in user_scores or not user_scores[chat_id]:
        await context.bot.send_message(
            chat_id=chat_id,
            text="📊 No one participated in this quiz. 😢"
        )
        return
    
    # Get user names and scores
    leaderboard_data = []
    for user_id, score in user_scores[chat_id].items():
        try:
            user = await context.bot.get_chat_member(chat_id, user_id)
            user_name = user.user.first_name
            if user.user.last_name:
                user_name += f" {user.user.last_name}"
            if user.user.username:
                user_name += f" (@{user.user.username})"
            leaderboard_data.append((user_name, score))
        except Exception as e:
            logger.error(f"Could not get user info: {e}")
            leaderboard_data.append((f"User {user_id}", score))
    
    # Sort by score (descending)
    leaderboard_data.sort(key=lambda x: x[1], reverse=True)
    
    # Create leaderboard message
    leaderboard_text = f"🏆 *{group_name} - Quiz Leaderboard* 🏆\n\n"
    for i, (user_name, score) in enumerate(leaderboard_data):
        medal = ""
        if i == 0:
            medal = "🥇 "
        elif i == 1:
            medal = "🥈 "
        elif i == 2:
            medal = "🥉 "
        
        leaderboard_text += f"{medal}{i+1}. {user_name}: {score} points\n"
    
    leaderboard_text += f"\n📈 Total Participants: {len(leaderboard_data)}"
    
    await context.bot.send_message(
        chat_id=chat_id,
        text=leaderboard_text,
        parse_mode='Markdown'
    )

async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stop an ongoing group quiz - Admin only."""
    chat_id = update.effective_chat.id
    
    # Check if user is admin
    if not await is_group_admin(update, context):
        await update.message.reply_text("❌ Only group admins can stop quizzes!")
        
        # Log unauthorized access attempt
        try:
            import log
            await log.log_user_activity(update, context, "Tried to stop quiz without admin rights")
        except ImportError:
            pass
            
        return
    
    if chat_id not in group_quizzes or not group_quizzes[chat_id].get('active', False):
        await update.message.reply_text("❌ No active quiz found in this group!")
        return
    
    # Get group name for logging
    group_name = update.effective_chat.title or f"Group {chat_id}"
    
    # Stop the quiz
    group_quizzes[chat_id]['active'] = False
    
    # Remove from active quizzes set
    if chat_id in active_group_quizzes:
        active_group_quizzes.remove(chat_id)
    
    # Remove the job from job queue
    current_jobs = context.job_queue.get_jobs_by_name(str(chat_id))
    for job in current_jobs:
        job.schedule_removal()
    
    # Get scores for logging
    scores = user_scores.get(chat_id, {})
    
    # Send leaderboard
    await send_leaderboard(context, chat_id, group_name)
    
    # Log quiz stop
    try:
        import log
        await log.log_quiz_stopped(update, context, group_name, chat_id, scores)
        await log.log_admin_action(update, context, "Stopped quiz", group_name)
    except ImportError:
        pass
    
    # Clean up
    if chat_id in group_quizzes:
        del group_quizzes[chat_id]
    
    await update.message.reply_text("✅ Quiz stopped successfully! Leaderboard has been posted.")

async def generate_quiz_with_perplexity(subject: str, difficulty: str, num_questions: int = 20):
    """Generate quiz questions using Perplexity AI API."""
    try:
        from personal import quiz_topics
        # Select a random topic from the available topics for this subject
        topic = random.choice(quiz_topics[subject])
        
        # Perplexity API endpoint
        url = "https://api.perplexity.ai/chat/completions"
        
        # Prepare the prompt
        prompt = f"""
        Create a {num_questions}-question multiple choice quiz on {subject} for 12th grade Commerce students.
        Focus on the topic: {topic}
        Difficulty level: {difficulty}.
        For each question, provide:
        1. The question text
        2. Four options (labeled a, b, c, d)
        3. The correct answer (0-indexed, e.g., 0 for first option)
        4. A brief explanation of the correct answer
        
        Return the response as a JSON array with the following structure:
        [
          {{
            "question": "question text",
            "options": ["option1", "option2", "option3", "option4"],
            "correct_answer": 0,
            "explanation": "brief explanation"
          }}
        ]
        """
        
        # Headers for the API request
        from main import PERPLEXITY_API_KEY
        headers = {
            "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Payload for the API request
        payload = {
            "model": "sonar",
            "messages": [
                {"role": "system", "content": "You are a helpful educational assistant that creates quiz questions for 12th grade Commerce students."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 4000,
            "temperature": 0.7
        }
        
        # Make the API request
        import requests
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            # Parse the response
            response_data = response.json()
            content = response_data['choices'][0]['message']['content']
            
            # Extract JSON from the response
            import json
            try:
                # Try to find JSON array in the response
                start_idx = content.find('[')
                end_idx = content.rfind(']') + 1
                json_str = content[start_idx:end_idx]
                quiz_data = json.loads(json_str)
                return quiz_data
            except (json.JSONDecodeError
