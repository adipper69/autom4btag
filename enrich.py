import os
import shutil
import json
import requests
import time
from mutagen.mp4 import MP4, MP4Cover
from mutagen.easyid3 import EasyID3

UNTAGGED_DIR = "/data/untagged"
FIX_DIR = "/data/fix"
OUTPUT_BASE = "/data/output"

AUDIO_EXTENSIONS = [".m4b", ".mp3"]

def is_safe_to_process(folder_path):
    # 1. Skip if folder is less than 2 minutes old
    age = time.time() - os.path.getmtime(folder_path)
    if age < 120:
        print(f"⏳ Skipping (too new): {folder_path}")
        return False

    # 2. Skip if folder has "-tmpfiles" in the name
    if "-tmpfiles" in os.path.basename(folder_path).lower():
        print(f"🛑 Skipping (in progress): {folder_path}")
        return False

    return True

def get_main_audio_file(path):
    audio_files = [f for f in os.listdir(path) if os.path.splitext(f)[1].lower() in AUDIO_EXTENSIONS]
    if not audio_files:
        return None
    return max(audio_files, key=lambda f: os.path.getsize(os.path.join(path, f)))

def query_audnexus(title):
    url = f"https://api.audnex.us/lookup?term={title}&type=all"
    r = requests.get(url)
    if r.status_code != 200:
        return None
    try:
        items = r.json().get("items", [])
        return items[0] if items else None
    except json.JSONDecodeError:
        return None

def download_cover(cover_url):
    r = requests.get(cover_url)
    if r.status_code != 200:
        return None
    return r.content

def tag_audio(file_path, metadata, cover_bytes):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".m4b":
        audio = MP4(file_path)
        audio["\xa9nam"] = metadata["title"]
        audio["\xa9ART"] = metadata["author"]
        audio["\xa9alb"] = metadata["series"]
        if cover_bytes:
            audio["covr"] = [MP4Cover(cover_bytes, imageformat=MP4Cover.FORMAT_JPEG)]
        audio.save()
    elif ext == ".mp3":
        audio = EasyID3(file_path)
        audio["title"] = metadata["title"]
        audio["artist"] = metadata["author"]
        audio["album"] = metadata["series"]
        audio.save()

def move_to_fix(src_path):
    dest = os.path.join(FIX_DIR, os.path.basename(src_path))
    shutil.move(src_path, dest)
    print(f"❌ Moved to fix: {src_path}")

def process_folder(folder_path):
    print(f"📚 Processing: {folder_path}")
    audio_file = get_main_audio_file(folder_path)
    if not audio_file:
        return move_to_fix(folder_path)

    guessed_title = os.path.splitext(audio_file)[0]
    metadata_raw = query_audnexus(guessed_title)
    if not metadata_raw:
        return move_to_fix(folder_path)

    metadata = {
        "title": metadata_raw.get("title", "Unknown Title"),
        "author": metadata_raw.get("author", "Unknown Author"),
        "series": metadata_raw.get("series", "Standalone")
    }

    cover_url = metadata_raw.get("coverUrl")
    cover_bytes = download_cover(cover_url) if cover_url else None

    for f in os.listdir(folder_path):
        if os.path.splitext(f)[1].lower() in AUDIO_EXTENSIONS:
            try:
                tag_audio(os.path.join(folder_path, f), metadata, cover_bytes)
            except Exception as e:
                print(f"❌ Tag error on {f}: {e}")
                return move_to_fix(folder_path)

    dest_path = os.path.join(
        OUTPUT_BASE,
        metadata["author"].strip(),
        metadata["series"].strip(),
        metadata["title"].strip()
    )

    os.makedirs(dest_path, exist_ok=True)
    shutil.move(folder_path, dest_path)
    print(f"✅ Moved to: {dest_path}")

def main():
    for entry in os.listdir(UNTAGGED_DIR):
        full_path = os.path.join(UNTAGGED_DIR, entry)
        if os.path.isdir(full_path) and is_safe_to_process(full_path):
            try:
                process_folder(full_path)
            except Exception as e:
                print(f"❌ Unexpected error: {e}")
                move_to_fix(full_path)

if __name__ == "__main__":
    main()
