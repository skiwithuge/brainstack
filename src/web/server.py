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

@app.get("/", response_class=HTMLResponse)
async def list_files(request: Request, username: str = Depends(verify_credentials)):
    tree = {}
    if os.path.exists(NOTES_DIR):
        for root, _, files in os.walk(NOTES_DIR):
            date_dir = os.path.basename(root)
            if date_dir == os.path.basename(NOTES_DIR):
                continue
            md_files = [f for f in files if f.endswith('.md')]
            if md_files:
                tree[date_dir] = sorted(md_files)
                
    sorted_tree = dict(sorted(tree.items(), reverse=True))
    return templates.TemplateResponse("index.html", {"request": request, "tree": sorted_tree})

@app.get("/view/{date_str}/{filename}", response_class=HTMLResponse)
async def view_file(request: Request, date_str: str, filename: str, username: str = Depends(verify_credentials)):
    filepath = os.path.join(NOTES_DIR, date_str, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")
        
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
        
    html_content = markdown.markdown(content)
    
    return templates.TemplateResponse("view.html", {
        "request": request, 
        "date_str": date_str, 
        "filename": filename, 
        "content": html_content
    })

@app.get("/edit/{date_str}/{filename}", response_class=HTMLResponse)
async def edit_file_get(request: Request, date_str: str, filename: str, username: str = Depends(verify_credentials)):
    filepath = os.path.join(NOTES_DIR, date_str, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")
        
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
        
    return templates.TemplateResponse("edit.html", {
        "request": request, 
        "date_str": date_str, 
        "filename": filename, 
        "content": content
    })

@app.post("/edit/{date_str}/{filename}")
async def edit_file_post(date_str: str, filename: str, content: str = Form(...), username: str = Depends(verify_credentials)):
    filepath = os.path.join(NOTES_DIR, date_str, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")
        
    fixed_content = content.replace('\r\n', '\n')
        
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(fixed_content)
        
    return RedirectResponse(url=f"/view/{date_str}/{filename}", status_code=303)
