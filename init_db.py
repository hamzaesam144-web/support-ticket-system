from database import get_db_connection
from werkzeug.security import generate_password_hash
from datetime import datetime

connection = get_db_connection()

connection.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    role TEXT NOT NULL
)
""")

connection.execute("""
CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    category TEXT NOT NULL,
    priority TEXT NOT NULL DEFAULT 'Medium',
    status TEXT NOT NULL DEFAULT 'Open',
    creator_id INTEGER NOT NULL,
    assigned_to INTEGER,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,

    FOREIGN KEY (creator_id) REFERENCES users(id),
    FOREIGN KEY (assigned_to) REFERENCES users(id)
)
""")

connection.execute("""
CREATE TABLE IF NOT EXISTS comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL,

    FOREIGN KEY (ticket_id) REFERENCES tickets(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
)
""")

connection.execute("""
CREATE TABLE IF NOT EXISTS ticket_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER NOT NULL,
    actor_id INTEGER NOT NULL,
    change_type TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    note TEXT,
    created_at TEXT NOT NULL,

    FOREIGN KEY (ticket_id) REFERENCES tickets(id),
    FOREIGN KEY (actor_id) REFERENCES users(id)
)
""")

# -------------------------
# CREATE TEST USERS
# -------------------------

users = [
    ("employee1", generate_password_hash("emp123"), "employee"),
    ("employee2", generate_password_hash("emp123"), "employee"),
    ("support1", generate_password_hash("sup123"), "support"),
    ("support2", generate_password_hash("sup123"), "support")
]

connection.executemany("""
INSERT OR IGNORE INTO users (username, password, role)
VALUES (?, ?, ?)
""", users)

# -------------------------
# GET USER IDS
# -------------------------

employee1 = connection.execute(
    "SELECT id FROM users WHERE username = ?",
    ("employee1",)
).fetchone()

employee2 = connection.execute(
    "SELECT id FROM users WHERE username = ?",
    ("employee2",)
).fetchone()

support1 = connection.execute(
    "SELECT id FROM users WHERE username = ?",
    ("support1",)
).fetchone()

support2 = connection.execute(
    "SELECT id FROM users WHERE username = ?",
    ("support2",)
).fetchone()

# -------------------------
# CREATE SAMPLE TICKETS
# -------------------------

ticket_count = connection.execute(
    "SELECT COUNT(*) AS count FROM tickets"
).fetchone()["count"]

if ticket_count == 0:

    now = datetime.now().isoformat()

    sample_tickets = [
        (
            "Laptop not starting",
            "My work laptop does not turn on.",
            "Technical Issue",
            "High",
            "Open",
            employee1["id"],
            None,
            now,
            now
        ),

        (
            "Need access to accounting system",
            "Please provide access to the accounting system.",
            "Access Request",
            "Medium",
            "In Progress",
            employee1["id"],
            support1["id"],
            now,
            now
        ),

        (
            "Email sending problem",
            "I cannot send emails from my account.",
            "Technical Issue",
            "Low",
            "Resolved",
            employee2["id"],
            support2["id"],
            now,
            now
        ),

        (
            "Old equipment request",
            "Request for replacement office equipment.",
            "Other",
            "Medium",
            "Closed",
            employee2["id"],
            support1["id"],
            now,
            now
        )
    ]

    connection.executemany("""
    INSERT INTO tickets (
        title,
        description,
        category,
        priority,
        status,
        creator_id,
        assigned_to,
        created_at,
        updated_at
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, sample_tickets)

connection.commit()
connection.close()

print("Database, test users, and sample tickets created successfully.")
