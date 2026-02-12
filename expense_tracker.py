#!/usr/bin/env python3
"""Simple expense tracking agent with auto-categorization."""

import sqlite3
import base64
import json
import os
import re
import sys
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expenses.db")

# Keyword-to-category mapping for auto-categorization
CATEGORY_KEYWORDS = {
    "Food & Dining": [
        "grocery", "groceries", "restaurant", "cafe", "coffee", "lunch",
        "dinner", "breakfast", "pizza", "burger", "sushi", "food", "snack",
        "drink", "bar", "pub", "bakery", "meal", "takeout", "delivery",
        "uber eats", "doordash", "grubhub", "starbucks", "mcdonald",
    ],
    "Transport": [
        "uber", "lyft", "taxi", "gas", "fuel", "petrol", "parking",
        "toll", "bus", "train", "metro", "subway", "flight", "airline",
        "car wash", "car repair", "mechanic", "oil change", "tire",
    ],
    "Shopping": [
        "amazon", "walmart", "target", "clothes", "shoes", "shirt",
        "pants", "jacket", "electronics", "gadget", "furniture", "ikea",
        "mall", "store", "online order", "ebay",
    ],
    "Bills & Utilities": [
        "rent", "mortgage", "electric", "electricity", "water", "internet",
        "wifi", "phone bill", "mobile plan", "insurance", "tax", "cable",
        "subscription", "netflix", "spotify", "hulu", "utility",
    ],
    "Entertainment": [
        "movie", "cinema", "concert", "theater", "game", "gaming",
        "bowling", "arcade", "park", "museum", "zoo", "event", "ticket",
        "festival", "sports", "gym membership",
    ],
    "Health": [
        "doctor", "hospital", "pharmacy", "medicine", "prescription",
        "dental", "dentist", "eye", "optician", "therapy", "vitamin",
        "supplement", "clinic", "health", "medical",
    ],
    "Education": [
        "book", "course", "class", "tuition", "school", "university",
        "udemy", "coursera", "tutorial", "training", "workshop", "seminar",
    ],
    "Personal Care": [
        "haircut", "salon", "spa", "barber", "skincare", "cosmetics",
        "makeup", "perfume", "hygiene", "laundry", "dry clean",
    ],
    "Gifts & Donations": [
        "gift", "present", "donation", "charity", "tip", "birthday gift",
        "wedding gift",
    ],
}


def init_db():
    """Initialize the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL,
            description TEXT NOT NULL,
            category TEXT NOT NULL,
            date TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    return conn


def auto_categorize(description):
    """Guess a category based on keywords in the description."""
    desc_lower = description.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in desc_lower:
                return category
    return "Other"


def _image_to_base64(image_path):
    """Read an image file and return its base64 encoding and media type."""
    ext = os.path.splitext(image_path)[1].lower()
    media_types = {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".png": "image/png", ".gif": "image/gif",
        ".webp": "image/webp", ".bmp": "image/bmp",
    }
    media_type = media_types.get(ext, "image/jpeg")
    with open(image_path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    return data, media_type


def scan_receipt(image_path):
    """Extract expense details from a receipt image using Claude Vision API."""
    if not os.path.isfile(image_path):
        return None, f"File not found: {image_path}"

    try:
        import anthropic
    except ImportError:
        return None, "Missing dependency. Install with: pip install anthropic"

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None, (
            "ANTHROPIC_API_KEY not set.\n"
            "  Export it first: export ANTHROPIC_API_KEY=your-key-here"
        )

    try:
        img_data, media_type = _image_to_base64(image_path)
    except Exception as e:
        return None, f"Cannot read image: {e}"

    categories_list = ", ".join(sorted(CATEGORY_KEYWORDS.keys())) + ", Other"

    client = anthropic.Anthropic(api_key=api_key)
    try:
        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=512,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {"type": "base64", "media_type": media_type, "data": img_data},
                    },
                    {
                        "type": "text",
                        "text": (
                            "Extract expense details from this receipt/bill image. "
                            "Return ONLY valid JSON with these fields:\n"
                            '  "amount": <number, the total/grand total amount>,\n'
                            '  "description": "<vendor or short description of purchase>",\n'
                            f'  "category": "<one of: {categories_list}>",\n'
                            '  "date": "<YYYY-MM-DD if visible, else null>",\n'
                            '  "items": ["<list of line items if visible>"]\n'
                            "If you cannot extract a field, use null. Return ONLY the JSON object."
                        ),
                    },
                ],
            }],
        )
    except Exception as e:
        return None, f"API call failed: {e}"

    raw = response.content[0].text.strip()
    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        return None, f"Could not parse API response:\n{raw}"

    return result, None


def add_expense(conn, amount, description, category=None, date=None):
    """Add a new expense."""
    if category is None:
        category = auto_categorize(description)
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO expenses (amount, description, category, date) VALUES (?, ?, ?, ?)",
        (amount, description, category, date),
    )
    conn.commit()
    return cursor.lastrowid, category


def list_expenses(conn, limit=20):
    """List recent expenses."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, amount, description, category, date FROM expenses ORDER BY date DESC, id DESC LIMIT ?",
        (limit,),
    )
    return cursor.fetchall()


def summary_by_category(conn, month=None):
    """Get spending summary grouped by category."""
    cursor = conn.cursor()
    if month:
        cursor.execute(
            "SELECT category, SUM(amount), COUNT(*) FROM expenses WHERE strftime('%Y-%m', date) = ? GROUP BY category ORDER BY SUM(amount) DESC",
            (month,),
        )
    else:
        cursor.execute(
            "SELECT category, SUM(amount), COUNT(*) FROM expenses GROUP BY category ORDER BY SUM(amount) DESC"
        )
    return cursor.fetchall()


def monthly_summary(conn):
    """Get spending totals by month."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT strftime('%Y-%m', date) AS month, SUM(amount), COUNT(*) FROM expenses GROUP BY month ORDER BY month DESC LIMIT 12"
    )
    return cursor.fetchall()


def search_expenses(conn, query):
    """Search expenses by description."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, amount, description, category, date FROM expenses WHERE description LIKE ? ORDER BY date DESC",
        (f"%{query}%",),
    )
    return cursor.fetchall()


def delete_expense(conn, expense_id):
    """Delete an expense by ID."""
    cursor = conn.cursor()
    cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    conn.commit()
    return cursor.rowcount > 0


def get_all_categories(conn):
    """Get all categories currently in use."""
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT category FROM expenses ORDER BY category")
    return [row[0] for row in cursor.fetchall()]


def print_table(rows, headers):
    """Print a formatted table."""
    if not rows:
        print("  No records found.")
        return

    col_widths = [len(h) for h in headers]
    str_rows = []
    for row in rows:
        str_row = [str(v) for v in row]
        str_rows.append(str_row)
        for i, val in enumerate(str_row):
            col_widths[i] = max(col_widths[i], len(val))

    header_line = "  ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
    separator = "  ".join("-" * col_widths[i] for i in range(len(headers)))

    print(f"  {header_line}")
    print(f"  {separator}")
    for row in str_rows:
        line = "  ".join(row[i].ljust(col_widths[i]) for i in range(len(headers)))
        print(f"  {line}")


def print_bar(label, value, max_value, bar_width=30):
    """Print a single bar chart row."""
    filled = int((value / max_value) * bar_width) if max_value > 0 else 0
    bar = "█" * filled + "░" * (bar_width - filled)
    print(f"  {label:20s} |{bar}| ${value:>10.2f}")


def cmd_add(conn, args):
    """Handle the 'add' command."""
    if len(args) < 2:
        print("Usage: add <amount> <description> [--category CATEGORY] [--date YYYY-MM-DD]")
        return

    try:
        amount = float(args[0])
    except ValueError:
        print(f"Error: '{args[0]}' is not a valid amount.")
        return

    category = None
    date = None
    desc_parts = []

    i = 1
    while i < len(args):
        if args[i] == "--category" and i + 1 < len(args):
            category = args[i + 1]
            i += 2
        elif args[i] == "--date" and i + 1 < len(args):
            date = args[i + 1]
            i += 2
        else:
            desc_parts.append(args[i])
            i += 1

    description = " ".join(desc_parts)
    if not description:
        print("Error: Description is required.")
        return

    expense_id, assigned_category = add_expense(conn, amount, description, category, date)
    date_display = date or datetime.now().strftime("%Y-%m-%d")
    print(f"  Added expense #{expense_id}:")
    print(f"    Amount:   ${amount:.2f}")
    print(f"    Desc:     {description}")
    print(f"    Category: {assigned_category}")
    print(f"    Date:     {date_display}")


def cmd_list(conn, args):
    """Handle the 'list' command."""
    limit = 20
    if args:
        try:
            limit = int(args[0])
        except ValueError:
            pass

    rows = list_expenses(conn, limit)
    formatted = [(r[0], f"${r[1]:.2f}", r[2], r[3], r[4]) for r in rows]
    print(f"\n  Recent Expenses (last {limit}):\n")
    print_table(formatted, ["ID", "Amount", "Description", "Category", "Date"])
    print()


def cmd_summary(conn, args):
    """Handle the 'summary' command."""
    month = None
    if args:
        month = args[0]
        print(f"\n  Expense Summary for {month}:\n")
    else:
        print("\n  Expense Summary (All Time):\n")

    rows = summary_by_category(conn, month)
    if not rows:
        print("  No expenses recorded yet.")
        return

    total = sum(r[1] for r in rows)
    max_val = max(r[1] for r in rows)

    for category, amount, count in rows:
        pct = (amount / total * 100) if total > 0 else 0
        print_bar(f"{category} ({count})", amount, max_val)
        print(f"  {'':20s}  {pct:.1f}% of total")

    print(f"\n  {'TOTAL':20s}  ${total:>10.2f}")
    print()


def cmd_monthly(conn, _args):
    """Handle the 'monthly' command."""
    print("\n  Monthly Spending Overview:\n")
    rows = monthly_summary(conn)
    if not rows:
        print("  No expenses recorded yet.")
        return

    max_val = max(r[1] for r in rows)
    for month, amount, count in rows:
        print_bar(f"{month} ({count} items)", amount, max_val)

    print()


def cmd_search(conn, args):
    """Handle the 'search' command."""
    if not args:
        print("Usage: search <query>")
        return

    query = " ".join(args)
    rows = search_expenses(conn, query)
    formatted = [(r[0], f"${r[1]:.2f}", r[2], r[3], r[4]) for r in rows]
    print(f"\n  Search results for '{query}':\n")
    print_table(formatted, ["ID", "Amount", "Description", "Category", "Date"])
    print()


def cmd_delete(conn, args):
    """Handle the 'delete' command."""
    if not args:
        print("Usage: delete <id>")
        return

    try:
        expense_id = int(args[0])
    except ValueError:
        print(f"Error: '{args[0]}' is not a valid ID.")
        return

    if delete_expense(conn, expense_id):
        print(f"  Deleted expense #{expense_id}.")
    else:
        print(f"  Expense #{expense_id} not found.")


def cmd_scan(conn, args):
    """Handle the 'scan' command — extract expense from a receipt image."""
    if not args:
        print("Usage: scan <image_path> [--category CATEGORY] [--date YYYY-MM-DD]")
        return

    image_path = args[0]
    override_category = None
    override_date = None

    i = 1
    while i < len(args):
        if args[i] == "--category" and i + 1 < len(args):
            override_category = args[i + 1]
            i += 2
        elif args[i] == "--date" and i + 1 < len(args):
            override_date = args[i + 1]
            i += 2
        else:
            i += 1

    print(f"  Scanning receipt: {image_path} ...")
    result, error = scan_receipt(image_path)

    if error:
        print(f"  Error: {error}")
        return

    amount = result.get("amount")
    description = result.get("description") or "Receipt purchase"
    category = override_category or result.get("category") or auto_categorize(description)
    date = override_date or result.get("date")
    items = result.get("items") or []

    if amount is None:
        print("  Could not extract an amount from the receipt.")
        print("  Use: add <amount> <description> to enter manually.")
        return

    # Show extracted info
    print(f"\n  Extracted from receipt:")
    print(f"    Vendor:   {description}")
    print(f"    Amount:   ${amount:.2f}")
    print(f"    Category: {category}")
    print(f"    Date:     {date or 'not detected (using today)'}")
    if items:
        print(f"    Items:")
        for item in items[:10]:
            print(f"      - {item}")

    expense_id, assigned_category = add_expense(conn, amount, description, category, date)
    date_display = date or datetime.now().strftime("%Y-%m-%d")

    print(f"\n  Added expense #{expense_id}:")
    print(f"    Amount:   ${amount:.2f}")
    print(f"    Desc:     {description}")
    print(f"    Category: {assigned_category}")
    print(f"    Date:     {date_display}")


def cmd_categories(conn, _args):
    """Handle the 'categories' command."""
    print("\n  Built-in categories:")
    for cat in sorted(CATEGORY_KEYWORDS.keys()):
        print(f"    - {cat}")
    print(f"    - Other")

    used = get_all_categories(conn)
    custom = [c for c in used if c not in CATEGORY_KEYWORDS and c != "Other"]
    if custom:
        print("\n  Custom categories in use:")
        for cat in custom:
            print(f"    - {cat}")
    print()


def cmd_help(_conn, _args):
    """Print help information."""
    print("""
  Expense Tracker - Commands:

    add <amount> <description> [--category CAT] [--date YYYY-MM-DD]
        Add a new expense. Category is auto-detected if not specified.

    list [N]
        Show the last N expenses (default: 20).

    summary [YYYY-MM]
        Show spending breakdown by category. Optionally filter by month.

    monthly
        Show month-by-month spending overview.

    search <query>
        Search expenses by description.

    scan <image_path> [--category CAT] [--date YYYY-MM-DD]
        Scan a receipt/bill image and auto-extract expense details.
        Uses Claude Vision API (requires ANTHROPIC_API_KEY env var).

    delete <id>
        Delete an expense by its ID.

    categories
        List all available categories.

    help
        Show this help message.

    quit / exit
        Exit the tracker.

  Examples:
    add 12.50 Coffee at Starbucks
    add 45.00 Uber ride to airport --category Transport
    add 120 Monthly gym membership --date 2025-01-15
    scan receipt.jpg
    scan bills/electricity.png --category "Bills & Utilities"
    summary 2025-01
    search grocery
""")


COMMANDS = {
    "add": cmd_add,
    "list": cmd_list,
    "ls": cmd_list,
    "summary": cmd_summary,
    "monthly": cmd_monthly,
    "search": cmd_search,
    "find": cmd_search,
    "delete": cmd_delete,
    "rm": cmd_delete,
    "categories": cmd_categories,
    "cats": cmd_categories,
    "scan": cmd_scan,
    "receipt": cmd_scan,
    "help": cmd_help,
}


def interactive_mode(conn):
    """Run the tracker in interactive mode."""
    print("\n  ╔══════════════════════════════════════╗")
    print("  ║       Expense Tracker Agent          ║")
    print("  ╚══════════════════════════════════════╝")
    print('  Type "help" for available commands.\n')

    while True:
        try:
            user_input = input("  expense> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  Goodbye!")
            break

        if not user_input:
            continue

        parts = user_input.split()
        command = parts[0].lower()
        args = parts[1:]

        if command in ("quit", "exit", "q"):
            print("  Goodbye!")
            break

        handler = COMMANDS.get(command)
        if handler:
            handler(conn, args)
        else:
            print(f"  Unknown command: '{command}'. Type 'help' for available commands.")


def single_command_mode(conn, args):
    """Run a single command from CLI arguments."""
    command = args[0].lower()
    cmd_args = args[1:]

    handler = COMMANDS.get(command)
    if handler:
        handler(conn, cmd_args)
    else:
        print(f"Unknown command: '{command}'. Use 'help' for available commands.")


def main():
    conn = init_db()
    try:
        if len(sys.argv) > 1:
            single_command_mode(conn, sys.argv[1:])
        else:
            interactive_mode(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
