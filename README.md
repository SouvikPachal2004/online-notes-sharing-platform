# Online Notes Sharing Platform

A modern Flask-based web app where students can upload, categorize, search, and download study notes.

## Quick Start

```bash
python -m venv venv
# Windows: venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt

# Run the app
export FLASK_APP=app.py  # Windows PowerShell: $env:FLASK_APP="app.py"
flask run --port 5000
# Open http://127.0.0.1:5000
```

## Features
- User registration & login (Flask-Login)
- Upload notes (PDF, DOCX, PPT, images)
- Search by keyword & filter by category
- Download notes, with download counter
- Profile page for managing your uploads

## Project Structure
```
online-notes-platform/
├─ app.py
├─ requirements.txt
├─ README.md
├─ templates/
│  ├─ base.html
│  ├─ index.html
│  ├─ login.html
│  ├─ register.html
│  ├─ upload.html
│  ├─ notes.html
│  └─ profile.html
├─ static/
│  ├─ css/styles.css
│  └─ js/app.js
└─ uploads/  # where files are stored (auto-created)
```

## Default Categories
- Mathematics
- Computer Science
- Physics
- Chemistry
- Biology
- Humanities
- Other

> Tip: To change allowed file types or categories, edit `app.py` (sections marked UPPERCASE comments).
