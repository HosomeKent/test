from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)
DB = "kakeibo.db"


def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                type TEXT NOT NULL,
                category TEXT NOT NULL,
                amount INTEGER NOT NULL,
                note TEXT
            )
        """)


@app.route("/")
def index():
    month = request.args.get("month", datetime.now().strftime("%Y-%m"))
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM transactions WHERE date LIKE ? ORDER BY date DESC",
            (f"{month}%",)
        ).fetchall()
        income = sum(r["amount"] for r in rows if r["type"] == "income")
        expense = sum(r["amount"] for r in rows if r["type"] == "expense")
    return render_template("index.html", rows=rows, month=month, income=income, expense=expense)


@app.route("/add", methods=["POST"])
def add():
    with get_db() as conn:
        conn.execute(
            "INSERT INTO transactions (date, type, category, amount, note) VALUES (?, ?, ?, ?, ?)",
            (request.form["date"], request.form["type"], request.form["category"],
             int(request.form["amount"]), request.form.get("note", ""))
        )
    return redirect(url_for("index", month=request.form["date"][:7]))


@app.route("/delete/<int:id>")
def delete(id):
    with get_db() as conn:
        row = conn.execute("SELECT date FROM transactions WHERE id=?", (id,)).fetchone()
        month = row["date"][:7] if row else datetime.now().strftime("%Y-%m")
        conn.execute("DELETE FROM transactions WHERE id=?", (id,))
    return redirect(url_for("index", month=month))


@app.route("/chart_data")
def chart_data():
    month = request.args.get("month", datetime.now().strftime("%Y-%m"))
    with get_db() as conn:
        rows = conn.execute(
            "SELECT category, SUM(amount) as total FROM transactions WHERE date LIKE ? AND type='expense' GROUP BY category",
            (f"{month}%",)
        ).fetchall()
    return jsonify({"labels": [r["category"] for r in rows], "values": [r["total"] for r in rows]})


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
