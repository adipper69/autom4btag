# autom4btag

This container build on seanap's auto-m4b tool for audiobook handling. Instead of using beets-audible I made this as a little project. It automatically  organizes audiobooks by tagging `.m4b` and `.mp3` files using anonymous Audible metadata (via Audnexus), and structuring them for use in Audiobookshelf. 

## Features

- Scans `/untagged` folder for new audiobook folders
- Extracts metadata using **Audnexus** (no login required)
- Tags audio files using **Mutagen**
- Moves organized books into `/Author/Series/Book Title/` for organization
- Problem folders are routed to `/fix` for manual cleanup
- Runs every 5 minutes via a loop inside the container

## Volume Mapping (same as auto-m4b)

```sh
Audiobookshelf/
└── Audiobooks/                 # Audiobookshelf default library

temp/
├── recentlyadded/             # Input folder - add new books here
│   ├── book1.m4b
│   ├── book2.mp3
│   └── book3/
│       ├── 01-book3.mp3
│       └── ...
│
├── merge/                     # Folder auto-m4b uses to combine mp3s
│   └── book2/
│       ├── 01-book2.mp3
│       └── ...
│
├── untagged/                  # auto-m4b output folder (autom4btag works here)
│   └── book4/
│       └── book4.m4b
│
├── delete/                    # Needed by auto-m4b (internal use)
│
├── fix/                       # All books with errors go here
│
└── backup/                    # Backups (unused by autom4btag)
    └── book2/
        ├── 01-book2.mp3
        └── ...
```
## Workflow
mp3 files >
auto-m4b >
this program >
audiobookshelf

## Future Work
I should probably build out proper logging of errors but this is good enough for now. 
