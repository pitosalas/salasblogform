#!/usr/bin/env python3
# Authors: Pito Salas and ChatGPT
# License: MIT
# File: main.py
# Version: 1.0
# Last revised: 2025-05-16

from fastapi import FastAPI, Form, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from datetime import datetime
from pathlib import Path
import os
import subprocess
import shutil
import urllib.parse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

app = FastAPI()

# Local directories for staging content
POST_DIR = Path("content/posts")
IMG_DIR = Path("content/images")

# Remote blog repo
REPO_URL = "https://github.com/pitosalas/salasblog.git"
REPO_DIR = Path("tmp")

# Ensure local directories exist
POST_DIR.mkdir(parents=True, exist_ok=True)
IMG_DIR.mkdir(parents=True, exist_ok=True)

# Serve uploaded images
app.mount("/images", StaticFiles(directory=IMG_DIR), name="images")
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
def show_form(request: Request):
    return templates.TemplateResponse("form.html", {"request": request})

@app.post("/submit")
async def submit(
    title: str = Form(...),
    content: str = Form(...),
    image: UploadFile = File(None)
):
    print(f"form submission: {title}, {content[:20]}..., ")
    
    # Validate inputs
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}.md"
    post_path = POST_DIR / filename

    # Save the image (if provided)
    image_url = ""
    image_data = None
    image_filename = None
    if image and image.filename:
        image_filename = image.filename
        image_path = IMG_DIR / image_filename
        image_data = await image.read()
        image_path.write_bytes(image_data)
        image_url = f"/images/{image_filename}"

    # Compose Markdown content
    md_lines = [
        "---",
        f"title: {title}",
        f"date: {date_str}",
        "---",
        "",
    ]
    if image_url:
        md_lines.append(f"![image]({image_url})")
        md_lines.append("")
    md_lines.append(content.strip())

    post_content = "\n".join(md_lines)
    post_path.write_text(post_content)

    # Push to GitHub Pages blog repo
    print("pushing to GitHub Pages")
    try:
        commit_to_blog_repo(filename, post_content, image_data, image_filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Git commit failed: {e}")
    return RedirectResponse(url="https://pitosalas.github.io/salasblog", status_code=303)

def commit_to_blog_repo(filename: str, content: str, image_data=None, image_filename=None):
    token = os.getenv("GH_TOKEN")
    print("token: ", token)    
    if not token:
        raise RuntimeError("GH_TOKEN not set in environment")

    # Authenticated clone URL
    token_encoded = urllib.parse.quote(token)
    auth_url = f"https://{token_encoded}@github.com/pitosalas/salasblog.git"
    print(f"auth_url: {auth_url}, repo_dir: {REPO_DIR}")

    # Clean clone
    if REPO_DIR.exists():
        shutil.rmtree(REPO_DIR)
    print(f"COMMAND: git clone {auth_url} {REPO_DIR}")
    subprocess.run(["git", "clone", auth_url, str(REPO_DIR)], check=True)
    print("cloned repo")
    posts_dir = REPO_DIR / "content/posts"
    images_dir = REPO_DIR / "content/images"
    posts_dir.mkdir(parents=True, exist_ok=True)
    images_dir.mkdir(parents=True, exist_ok=True)

    # Save Markdown
    (posts_dir / filename).write_text(content)

    # Save image if provided
    if image_data and image_filename:
        (images_dir / image_filename).write_bytes(image_data)

    print(f"Committing {filename} to {REPO_URL} with {token}")

    # Commit and push
    # Set up Git config
    subprocess.run(["git", "-C", str(REPO_DIR), "config", "--global", "user.email", "pitosalas@gmail.com"], check=True)
    print("git config email")
    subprocess.run(["git", "-C", str(REPO_DIR), "config", "--global", "user.name", "Pito Salas"], check=True)
    
    print("git add")
    subprocess.run(["git", "-C", str(REPO_DIR), "add", "."], check=True)

    print("git commit")
    subprocess.run(["git", "-C", str(REPO_DIR), "commit", "-m", f"Add blog post {filename}"], check=True)

    print("git push")
    subprocess.run(["git", "-C", str(REPO_DIR), "push"], check=True)
