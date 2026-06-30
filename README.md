# 🎯 Laado Quiz Bot - Telegram Quiz Master

An advanced **Telegram bot** for creating and hosting interactive group quizzes in real-time using polls with scoring, leaderboards, and social sharing.

---

## ✨ Features

### 📝 Quiz Creation
- Create custom quizzes with multiple-choice questions
- Add quiz titles and descriptions
- Set per-question time limits (15, 30, 40, 60 seconds)
- Support for explanations and pre-question context
- Undo functionality during quiz building

### 🎮 Group Quiz Mode
- Host quizzes in Telegram groups/channels
- Real-time poll-based Q&A
- Auto-joining participant system (minimum 2 players to start)
- Live score tracking and ranking

### 📊 Leaderboard & Results
- Ranked leaderboard with medals (🥇🥈🥉)
- Individual scores and time tracking
- Top 20 players display
- Social sharing integration

### ⚙️ Quiz Management
- Edit quiz details (title, description, timer)
- View all created quizzes
- Deep-linking for quiz distribution
- Share quizzes via groups or direct links

---

## 🚀 Installation

### Prerequisites
- Python 3.8+
- Telegram Bot API token (from [@BotFather](https://t.me/botfather))
- Required dependencies

### Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/manishakumarim293-ctrl/Quiz_Bot.git
   cd Quiz_Bot
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Create `.env` file:**
   ```env
   BOT_TOKEN=your_telegram_bot_token_here
   OWNER_ID=your_telegram_user_id_here
   ```

4. **Run the bot:**
   ```bash
   python quiz_bot.py
   ```

---

## 📖 Usage

### Commands

| Command | Description |
|---------|------------|
| `/start` | Initialize bot and see main menu |
| `/newquiz` | Start creating a new quiz |
| `/help` | Display help information |
| `/cancel` | Cancel current operation |
| `/skip` | Skip optional fields |
| `/undo` | Remove last added question |
| `/done` | Finish adding questions |

### Creating a Quiz

1. Use `/newquiz` or click "Create New Quiz 🚀"
2. Enter quiz title
3. Add optional description (or `/skip`)
4. Add questions via **Telegram polls** in quiz mode
   - Click 📎 (Attachment) → Select Poll
   - Enable "Quiz Mode"
   - Add 2-7 options and select correct answer
   - Optionally add explanation
5. Click `/done` when finished
6. Set time limit per question (15/30/40/60 seconds)
7. Share or start quiz!

### Hosting a Group Quiz

1. Create a quiz first (steps above)
2. Click "🏁 Start this quiz" for solo mode or
3. Click "👥 Start quiz in group" to invite others
4. Share the link with friends
5. Minimum 2 players must click "I am ready! 🎯" to begin
6. Answer each question within the time limit
7. View final leaderboard with scores and rankings

---

## 🗄️ Database Schema

### Quizzes Table
```sql
CREATE TABLE quizzes (
    quiz_id INTEGER PRIMARY KEY AUTOINCREMENT,
    creator_id INTEGER,
    title TEXT,
    description TEXT,
    timer INTEGER DEFAULT 30
)
```

### Questions Table
```sql
CREATE TABLE questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quiz_id INTEGER,
    question_text TEXT,
    options TEXT,
    correct_answer TEXT,
    explanation TEXT,
    pre_message TEXT,
    FOREIGN KEY(quiz_id) REFERENCES quizzes(quiz_id)
)
```

---

## 🛠️ Technologies Used

- **python-telegram-bot** - Telegram Bot API wrapper
- **SQLite3** - Local database for quiz storage
- **asyncio** - Asynchronous operations
- **python-dotenv** - Environment variable management

---

## 🐛 Bug Fixes (Latest)

### Fixed Issues:
- ✅ URL formatting in sharing links (corrected `t.me/` format)
- ✅ Share button functionality 
- ✅ Group quiz initialization
- ✅ Poll answer tracking
- ✅ Leaderboard compilation

---

## 📝 File Structure

```
Quiz_Bot/
├── quiz_bot.py          # Main bot application
├── quiz_bot.db          # SQLite database (auto-created)
├── requirements.txt     # Python dependencies
├── .env                 # Environment variables (create this)
└── README.md            # This file
```

---

## 🤝 Contributing

Contributions are welcome! To contribute:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is open-source and available under the MIT License.

---

## 👤 Author

**Manisha Kumar** [@manishakumarim293-ctrl](https://github.com/manishakumarim293-ctrl)

---

## 💬 Support & Feedback

For issues, bugs, or feature requests, please open a [GitHub Issue](https://github.com/manishakumarim293-ctrl/Quiz_Bot/issues).

---

## 🚀 Future Enhancements

- [ ] Category-based quizzes
- [ ] Difficulty levels (Easy/Medium/Hard)
- [ ] Quiz analytics and statistics
- [ ] Leaderboard persistence
- [ ] Question shuffling option
- [ ] Negative marking system
- [ ] Admin dashboard
- [ ] Multi-language support

---

**Happy Quizzing! 🎉**
