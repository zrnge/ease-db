# 💾 Ease-DB: Lightweight SQLite Editor



Ease-DB is an **open-source**, user-friendly SQLite database editor built using Python and Tkinter. It provides essential CRUD (Create, Read, Update, Delete) functionality through a simple graphical interface, making SQLite database management accessible and efficient for developers and enthusiasts.

---

## ✨ Features

* **Database Management:** Create new `.db` files or open existing SQLite files.
* **Structured Editing:**
    * Add/Delete rows and columns.
    * Rename tables and columns.
    * In-place cell editing (double-click to modify).
* **Intuitive Interface:**
    * Right-click context menu (Edit functions available directly on the table).
    * Table selection dropdown for easy navigation between multiple tables.
* **Query Execution:** Dedicated text area to run custom SQL queries.
* **Data Handling:** Copy selected cell, row, or column data to the clipboard.
* **Data Export:** Save database structure and data as a new `.db` file or export as an SQL dump (`.sql`).

---

## 🛠️ Installation

### Prerequisites

You need Python 3 installed on your system.

### Steps

1.  **Clone the Repository:**
    ```bash
    git clone [https://github.com/zrnge/ease-db.git](https://github.com/zrnge/ease-db.git)
    cd ease-db
    ```

2.  **Install Dependencies:**
    Ease-DB uses standard Python libraries, primarily `sqlite3` (built-in) and `tkinter` (often built-in), along with the `webbrowser` library. The `requirements.txt` ensures any non-standard or necessary packages are present.
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the Application:**
    ```bash
    python ease_db_main.py # Assuming you name the main file ease_db_main.py
    ```
    *(Note: If you saved the main Python code file with a different name, use that name instead of `ease_db_main.py`.)*

---

## 📜 Dependencies (`requirements.txt`)

Ease-DB relies mainly on libraries bundled with the standard Python distribution. Only `webbrowser` is explicitly imported for documentation links, and `sqlite3`/`tkinter` are standard.

```txt
# Standard Python libraries used in Ease-DB.
# These are typically included with Python installation (Python 3.x).
# Listing them here primarily for clarity.

# tkinter (Graphical User Interface)
# sqlite3 (Database connectivity)
# webbrowser (Opening documentation links)
