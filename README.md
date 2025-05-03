# Context-Aware Logging CLI Framework

A modular, context-aware logging framework for CLI applications written in Python — powered by [Rich](https://github.com/Textualize/rich) for beautiful output, and SQLite for persistent logging.  
Includes full context stack management, secure state control via tokens, and structured log export features.

![Richdisplay Logo](assets/img/richdisplay.png "Richdisplay Logo")

---

## 🔥 Features

- ✅ Rich-based CLI logging with color, level, and formatting
- ✅ Context-managed debug/log/database state (`SysContext`)
- ✅ Secure token-authenticated argument context (`ArgsContext`)
- ✅ Stack-based context separation (supports nesting)
- ✅ SQLite-based log storage with automatic DB lifecycle
- ✅ Export to JSON or CSV via CLI
- ✅ Modular class architecture (SRP & SOLID-principled)
- ✅ Zero external dependencies beyond `rich`

---

## 📦 Project Structure

```plaintext
src/
├── display/
│ ├── core/ # Display & LogControl core classes 
│ ├── database/ # SQLite backend logic 
│ ├── exporters/ # CSV / JSON log exporters 
│ ├── utils/ # Custom formatters 
│ └── state.py # Token-based context stack management 
├── run.py # Entry point
```

## 🐍 Dependencies

- `rich` (for beautiful CLI output)

That's it. No SQLAlchemy. No pandas. No click. No nonsense.
All other functionality — token management, argument parsing, DB logging, exporting — is written in clean, native Python.


## 🚀 Getting Started

### 1. Create & activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the CLI

```bash
python src/run.py
```

🛠 CLI Options

```bash
usage: run.py [-h] [-c] [-dbp DB_PATH] [-db] [-d] [-gl GET_LOGS] [-ll LOG_LEVEL] [-e EXPORT]

optional arguments:
  -c,  --clear         Clear the database
  -dbp, --db_path      Specify database path (default: logs.db)
  -db, --db            Enable logging to database
  -d,  --debug         Enable debug mode
  -gl, --get-logs      Fetch logs from the database (by level)
  -ll, --log-level     Set logging level (10-DEBUG, 20-INFO, 30-ERROR, etc.)
  -e,  --export        Export logs to file (json or csv)
  -h,  --help           Show this help message and exit
```

📚 Examples
Log to console only:

```bash
python src/run.py
```

Log to console and database, then export:

```bash
python src/run.py --db --export json
```

Fetch logs at INFO level (20):

```bash
python src/run.py --get-logs 20
```

## 🔐 Context Management

Both SysContext and ArgsContext are stack-based and protected by secure tokens managed by AuthManager.

This ensures:

- Separation of concerns

- Predictable behavior in nested or concurrent executions

- Strict token-bound lifecycle handling

## Testing & Extensibility

Unit tests can easily be written by mocking LogDB, AuthManager, or wrapping Display in test contexts.

The framework is highly extensible — just plug in new exporters, replace the storage backend, or integrate with other services.

## ✨ Credits

Created by someone who got up too early and had too much time to think. 😉
If you find this useful, please consider giving it a star! ⭐️
