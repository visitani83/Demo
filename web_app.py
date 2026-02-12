#!/usr/bin/env python3
"""Flask web UI for the Expense Tracker — upload receipts & view dashboard."""

import os
import tempfile
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, jsonify, flash

from expense_tracker import (
    init_db, add_expense, list_expenses, summary_by_category,
    monthly_summary, delete_expense, scan_receipt, auto_categorize,
    CATEGORY_KEYWORDS,
)

app = Flask(__name__)
app.secret_key = os.urandom(24)

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}


def get_db():
    return init_db()


def allowed_file(filename):
    return os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS


# ── Dashboard ─────────────────────────────────────────────────────────

@app.route("/")
def dashboard():
    conn = get_db()
    month_filter = request.args.get("month", "")

    # Category summary
    cat_rows = summary_by_category(conn, month_filter or None)
    categories = [r[0] for r in cat_rows]
    cat_amounts = [round(r[1], 2) for r in cat_rows]
    cat_counts = [r[2] for r in cat_rows]
    total = round(sum(cat_amounts), 2)

    # Monthly trend
    monthly_rows = monthly_summary(conn)
    months = [r[0] for r in reversed(monthly_rows)]
    month_totals = [round(r[1], 2) for r in reversed(monthly_rows)]

    # Recent expenses
    expenses = list_expenses(conn, limit=50)

    # Available months for filter dropdown
    cursor = conn.cursor()
    cursor.execute(
        "SELECT DISTINCT strftime('%Y-%m', date) AS m FROM expenses ORDER BY m DESC"
    )
    available_months = [r[0] for r in cursor.fetchall()]

    conn.close()

    return render_template(
        "dashboard.html",
        categories=categories,
        cat_amounts=cat_amounts,
        cat_counts=cat_counts,
        total=total,
        months=months,
        month_totals=month_totals,
        expenses=expenses,
        available_months=available_months,
        month_filter=month_filter,
    )


# ── Upload Receipt ────────────────────────────────────────────────────

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "GET":
        all_categories = sorted(CATEGORY_KEYWORDS.keys()) + ["Other"]
        return render_template("upload.html", categories=all_categories)

    # POST — handle file upload
    file = request.files.get("receipt")
    if not file or file.filename == "":
        flash("No file selected.", "error")
        return redirect(url_for("upload"))

    if not allowed_file(file.filename):
        flash("Unsupported file type. Use JPG, PNG, GIF, WebP, or BMP.", "error")
        return redirect(url_for("upload"))

    # Save to temp file
    ext = os.path.splitext(file.filename)[1].lower()
    tmp = tempfile.NamedTemporaryFile(dir=UPLOAD_DIR, suffix=ext, delete=False)
    file.save(tmp.name)
    tmp.close()

    # Scan with Claude Vision
    result, error = scan_receipt(tmp.name)

    if error:
        os.unlink(tmp.name)
        flash(f"Scan failed: {error}", "error")
        return redirect(url_for("upload"))

    # Apply user overrides from form
    override_cat = request.form.get("category", "").strip()
    override_date = request.form.get("date", "").strip()

    amount = result.get("amount")
    description = result.get("description") or "Receipt purchase"
    category = override_cat or result.get("category") or auto_categorize(description)
    date = override_date or result.get("date")
    items = result.get("items") or []

    if amount is None:
        os.unlink(tmp.name)
        flash("Could not extract an amount from the receipt. Please add manually.", "error")
        return redirect(url_for("upload"))

    # Save expense
    conn = get_db()
    expense_id, assigned_category = add_expense(conn, amount, description, category, date)
    conn.close()
    os.unlink(tmp.name)

    date_display = date or datetime.now().strftime("%Y-%m-%d")
    items_str = ", ".join(items[:5]) if items else ""

    flash(
        f"Added #{expense_id}: ${amount:.2f} — {description} [{assigned_category}] on {date_display}"
        + (f" | Items: {items_str}" if items_str else ""),
        "success",
    )
    return redirect(url_for("dashboard"))


# ── Add Manual Expense ────────────────────────────────────────────────

@app.route("/add", methods=["POST"])
def add():
    amount = request.form.get("amount", "").strip()
    description = request.form.get("description", "").strip()
    category = request.form.get("category", "").strip()
    date = request.form.get("date", "").strip()

    if not amount or not description:
        flash("Amount and description are required.", "error")
        return redirect(url_for("dashboard"))

    try:
        amount = float(amount)
    except ValueError:
        flash("Invalid amount.", "error")
        return redirect(url_for("dashboard"))

    conn = get_db()
    expense_id, assigned_category = add_expense(
        conn, amount, description, category or None, date or None
    )
    conn.close()

    flash(f"Added #{expense_id}: ${amount:.2f} — {description} [{assigned_category}]", "success")
    return redirect(url_for("dashboard"))


# ── Delete Expense ────────────────────────────────────────────────────

@app.route("/delete/<int:expense_id>", methods=["POST"])
def delete(expense_id):
    conn = get_db()
    if delete_expense(conn, expense_id):
        flash(f"Deleted expense #{expense_id}.", "success")
    else:
        flash(f"Expense #{expense_id} not found.", "error")
    conn.close()
    return redirect(url_for("dashboard"))


# ── API endpoints for AJAX ────────────────────────────────────────────

@app.route("/api/summary")
def api_summary():
    month = request.args.get("month", "")
    conn = get_db()
    rows = summary_by_category(conn, month or None)
    conn.close()
    return jsonify({
        "categories": [r[0] for r in rows],
        "amounts": [round(r[1], 2) for r in rows],
        "counts": [r[2] for r in rows],
        "total": round(sum(r[1] for r in rows), 2),
    })


if __name__ == "__main__":
    print("\n  Expense Tracker Web UI")
    print("  http://localhost:5000\n")
    app.run(debug=True, host="0.0.0.0", port=5000)
