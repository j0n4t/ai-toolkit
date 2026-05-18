import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel

app = FastAPI()

# __file__ is in root/dataset_editor/server.py
# One dirname up gives the project root directory
EDITOR_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(EDITOR_DIR) 
DATASETS_DIR = os.path.join(BASE_DIR, "datasets")

IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp'}

class DescriptionUpdate(BaseModel):
    text: str

if not os.path.exists(DATASETS_DIR):
    os.makedirs(DATASETS_DIR)

# Serves index.html from inside dataset_editor/
@app.get("/", response_class=HTMLResponse)
def read_index():
    index_path = os.path.join(EDITOR_DIR, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return f.read()
    return "index.html not found inside dataset_editor folder."

@app.get("/folders")
def get_folders():
    folders = [f for f in os.listdir(DATASETS_DIR) if os.path.isdir(os.path.join(DATASETS_DIR, f))]
    return sorted(folders)

@app.get("/files/{folder_name}")
def list_images(folder_name: str):
    folder_path = os.path.join(DATASETS_DIR, folder_name)
    if not os.path.exists(folder_path):
        raise HTTPException(status_code=404, detail="Folder not found")
    
    images = [
        f for f in os.listdir(folder_path) 
        if os.path.splitext(f)[1].lower() in IMAGE_EXTENSIONS
    ]
    return sorted(images)

@app.get("/files/{folder_name}/{filename}")
def get_file(folder_name: str, filename: str):
    file_path = os.path.join(DATASETS_DIR, folder_name, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="File not found")

@app.post("/save/{folder_name}/{filename}")
def save_text(folder_name: str, filename: str, data: DescriptionUpdate):
    if ".." in folder_name or ".." in filename or os.path.isabs(filename):
        raise HTTPException(status_code=400, detail="Invalid path")
        
    file_path = os.path.join(DATASETS_DIR, folder_name, filename)
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(data.text)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))