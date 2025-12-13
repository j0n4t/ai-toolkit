import os
import base64
import json
import sys
import requests
from pathlib import Path
from PIL import Image

# -----------------------------
# CONFIG
# -----------------------------
KOBOLDCPP_URL = "http://127.0.0.1:5001/v1/chat/completions"
IMAGE_FOLDER  = sys.argv[1] if len(sys.argv) > 1 else "dataset"
OUTPUT_EXT    = ".txt"       # caption save format
MODEL_NAME    = "koboldcpp/google_gemma-3-4b-it-Q6_K_L"    # must match your koboldcpp model id
MAX_TOKENS    = 256          # caption length
PROMPT        = """
You create simple factual image captions for training.
Analyze the following image and generate a detailed, objective description (caption).

Your response must  include:
1.  **What is present:** Identify all objects, people, animals, nature elements, and the main setting.
2.  **Action/Context:** Describe the activity taking place or the situation captured.
3.  **Factual Physical Characteristics:** Details such as colors, shapes, quantity, and spatial location of the elements within the frame.

**Attention:** It is crucial that you DO NOT include any description or analysis of artistic *style*, photographic technique, subjective perceived emotion (unless it is a clear and objective emoji or facial expression), or any aesthetic/dubious/vague judgment. Focus strictly on the visual facts of the scene. Only output the answer.
"""


# -----------------------------
# ENCODING UTIL
# -----------------------------
def img_to_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


# -----------------------------
# SEND REQUEST TO KOBOLDCPP
# -----------------------------
def generate_caption(image_path):
    img_b64 = img_to_base64(image_path)

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": PROMPT
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": "data:image/jpeg;base64,"  + img_b64
                        }
                    }
                ]
            }
        ],
        "max_tokens": MAX_TOKENS,
        "temperature": 0.3
    }

    response = requests.post(KOBOLDCPP_URL, json=payload)

    if response.status_code != 200:
        print(f"[ERROR] {image_path}: {response.text}")
        return None

    data = response.json()
    return data["choices"][0]["message"]["content"].strip()


# -----------------------------
# MAIN LOOP
# -----------------------------
def main():
    image_dir = Path(IMAGE_FOLDER)
    valid_exts = [".jpg", ".jpeg", ".png", ".webp"]

    paths = [p for p in image_dir.iterdir() if p.suffix.lower() in valid_exts]

    print(f"Found {len(paths)} images.")

    for img in paths:
        caption_file = img.with_suffix(OUTPUT_EXT)

        if caption_file.exists():
            print(f"[SKIP] Caption already exists: {caption_file}")
            continue

        print(f"[CAPTION] {img.name}")
        caption = generate_caption(img)

        if caption:
            with open(caption_file, "w", encoding="utf-8") as f:
                f.write(caption)
            print(f" → Saved: {caption_file}")
        else:
            print(f"[FAILED] Could not caption: {img}")


if __name__ == "__main__":
    main()
