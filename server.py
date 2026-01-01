from flask import Flask
from flask_socketio import SocketIO, emit
import sqlite3
from datetime import datetime, timedelta
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE_DIR, "..", "database.db")

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# DB = "database.db"


def get_db():
    conn = sqlite3.connect(DB, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


# 🔹 INIT DATABASE
def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT,
            message TEXT,
            timestamp DATETIME
        )
    """)

    conn.commit()


init_db()


@socketio.on("login")
def login(data):
    emit("login_success", {"username": data["username"]})


@socketio.on("message")
def handle_message(data):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO messages (sender, message, timestamp) VALUES (?, ?, ?)",
        (data["sender"], data["msg"], datetime.now())
    )
    conn.commit()

    # 🔁 send to all clients
    emit("message", data, broadcast=True)


@socketio.on("load_history")
def load_history():
    conn = get_db()
    cur = conn.cursor()

    since = datetime.now() - timedelta(days=3)

    cur.execute("""
        SELECT sender, message FROM messages
        WHERE timestamp >= ?
        ORDER BY id ASC
    """, (since,))

    rows = cur.fetchall()

    history = []
    for r in rows:
        history.append({
            "sender": r["sender"],
            "msg": r["message"]
        })

    # ✅ ONLY to requesting client
    emit("history", history)


if __name__ == "__main__":
    
    socketio.run(app, host="0.0.0.0", port=5000)

