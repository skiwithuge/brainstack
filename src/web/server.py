import os
import glob
import re
import markdown
import logging
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import secrets

from src.core.config import NOTES_DIR, MEMORY_DIR, WEB_PASSWORD
from src.llm import tag_service

logger = logging.getLogger(__name__)

app = FastAPI(title="Brainstack Web")
templates = Jinja2Templates(directory="src/web/templates")

SESSION_TOKEN = secrets.token_urlsafe(32)

class RequiresLoginException(Exception):
    pass

@app.exception_handler(RequiresLoginException)
async def requires_login_exception_handler(request: Request, exc: RequiresLoginException):
    return RedirectResponse(url="/login")

_ARTIFACT_DEFS = [
    {"suffix": "_lineage.md",  "label": "Lineage",  "icon": "📋"},
    {"suffix": "_actions.md",  "label": "Actions",  "icon": "✅"},
    {"suffix": "_drafts.md",   "label": "Drafts",   "icon": "✍️"},
    {"suffix": "_analysis.md", "label": "Analysis", "icon": "🔍"},
]

def verify_credentials(request: Request):
    if request.cookies.get("session_id") != SESSION_TOKEN:
        raise RequiresLoginException()
    return "admin"

@app.get("/login", response_class=HTMLResponse)
async def login_get(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")

@app.post("/login", response_class=HTMLResponse)
async def login_post(request: Request, username: str = Form(""), password: str = Form("")):
    if secrets.compare_digest(username, "admin") and secrets.compare_digest(password, WEB_PASSWORD):
        response = RedirectResponse(url="/", status_code=303)
        response.set_cookie(key="session_id", value=SESSION_TOKEN, httponly=True)
        return response
    
    return templates.TemplateResponse(
        request=request, 
        name="login.html", 
        context={"request": request, "error_message": "Invalid username or password"}
    )

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("session_id")
    return response

def _safe_path(file_path: str) -> str:
    """Resolves file_path under NOTES_DIR and guards against path traversal."""
    real_notes = os.path.realpath(NOTES_DIR)
    full_path = os.path.realpath(os.path.join(NOTES_DIR, file_path))
    if not full_path.startswith(real_notes + os.sep):
        raise HTTPException(status_code=403, detail="Access denied")
    return full_path

def _greeting() -> str:
    h = datetime.now().hour
    if h < 12: return "morning"
    if h < 18: return "afternoon"
    return "evening"

# ── Dashboard ─────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, username: str = Depends(verify_credentials)):
    today_str = datetime.now().strftime("%Y-%m-%d")

    focus_path = os.path.join(MEMORY_DIR, "focus.md")
    focus_html = None
    if os.path.exists(focus_path):
        with open(focus_path, "r", encoding="utf-8") as f:
            focus_html = markdown.markdown(f.read())

    latest_weekly = None
    weekly_dir = os.path.join(MEMORY_DIR, "weekly")
    if os.path.exists(weekly_dir):
        reports = sorted(glob.glob(os.path.join(weekly_dir, "*_report.md")))
        if reports:
            fname = os.path.basename(reports[-1])
            latest_weekly = {
                "name": fname.replace("_report.md", ""),
                "file_path": f"memory/weekly/{fname}",
            }

    return templates.TemplateResponse(request=request, name="dashboard.html", context={
        "request": request,
        "active": "home",
        "today_str": today_str,
        "focus_html": focus_html,
        "latest_weekly": latest_weekly,
        "greeting": _greeting(),
    })

# ── Memory Wiki ───────────────────────────────────────────────────────────────

@app.get("/memory", response_class=HTMLResponse)
async def memory_section(request: Request, username: str = Depends(verify_credentials)):
    wiki_pages = [
        {"name": "Goals",       "file": "goals.md",       "icon": "🎯", "desc": "Evolving goals and progress"},
        {"name": "Patterns",    "file": "patterns.md",    "icon": "🔄", "desc": "Recurring themes and habits"},
        {"name": "Open Loops",  "file": "open_loops.md",  "icon": "🔓", "desc": "Unresolved action items"},
        {"name": "Log",         "file": "log.md",         "icon": "📋", "desc": "Append-only audit trail"},
    ]
    for page in wiki_pages:
        page["exists"] = os.path.exists(os.path.join(MEMORY_DIR, page["file"]))
        page["file_path"] = f"memory/{page['file']}"

    return templates.TemplateResponse(request=request, name="memory.html", context={
        "request": request,
        "active": "memory",
        "wiki_pages": wiki_pages,
    })

# ── Tags ───────────────────────────────────────────────────────────────────────

@app.get("/tags", response_class=HTMLResponse)
async def tags_page(request: Request, username: str = Depends(verify_credentials)):
    tag_index = tag_service.collect_all_tags()
    return templates.TemplateResponse(request=request, name="tags.html", context={
        "request": request,
        "active": "tags",
        "tag_index": tag_index,
        "total_tags": len(tag_index),
    })

# ── Daily List ────────────────────────────────────────────────────────────────

@app.get("/daily", response_class=HTMLResponse)
async def daily_list(request: Request, username: str = Depends(verify_credentials)):
    dates = []
    if os.path.exists(NOTES_DIR):
        for entry in sorted(os.listdir(NOTES_DIR), reverse=True):
            folder = os.path.join(NOTES_DIR, entry)
            if not (os.path.isdir(folder) and re.match(r'^\d{4}-\d{2}-\d{2}$', entry)):
                continue
            artifacts = [f for f in os.listdir(folder)
                         if f.endswith('.md') and os.path.isfile(os.path.join(folder, f))]
            raw_folder = os.path.join(folder, "raw")
            raw_count = len([f for f in os.listdir(raw_folder) if f.endswith('.md')]) \
                if os.path.exists(raw_folder) else 0
            if artifacts or raw_count:
                dates.append({"date": entry, "count": len(artifacts), "raw_count": raw_count})

    return templates.TemplateResponse(request=request, name="daily_list.html", context={
        "request": request,
        "active": "daily",
        "dates": dates,
    })

# ── Day View ──────────────────────────────────────────────────────────────────

@app.get("/daily/{date_str}", response_class=HTMLResponse)
async def daily_day(request: Request, date_str: str, username: str = Depends(verify_credentials)):
    if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
        raise HTTPException(status_code=400, detail="Invalid date format")

    folder = os.path.join(NOTES_DIR, date_str)
    if not os.path.isdir(folder):
        raise HTTPException(status_code=404, detail="No notes for this date")

    artifacts = []
    for a in _ARTIFACT_DEFS:
        filename = f"{date_str}{a['suffix']}"
        if os.path.exists(os.path.join(folder, filename)):
            artifacts.append({**a, "filename": filename, "file_path": f"{date_str}/{filename}"})

    raw_folder = os.path.join(folder, "raw")
    raw_files = []
    if os.path.exists(raw_folder):
        raw_files = [
            {"name": f, "file_path": f"{date_str}/raw/{f}"}
            for f in sorted(os.listdir(raw_folder)) if f.endswith('.md')
        ]

    return templates.TemplateResponse(request=request, name="daily_day.html", context={
        "request": request,
        "active": "daily",
        "date_str": date_str,
        "artifacts": artifacts,
        "raw_files": raw_files,
    })

# ── Reports ───────────────────────────────────────────────────────────────────

@app.get("/reports", response_class=HTMLResponse)
async def reports_section(request: Request, username: str = Depends(verify_credentials)):
    def get_reports(subdir: str):
        d = os.path.join(MEMORY_DIR, subdir)
        if not os.path.exists(d):
            return []
        return [
            {"name": os.path.basename(f).replace("_report.md", ""),
             "file_path": f"memory/{subdir}/{os.path.basename(f)}"}
            for f in sorted(glob.glob(os.path.join(d, "*.md")), reverse=True)
        ]

    return templates.TemplateResponse(request=request, name="reports.html", context={
        "request": request,
        "active": "reports",
        "weekly": get_reports("weekly"),
        "monthly": get_reports("monthly"),
        "annual": get_reports("annual"),
    })

# ── View / Edit (unchanged routing, updated templates) ────────────────────────

@app.get("/view/{file_path:path}", response_class=HTMLResponse)
async def view_file(request: Request, file_path: str, username: str = Depends(verify_credentials)):
    filepath = _safe_path(file_path)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    return templates.TemplateResponse(request=request, name="view.html", context={
        "request": request,
        "active": "",
        "file_path": file_path,
        "filename": os.path.basename(file_path),
        "content": markdown.markdown(content),
    })

@app.get("/edit/{file_path:path}", response_class=HTMLResponse)
async def edit_file_get(request: Request, file_path: str, username: str = Depends(verify_credentials)):
    filepath = _safe_path(file_path)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    return templates.TemplateResponse(request=request, name="edit.html", context={
        "request": request,
        "active": "",
        "file_path": file_path,
        "filename": os.path.basename(file_path),
        "content": content,
    })

@app.post("/edit/{file_path:path}")
async def edit_file_post(file_path: str, content: str = Form(...), username: str = Depends(verify_credentials)):
    filepath = _safe_path(file_path)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content.replace('\r\n', '\n'))

    return RedirectResponse(url=f"/view/{file_path}", status_code=303)
