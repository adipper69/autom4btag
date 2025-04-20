# autom4btag

Automatically enrich and organize audiobooks by tagging `.m4b` and `.mp3` files using anonymous Audible metadata (via Audnexus), and structuring them for use in Audiobookshelf.

## Features

- Scans `/untagged` folder for new audiobook folders
- Extracts metadata using **Audnexus** (no login required)
- Tags audio files using **Mutagen**
- Moves organized books into `/Author/Series/Book Title/`
- Problem folders are routed to `/fix` for manual cleanup
- Runs every 5 minutes via a loop inside the container

## Volume Mapping (example)

| Host Path                                      | Container Path                                 |
|-----------------------------------------------|------------------------------------------------|
| `/volume1/Books/Audiobooks/untagged`          | `/volume1/Books/Audiobooks/untagged`           |
| `/volume1/Books/Audiobookshelf/Audiobooks`    | `/volume1/Books/Audiobookshelf/Audiobooks`     |
| `/volume1/Books/Audiobooks/fix`               | `/volume1/Books/Audiobooks/fix`                |

## Docker Usage

Build the container:
```bash
docker build -t autom4btag .
