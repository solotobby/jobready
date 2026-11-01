import hashlib
import json
import os
import secrets
import sqlite3
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

DATA_DIR = Path(os.environ.get("DATA_DIR", "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / os.environ.get("DB_NAME", "jobready.db")


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000).hex()
    return f"{salt}:{hashed}"


def get_db_connection() -> sqlite3.Connection:
    """
    Returns a configured SQLite connection with WAL mode,
    foreign key constraints, and 10s busy timeout for high concurrency.
    """
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def init_db(reset: bool = False) -> None:
    """
    Initializes all application tables and performance indexes.
    If reset=True, existing tables are dropped first.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()

        if reset:
            print("⚠️ Resetting all database tables...")
            cursor.execute("DROP TABLE IF EXISTS password_resets;")
            cursor.execute("DROP TABLE IF EXISTS cv_generations;")
            cursor.execute("DROP TABLE IF EXISTS orders;")
            cursor.execute("DROP TABLE IF EXISTS users;")

        # 1. Users Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT,
                avatar_url TEXT,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL DEFAULT (strftime('%s', 'now'))
            );
        """)

        # 2. Orders & Packs Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                oid TEXT PRIMARY KEY,
                user_id TEXT,
                email TEXT NOT NULL,
                plan TEXT NOT NULL,
                status TEXT NOT NULL,
                data_json TEXT NOT NULL,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
            );
        """)

        # 3. Password Resets Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS password_resets (
                token TEXT PRIMARY KEY,
                email TEXT NOT NULL,
                expires_at REAL NOT NULL,
                created_at REAL NOT NULL
            );
        """)

        # 4. CV Generations History Table (for granular querying & analytics)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cv_generations (
                id TEXT PRIMARY KEY,
                oid TEXT NOT NULL,
                user_id TEXT,
                job_title TEXT NOT NULL,
                job_ad_text TEXT NOT NULL,
                match_score INTEGER,
                cv_json TEXT NOT NULL,
                created_at REAL NOT NULL,
                FOREIGN KEY (oid) REFERENCES orders(oid) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
            );
        """)

        # Performance Indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_email ON orders(email);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at DESC);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_password_resets_token ON password_resets(token);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_password_resets_email ON password_resets(email);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cv_generations_oid ON cv_generations(oid);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cv_generations_user_id ON cv_generations(user_id);")

        conn.commit()
        print(f"✅ Database tables & indexes verified at: {DB_PATH.resolve()}")


def seed_data() -> None:
    """
    Populates sample accounts and verified starter/job-hunt packs
    if the database is clean.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Check if demo user already exists
        cursor.execute("SELECT id FROM users WHERE email = 'alex.mercer@gmail.com'")
        if cursor.fetchone():
            print("ℹ️ Demo user already seeded.")
            return

        now = time.time()
        user_id = "8b8d5c631f3e4a138062803f50f5bb89"
        pwd_hash = hash_password("jobready123")

        cursor.execute("""
            INSERT OR REPLACE INTO users (id, email, password_hash, full_name, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, "alex.mercer@gmail.com", pwd_hash, "Alex Mercer", now - 86400, now))

        # Sample Completed Starter Pack Order
        sample_oid = "d7a4c9e1b2f8430ea6914589d1b023f4"
        sample_order_folder = DATA_DIR / sample_oid
        sample_order_folder.mkdir(parents=True, exist_ok=True)
        (sample_order_folder / "headshots").mkdir(exist_ok=True)

        sample_order_data = {
            "oid": sample_oid,
            "user_id": user_id,
            "plan": "hunt",
            "email": "alex.mercer@gmail.com",
            "job_ad": "Senior Operations & Strategy Manager to lead scalable workflow automation and cross-functional high-growth programs.",
            "status": "done",
            "headshots": ["0.jpg", "1.jpg", "2.jpg", "3.jpg"],
            "cvs": [
                {
                    "job_title": "Senior Operations & Strategy Manager",
                    "name": "Alex Mercer",
                    "contact": "alex.mercer@gmail.com | +1 (555) 234-5678 | linkedin.com/in/alexmercer-ops",
                    "headline": "Senior Operations Manager | Scaling Cross-Functional Execution & Driving Workflow Automation",
                    "summary": "Results-driven Operations Leader with 6+ years scaling cross-functional teams and automated infrastructure. Consistently improves delivery velocity and slashes turnaround times across enterprise departments.",
                    "experience": [
                        {
                            "role": "Lead Operations Specialist",
                            "company": "Apex Global Solutions",
                            "dates": "2022 - Present",
                            "bullets": [
                                "Spearheaded core workflow optimizations directly addressing requirements for Senior Operations & Strategy Manager, improving throughput by 38%.",
                                "Led cross-functional team of 6 to deploy high-leverage initiatives, cutting turnaround time by 45%.",
                                "Architected standardized reporting frameworks and automated pipelines adopted across department."
                            ]
                        },
                        {
                            "role": "Associate Project Specialist",
                            "company": "Beacon Enterprises",
                            "dates": "2020 - 2022",
                            "bullets": [
                                "Managed end-to-end deliverables for key stakeholders with a 99.4% on-time completion rate.",
                                "Implemented data-driven review procedures that eliminated critical errors by 32%."
                            ]
                        }
                    ],
                    "education": ["B.S. in Business & Technology Management, Honors Graduate"],
                    "skills": ["Strategic Planning", "Data Analysis", "Cross-functional Leadership", "Process Optimization", "Agile Execution", "Stakeholder Communication"],
                    "match_score": 96,
                    "missing_keywords": ["Certifications: PMP or Scrum Master (recommended)", "Advanced SQL / BigQuery experience"],
                    "ats_insights": [
                        "Matches 9 out of 11 critical skill keywords from the job description.",
                        "Strong leadership metrics and quantified achievements identified."
                    ],
                    "linkedin_headline": "Senior Operations & Strategy Manager | Scaling Operations & Driving Business Growth | Tech & Strategy",
                    "linkedin_about": "Passionate about solving complex challenges at the intersection of execution and strategy. Over the past 5+ years, I've focused on delivering measurable outcomes, optimizing team workflows, and building scalable systems."
                }
            ],
            "cvs_left": 4,
            "linkedin_included": True,
            "created_at": now - 3600,
            "updated_at": now - 1800,
        }

        # Write sample order file and DB row
        (sample_order_folder / "order.json").write_text(json.dumps(sample_order_data, indent=2), encoding="utf-8")

        cursor.execute("""
            INSERT OR REPLACE INTO orders (oid, user_id, email, plan, status, data_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            sample_oid,
            user_id,
            "alex.mercer@gmail.com",
            "hunt",
            "done",
            json.dumps(sample_order_data),
            now - 3600,
            now - 1800
        ))

        conn.commit()
        print("✅ Demo user ('alex.mercer@gmail.com' / 'jobready123') and sample Job Hunt Pack seeded successfully.")


def get_db_stats() -> Dict[str, int]:
    """Returns total row counts for all database tables."""
    stats = {}
    with get_db_connection() as conn:
        cursor = conn.cursor()
        for table in ["users", "orders", "password_resets", "cv_generations"]:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                stats[table] = cursor.fetchone()[0]
            except Exception:
                stats[table] = 0
    return stats


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--reset" in args:
        init_db(reset=True)
        seed_data()
    elif "--seed" in args:
        seed_data()
    elif "--stats" in args:
        print("Database Statistics:")
        for tbl, count in get_db_stats().items():
            print(f"  • {tbl}: {count} records")
    else:
        init_db(reset=False)
        seed_data()
        print("\nDatabase Statistics:")
        for tbl, count in get_db_stats().items():
            print(f"  • {tbl}: {count} records")
