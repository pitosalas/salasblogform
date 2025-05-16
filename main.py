from fastapi import FastAPI, Form, File, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import os
from datetime import datetime

app = FastAPI()

POST_DIR = "content/posts"
IMG_DIR = "content/images"

os.makedirs(POST_DIR, exist_ok=True)
os.makedirs(IMG_DIR, exist_ok=True)

app.mount("/images", StaticFiles(directory=IMG_DIR), name="images")


@app.get("/", response_class=HTMLResponse)
def form():
    return """
        <form action="/submit" method="post" enctype="multipart/form-data">
            <input name="title" placeholder="Title"><br>
            <input name="slug" placeholder="Slug"><br>
            <input name="tags" placeholder="Comma-separated tags"><br>
            <textarea name="content" rows="10" cols="60" placeholder="Markdown content"></textarea><br>
            <input type="file" name="image"><br>
            <input type="submit">
        </form>
    """


@app.post("/submit")
async def submit(
    title: str = Form(...),
    slug: str = Form(...),
    tags: str = Form(""),
    content: str = Form(...),
    image = None
):
    date_str = datetime.now().strftime("%Y-%m-%d")
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    filename = f"{slug}.md"
    post_path = os.path.join(POST_DIR, filename)

    # Save uploaded image
    image_url = ""
    print(f"*************** image: {image}")
    # if image is not None:
    #     image_filename : image.filename
    #     image_path = os.path.join(IMG_DIR, image_filename)
    #     with open(image_path, "wb") as f:
    #         f.write(await image.read())
    #     image_url = f"/images/{image_filename}"

    # Generate Markdown content
    with open(post_path, "w") as f:
        f.write(f"---\n")
        f.write(f"title: {title}\n")
        f.write(f"date: {date_str}\n")
        f.write(f"tags: [{', '.join(tag_list)}]\n")
        f.write(f"slug: {slug}\n")
        f.write(f"---\n\n")
        # if image_url:
        #     f.write(f"![image]({image_url})\n\n")
        f.write(content.strip())

    return {"status": "ok", "message": f"Saved {filename}"}