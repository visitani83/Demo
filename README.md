# Expense Tracker Agent

A simple CLI-based expense tracker that automatically categorizes your spending.

## Features

- **Auto-categorization** — Expenses are automatically assigned a category based on keywords in the description
- **SQLite storage** — All data is persisted locally in `expenses.db`
- **Visual summaries** — Bar chart breakdowns by category and by month
- **Search** — Find past expenses by description
- **No dependencies** — Uses only Python standard library

## Quick Start

```bash
# Interactive mode
python expense_tracker.py

# Or run a single command directly
python expense_tracker.py add 12.50 Coffee at Starbucks
python expense_tracker.py list
python expense_tracker.py summary
```

## Commands

| Command | Description |
|---------|-------------|
| `add <amount> <desc> [--category CAT] [--date YYYY-MM-DD]` | Add an expense |
| `list [N]` | Show last N expenses (default 20) |
| `summary [YYYY-MM]` | Spending breakdown by category |
| `monthly` | Month-by-month overview |
| `search <query>` | Search expenses by description |
| `delete <id>` | Remove an expense |
| `categories` | List all categories |
| `help` | Show help |

## Categories

Expenses are auto-categorized into:

- Food & Dining
- Transport
- Shopping
- Bills & Utilities
- Entertainment
- Health
- Education
- Personal Care
- Gifts & Donations
- Other (fallback)

You can always override with `--category "Your Category"`.

## Examples

```bash
# Auto-categorized as "Food & Dining"
python expense_tracker.py add 8.50 Lunch at restaurant

# Manually categorized
python expense_tracker.py add 200 New headphones --category Shopping

# Backdate an expense
python expense_tracker.py add 50 Gym membership --date 2025-01-15

# View this month's summary
python expense_tracker.py summary 2025-02

# Search for all coffee expenses
python expense_tracker.py search coffee
```
