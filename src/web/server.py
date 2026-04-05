import os
import markdown
import logging
from fastapi import FastAPI, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets

from src.core.config import NOTES_DIR, WEB_PASSWORD

logger = logging.getLogger(__name__)

app = FastAPI(title="Brainstack Web")
security = HTTPBasic()
templates = Jinja2Templates(directory="src/web/templates")

def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    is_correct_username = secrets.compare_digest(credentials.username, "admin")
    is_correct_password = secrets.compare_digest(credentials.password, WEB_PASSWORD)
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

def _safe_path(file_path: str) -> str:
    """Resolves file_path under NOTES_DIR and guards against path traversal."""
    real_notes = os.path.realpath(NOTES_DIR)
    full_path = os.path.realpath(os.path.join(NOTES_DIR, file_path))
    if not full_path.startswith(real_notes + os.sep):
        raise HTTPException(status_code=403, detail="Access denied")
    return full_path

@app.get("/", response_class=HTMLResponse)
async def list_files(request: Request, username: str = Depends(verify_credentials)):
    tree = {}
    if os.path.exists(NOTES_DIR):
        for root, _, files in os.walk(NOTES_DIR):
            rel_dir = os.path.relpath(root, NOTES_DIR)
            if rel_dir == ".":
                continue
            md_files = [f for f in sorted(files) if f.endswith('.md')]
            if md_files:
                tree[rel_dir] = md_files

    # Reverse sort: most recent dates first; memory/ entries sort naturally
    sorted_tree = dict(sorted(tree.items(), reverse=True))
    return templates.TemplateResponse(request=request, name="index.html", context={"request": request, "tree": sorted_tree})

@app.get("/view/{file_path:path}", response_class=HTMLResponse)
async def view_file(request: Request, file_path: str, username: str = Depends(verify_credentials)):
    filepath = _safe_path(file_path)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    html_content = markdown.markdown(content)

    return templates.TemplateResponse(request=request, name="view.html", context={
        "request": request,
        "file_path": file_path,
        "filename": os.path.basename(file_path),
        "content": html_content
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
        "file_path": file_path,
        "filename": os.path.basename(file_path),
        "content": content
    })

@app.post("/edit/{file_path:path}")
async def edit_file_post(file_path: str, content: str = Form(...), username: str = Depends(verify_credentials)):
    filepath = _safe_path(file_path)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")

    fixed_content = content.replace('\r\n', '\n')

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(fixed_content)

    return RedirectResponse(url=f"/view/{file_path}", status_code=303)

