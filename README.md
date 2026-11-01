# JobReady Pack ⚡

> **AI Studio Headshots + ATS-Tailored CVs That Get You Hired.**

Why pay $35+ for just headshots? JobReady delivers 40 studio-grade AI headshots PLUS an ATS-tailored resume rewritten for your dream job in 2 minutes for just $9.99.

---

## 🚀 Features

- **📸 4K AI Studio Headshots:** 4 distinct styles (Corporate Executive, Tech Founder, Smart Casual, Studio 4K) using FLUX Pro / Fal AI.
- **📄 ATS Resume Tailoring:** Powered by OpenAI GPT-4o with zero-hallucination factual rewrites against real job postings.
- **🔒 Complete Authentication:** JWT cookie & bearer authentication, signup, login, password reset flow.
- **📊 Member Dashboard:** Track packs, view generated 4K photos gallery, and access tailored CV versions.
- **💳 Stripe Integration:** Secure payments for Starter ($9.99), Job Hunt ($19.99), and 5x CV Top-up ($4.99).
- **🗄️ High-Concurrency SQLite Database:** WAL mode, foreign key constraints, automated seeding and performance indexes.

---

## 🛠️ Tech Stack

- **Backend:** FastAPI, Python 3.9+, Uvicorn, SQLite (WAL mode)
- **AI Engines:** OpenAI (`gpt-4o`), Fal.ai FLUX Pro, Anthropic Claude (optional fallback)
- **PDF Processing:** PyPDF
- **Frontend:** Single-page responsive web app with Tailwind CSS and Lucide Icons
- **Payments:** Stripe Checkout & Webhooks

---

## 📦 Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/solotobby/jobready.git
cd jobready
```

### 2. Set up virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env` and fill in your keys:
```bash
cp .env.example .env
```

### 4. Initialize Database
```bash
python database.py
```

### 5. Run the Application
```bash
uvicorn main:app --host 0.0.0.0 --port 8080 --reload
```

Visit `http://localhost:8080` in your browser.

---

## 🧪 Demo Credentials

- **Email:** `alex.mercer@gmail.com`
- **Password:** `jobready123`

---

## 📄 License

MIT License.
