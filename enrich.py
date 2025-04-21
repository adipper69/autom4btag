import os
import shutil
import json
import requests
import time
import re
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

def clean_title(text):
    # Remove leading track numbers like "01 of 10 - " or "01 - "
    return re.sub(r'^\s*\d{1,2}( of \d{1,2})?[\s\-–:]+', '', text).strip()

def extract_tags_from_m4b(file_path):
    try:
        audio = MP4(file_path)
        title = audio.get("\xa9alb", [""])[0]  # Album = Book Title
        author = audio.get("aART", [""]) or audio.get("\xa9ART", [""])
        author = author[0] if author else ""
        return title.strip(), author.strip()
    except Exception as e:
        print(f"⚠️ Failed to extract embedded tags: {e}")
        return None, None

def get_main_audio_file(path):
    audio_files = [f for f in os.listdir(path) if os.path.splitext(f)[1].lower() in AUDIO_EXTENSIONS]
    if not audio_files:
        return None
    return max(audio_files, key=lambda f: os.path.getsize(os.path.join(path, f)))

def query_audnexus(title):
    url = f"https://api.audnex.us/lookup?term={title}&type=all"
    print(f"🔎 Querying metadata for: {title}")
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        items = r.json().get("items", [])
        if not items:
            print(f"⚠️ No metadata found for: {title}")
        return items
    except requests.RequestException as e:
        print(f"❌ Metadata lookup failed for '{title}': {e}")
        return []

def download_cover(cover_url):
    r = requests.get(cover_url)
    if r.status_code != 200:
        return None
    return r.content

def tag_audio(file_path, metadata, cover_bytes):
    try:
        ext = os.path.splitext(file_path)[1].lower()
        print(f"🏷 Tagging: {file_path}")
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
    except Exception as e:
        raise Exception(f"❌ Failed tagging {file_path}: {e}")

def move_to_fix(src_path):
    dest = os.path.join(FIX_DIR, os.path.basename(src_path))
    print(f"📦 Moving to fix: {src_path} → {dest}")
    shutil.move(src_path, dest)

def process_folder(folder_path):
    print(f"📚 Processing: {folder_path}")
    audio_file = get_main_audio_file(folder_path)
    if not audio_file:
        print(f"⚠️ No audio file found in {folder_path}")
        return move_to_fix(folder_path)

    audio_path = os.path.join(folder_path, audio_file)

    # Step 1: Try to extract embedded tags
    title, author = extract_tags_from_m4b(audio_path)
    if not title:
        print("❌ No title found in tags. Moving to fix.")
        return move_to_fix(folder_path)

    query = title
    results = query_audnexus(query)

    # Step 2: Match author if available
    metadata_raw = None
    if results:
        for item in results:
          if author and author.lower() in item.get("author", "").lower():
                metadata_raw = item
                print(f"🎯 Author match found: {item['title']} by {item['author']}")
                break

    # Step 3: Fallback to first result if no author matched
    if not metadata_raw and results:
        metadata_raw = results[0]
        print(f"⚠️ No author match. Using first result: {metadata_raw['title']} by {metadata_raw['author']}")

    # Step 4: Still nothing? Crash out
    if not metadata_raw:
        print("❌ Audnexus lookup failed even after fallback. Moving to fix.")
        return move_to_fix(folder_path)

    # Step 5: Build metadata from Audnexus response
    metadata = {
        "title": metadata_raw.get("title", title or "Unknown Title"),
        "author": metadata_raw.get("author", author or "Unknown Author"),
        "series": metadata_raw.get("series", "Standalone")
    }

    print(f"✅ Metadata found: {metadata['title']} by {metadata['author']} (Series: {metadata['series']})")

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
