# AI_BACKEND – Intelligent Interview Management System

This backend system is designed to support an intelligent interview management platform. It features resume parsing, interview scheduling, AI-based feedback analysis, and analytics dashboards, all integrated via APIs and databases.

---

## 📦 Features

### ✅ Resume Parser
- Supports `.pdf`, `.docx`, and `.doc` formats.
- Extracts and analyzes content using Google Generative AI.
- Saves parsed details for further processing.

### 📅 Event Scheduler
- Schedules interviews using Google Calendar API.
- Uses Faker to populate dummy interviewer/candidate data.
- Stores data in an SQLite database.

### 🎤 Interview Feedback
- Transcribes interview videos using AssemblyAI.
- Generates feedback using OpenRouter's language models.
- Saves structured feedback and interview metadata.

### 📊 Analytics Dashboard
- Visualizes candidate data (e.g., performance, trends).
- Built with Streamlit, SQLite, Pandas, and Matplotlib.

---

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/AI_BACKEND.git
cd AI_BACKEND

pip install -r requirements.txt

GOOGLE_API_KEY=your_google_gemini_key
ASSEMBLYAI_API_KEY=your_assemblyai_key
OPENROUTER_API_KEY=your_openrouter_key

```
