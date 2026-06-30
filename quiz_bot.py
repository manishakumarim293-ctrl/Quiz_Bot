import os
import sqlite3
import json
import logging
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    filters, ContextTypes, ConversationHandler, CallbackQueryHandler, PollAnswerHandler
)

# Enable Logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID")) if os.getenv("OWNER_ID") else None

DB_FILE = "quiz_bot.db"

# Global dictionary for active group games memory
GROUP_GAMES = {}

# Conversation flow states
TITLE, DESCRIPTION, QUESTIONS, TIMER = range(4)
EDIT_TITLE, EDIT_DESC, EDIT_TIMER = range(4, 7)

def escape_markdown(text):
    """Escape special characters for Telegram Markdown"""
    if not text:
        return text
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text

def format_time(seconds):
    """Convert seconds to min:sec format (e.g., 1m 45s)"""
    if seconds < 60:
        return f"{int(seconds)}s"
    minutes = int(seconds) // 60
    secs = int(seconds) % 60
    return f"{minutes}m {secs}s"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quizzes (
            quiz_id INTEGER PRIMARY KEY AUTOINCREMENT,
            creator_id INTEGER,
            title TEXT,
            description TEXT,
            timer INTEGER DEFAULT 30
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_id INTEGER,
            question_text TEXT,
            options TEXT,
            correct_answer TEXT,
            explanation TEXT,
            pre_message TEXT,
            FOREIGN KEY(quiz_id) REFERENCES quizzes(quiz_id)
        )
    """)
    conn.commit()
    conn.close()

init_db()
    async def new_quiz_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Check if interaction is via callback button or command
    msg_obj = update.callback_query.message if update.callback_query else update.message
    user_id = update.callback_query.from_user.id if update.callback_query else update.message.from_user.id
    
    if update.callback_query:
        await update.callback_query.answer()
        
    await msg_obj.reply_text(
        "Let's create a new quiz. First, send me the title of your quiz (e.g., 'Aptitude Test' or '10 questions about bears').",
        reply_markup=ReplyKeyboardRemove()
    )
    context.user_data["quiz_build"] = {"title": "", "description": "", "questions": []}
    context.user_data["quiz_build_creator_id"] = user_id
    return TITLE

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    # Handle direct deep-linking tracking code
    if args and len(args) > 0 and args[0].startswith("quiz_"):
        quiz_id = args[0].split("_")[1]
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT title, description, timer FROM quizzes WHERE quiz_id = ?", (quiz_id,))
        quiz_data = cursor.fetchone()
        cursor.execute("SELECT COUNT(*) FROM questions WHERE quiz_id = ?", (quiz_id,))
        total_q = cursor.fetchone()
        conn.close()
        
        if not quiz_data:
            await update.message.reply_text("❌ Quiz data not found.")
            return

        title, desc, timer = quiz_data
        time_disp = f"{timer} sec" if timer < 60 else f"{timer // 60} min"
        
        init_text = (
            f"🏁 **Quiz Setup Ready!**\n\n"
            f"📚 **Title:** {escape_markdown(title)}\n"
            f"ℹ️ **Description:** {escape_markdown(desc) if desc else 'No description'}\n"
            f"🙋‍♂️ **Questions:** {total_q[0]}\n"
            f"⏱ **Time per question:** {time_disp}\n\n"
            "⚠️ *Quiz shuru karne ke liye kam se kam 2 users ka Ready hona zaroori hai!*"
        )
        
        keyboard = [[InlineKeyboardButton("I am ready! 🎯 (0/2)", callback_data=f"ready_{quiz_id}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(init_text, reply_markup=reply_markup, parse_mode="Markdown")
        return

    # Normal private chat initialization layout
    welcome_text = (
        "👋 **Welcome to Laado Quiz Bot!**\n\n"
        "Niche diye gaye buttons se aap apna naya quiz bana sakte hain ya pehle banaye huye quizzes dekh sakte hain:\n\n"
        "🚀 /newquiz - Naya Quiz banana shuru karein\n"
        "❌ /cancel - Active creation flow cancel karein"
    )
    keyboard = [
        [InlineKeyboardButton("Create New Quiz 🚀", callback_data="btn_newquiz")],
        [InlineKeyboardButton("View My Quizzes 📚", callback_data="btn_viewquizzes")]
    ]
    await update.message.reply_text(welcome_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📖 **Laado Quiz Bot Help Menu**\n\n"
        "Aap is bot se quizzes bana kar apne dosto ke sath groups me realtime khel sakte hain.\n\n"
        "💡 **Available Actions:**"
    )
    keyboard = [
        [InlineKeyboardButton("Create New Quiz 🚀", callback_data="btn_newquiz")],
        [InlineKeyboardButton("View My Quizzes 📚", callback_data="btn_viewquizzes")]
    ]
    await update.message.reply_text(help_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def receive_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["quiz_build"]["title"] = update.message.text
    await update.message.reply_text("Good. Now send me a description of your quiz. This is optional, you can /skip this step.")
    return DESCRIPTION

async def receive_desc(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    context.user_data["quiz_build"]["description"] = "" if text.lower() == "/skip" else text
    await update.message.reply_text(
        f"Good. Your quiz '{context.user_data['quiz_build']['title']}' now has 0 questions. If you made a mistake, send /undo.\n\n"
        "💡 **Sawal jodne ke liye:**\nClick on 📎 (Attachment) -> Select **Poll**.\n"
        "Enable **Quiz Mode**, add 2-7 options, pick the correct one, and tap Create.\n\n"
        "Send /done when finished adding questions.",
        reply_markup=ReplyKeyboardRemove()
    )
    return QUESTIONS

async def receive_poll(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    poll = update.message.poll
    if poll.type != "quiz":
        await update.message.reply_text("❌ Kripya Quiz mode wala poll hi send karein:")
        return QUESTIONS
    if len(poll.options) > 7:
        await update.message.reply_text("❌ Maximum 7 options allowed. Re-send poll:")
        return QUESTIONS

    opts = [o.text for o in poll.options]
    q_data = {
        "text": poll.question, "options": opts, "correct": opts[poll.correct_option_id],
        "explanation": poll.explanation if poll.explanation else "", "pre_message": ""
    }
    context.user_data["quiz_build"]["questions"].append(q_data)
    
    await update.message.reply_text(
        f"✅ Question added! Your quiz now has {len(context.user_data['quiz_build']['questions'])} question(s).\n\n"
        "Send next question or /done to finish."
    )
    return QUESTIONS

async def handle_undo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    quiz = context.user_data.get("quiz_build")
    if quiz and quiz["questions"]:
        quiz["questions"].pop()
        await update.message.reply_text(f"↩️ Last question removed! Quiz now has {len(quiz['questions'])} question(s).\n\nSend next question or /done.")
    else:
        await update.message.reply_text("❌ No questions to remove!")
    return QUESTIONS

async def finish_quiz_creation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    quiz = context.user_data.get("quiz_build", {})
    if not quiz or not quiz.get("questions"):
        await update.message.reply_text("❌ Error: Quiz must have at least 1 question!")
        return QUESTIONS
    
    await update.message.reply_text(
        "⏱️ **Please set a time limit for questions:**\n\n"
        "Type any of these: 15, 30, 40, 60\n\n"
        "Example: Type '30' for 30 seconds per question",
        reply_markup=ReplyKeyboardRemove()
    )
    return TIMER
      async def handle_timer_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    time_map = {"15": 15, "30": 30, "40": 40, "60": 60}
    
    if text not in time_map:
        await update.message.reply_text("❌ Invalid time. Please enter: 15, 30, 40, or 60")
        return TIMER
    
    t_sec = time_map[text]
    quiz = context.user_data.get("quiz_build", {})
    
    if not quiz or not quiz.get("title"):
        await update.message.reply_text("❌ Error: Quiz data missing. Please start over with /newquiz")
        return ConversationHandler.END

    user_id = context.user_data.get("quiz_build_creator_id", update.message.from_user.id)

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO quizzes (creator_id, title, description, timer) VALUES (?, ?, ?, ?)", (user_id, quiz["title"], quiz["description"], t_sec))
    qid = cursor.lastrowid
    for q in quiz["questions"]:
        cursor.execute("INSERT INTO questions (quiz_id, question_text, options, correct_answer, explanation, pre_message) VALUES (?, ?, ?, ?, ?, ?)", 
                       (qid, q["text"], json.dumps(q["options"]), q["correct"], q["explanation"], q["pre_message"]))
    conn.commit()
    conn.close()
    
    context.user_data.pop("quiz_build", None)
    context.user_data.pop("quiz_build_creator_id", None)
    
    await update.message.reply_text("✅ Timer set! Creating your quiz summary...")
    await show_summary_panel_text(update, context, qid)
    return ConversationHandler.END
    async def view_my_quizzes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fetches and displays all quizzes created by the user"""
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT quiz_id, title FROM quizzes WHERE creator_id = ? ORDER BY quiz_id DESC", (user_id,))
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        keyboard = [[InlineKeyboardButton("Create New Quiz 🚀", callback_data="btn_newquiz")]]
        await query.edit_message_text(
            text="❌ Aapne abhi tak koi quiz nahi banaya hai!",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    text = "📚 **Aapke Banaye Huye Quizzes:**\n\nNiche kisi bhi quiz par click karke uska summary panel open karein:\n"
    keyboard = []
    for qid, title in rows:
        keyboard.append([InlineKeyboardButton(f"📝 {title}", callback_data=f"viewq_{qid}")])
    
    keyboard.append([InlineKeyboardButton("Back to Main Menu 🔙", callback_data="back_main")])
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def handle_view_quiz_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles opening summary panel from the quiz list"""
    query = update.callback_query
    await query.answer()
    quiz_id = int(query.data.split("_")[1])
    await query.message.delete()
    await show_summary_panel(query, context, quiz_id)

async def handle_back_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Returns to the original main greeting menu"""
    query = update.callback_query
    await query.answer()
    welcome_text = (
        "👋 **Welcome to Laado Quiz Bot!**\n\n"
        "Niche diye gaye buttons se aap apna naya quiz bana sakte hain ya pehle banaye huye quizzes dekh sakte hain:\n\n"
        "🚀 /newquiz - Naya Quiz banana shuru karein\n"
        "❌ /cancel - Active creation flow cancel karein"
    )
    keyboard = [
        [InlineKeyboardButton("Create New Quiz 🚀", callback_data="btn_newquiz")],
        [InlineKeyboardButton("View My Quizzes 📚", callback_data="btn_viewquizzes")]
    ]
    await query.edit_message_text(welcome_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def show_summary_panel(query, context, quiz_id):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT title, timer FROM quizzes WHERE quiz_id = ?", (quiz_id,))
        quiz_data = cursor.fetchone()
        
        if not quiz_data:
            await query.message.reply_text("❌ Error: Quiz data could not be retrieved.")
            conn.close()
            return
        
        title, timer = quiz_data
        cursor.execute("SELECT COUNT(*) FROM questions WHERE quiz_id = ?", (quiz_id,))
        total_q = cursor.fetchone()
        conn.close()

        time_display = f"{timer} sec" if timer < 60 else f"{timer // 60} min"
        bot_username = context.bot.username
        escaped_title = escape_markdown(title)
        
        summary_text = (
            "👍 Here's your quiz:\n\n"
            f"📚 {escaped_title}\n"
            f"🙋‍♂️ {total_q[0]} question(s) · ⏱ Time: {time_display}\n\n"
            f"🔗 External sharing link:\n"
            f"https://t.me{bot_username}?start=quiz_{quiz_id}"
        )
        
        inline_keyboard = [
            [InlineKeyboardButton("🏁 Start this quiz", callback_data=f"runsolo_{quiz_id}")],
            [InlineKeyboardButton("👥 Start quiz in group", url=f"https://t.me{bot_username}?startgroup=quiz_{quiz_id}")],
            [InlineKeyboardButton("📢 Share quiz", url=f"https://t.meshare/url?url=https://t.me{bot_username}?start=quiz_{quiz_id}")],
            [InlineKeyboardButton("⚙️ Edit quiz", callback_data=f"edit_{quiz_id}"), InlineKeyboardButton("📊 Quiz status", callback_data=f"status_{quiz_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(inline_keyboard)
        await query.message.reply_text(summary_text, reply_markup=reply_markup)
    except Exception as e:
        logging.error(f"Error in show_summary_panel: {e}")
        await query.message.reply_text(f"❌ Error: {str(e)}")

async def show_summary_panel_text(update, context, quiz_id):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT title, timer FROM quizzes WHERE quiz_id = ?", (quiz_id,))
        quiz_data = cursor.fetchone()
        
        if not quiz_data:
            await update.message.reply_text("❌ Error: Quiz data could not be retrieved.")
            conn.close()
            return
        
        title, timer = quiz_data
        cursor.execute("SELECT COUNT(*) FROM questions WHERE quiz_id = ?", (quiz_id,))
        total_q = cursor.fetchone()
        conn.close()

        time_display = f"{timer} sec" if timer < 60 else f"{timer // 60} min"
        bot_username = context.bot.username
        escaped_title = escape_markdown(title)
        
        summary_text = (
            "👍 Quiz created.\n\n"
            "🏁 Here's your quiz:\n"
            f"📚 {escaped_title}\n"
            f"🙋‍♂️ {total_q[0]} question(s) · ⏱ Time: {time_display}\n\n"
            f"🔗 External sharing link:\n"
            f"https://t.me{bot_username}?start=quiz_{quiz_id}"
        )
        
        inline_keyboard = [
            [InlineKeyboardButton("🏁 Start this quiz", callback_data=f"runsolo_{quiz_id}")],
            [InlineKeyboardButton("👥 Start quiz in group", url=f"https://t.me{bot_username}?startgroup=quiz_{quiz_id}")],
            [InlineKeyboardButton("📢 Share quiz", url=f"https://t.meshare/url?url=https://t.me{bot_username}?start=quiz_{quiz_id}")],
            [InlineKeyboardButton("⚙️ Edit quiz", callback_data=f"edit_{quiz_id}"), InlineKeyboardButton("📊 Quiz status", callback_data=f"status_{quiz_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(inline_keyboard)
        await update.message.reply_text(summary_text, reply_markup=reply_markup)
    except Exception as e:
        logging.error(f"Error in show_summary_panel_text: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def edit_quiz_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    quiz_id = int(query.data.split("_")[1])
    
    keyboard = [
        [InlineKeyboardButton("📝 Edit title", callback_data=f"edtitle_{quiz_id}")],
        [InlineKeyboardButton("ℹ️ Edit description", callback_data=f"eddesc_{quiz_id}")],
        [InlineKeyboardButton("⏱ Edit timer settings", callback_data=f"edtime_{quiz_id}")],
        [InlineKeyboardButton("Back 🔙", callback_data=f"backto_{quiz_id}")]
    ]
    await query.edit_message_text(
        text="⚙️ **Edit Quiz Menu**\n\nAap is quiz ka kya badalna chahte hain? Niche se chunyein:",
        reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
    )

async def back_to_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    quiz_id = int(query.data.split("_")[1])
    await query.message.delete()
    await show_summary_panel(query, context, quiz_id)
    # ==========================================
# ⚙️ FULLY OPERATIONAL QUIZ EDITOR HANDLERS
# ==========================================

async def edit_title_trigger(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    quiz_id = int(query.data.split("_")[1])
    context.user_data["editing_quiz_id"] = quiz_id
    await query.message.reply_text("📝 Please send the **new title** for your quiz:")
    return EDIT_TITLE

