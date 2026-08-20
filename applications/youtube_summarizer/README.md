# YouTube Video Summarizer

Paste a YouTube video URL and get a standalone HTML page — named after the
video's title — containing just the **key takeaways as a bulleted list**.
Available as a local **web app** (Flask, open in your browser), a desktop
**GUI** (Tkinter), a **command-line** tool, and a reusable Python library.

## How it works

1. The video id is parsed out of the URL.
2. Title/author are fetched from YouTube's public `oEmbed` endpoint (no API key required).
3. The video's transcript/captions are fetched with the [`youtube-transcript-api`](https://pypi.org/project/youtube-transcript-api/) package.
4. The transcript is split into sentences and each sentence is scored by the
   normalized frequency of its (non-stopword) words — a simple, dependency-free
   extractive summarization technique. The highest-scoring sentences become the
   key takeaways.
5. The keynotes are written out as an HTML page titled after the video, saved
   as `<sanitized video title>.html`.

No external LLM/API key is required — everything runs locally once the
transcript has been downloaded.

## Requirements

* The video must have captions/subtitles available (either uploaded or
  auto-generated) for a transcript to be fetched.
* `tkinter` for the GUI — included with most Python installs; on Debian/Ubuntu
  install it with `sudo apt-get install python3-tk` if it's missing.

## Setup

```bash
pip install -r requirements.txt
```

## Usage

### Web app (recommended)

```bash
python app.py
```

Then open **http://127.0.0.1:5000** in your browser. Paste a YouTube URL and
click **Generate** — the key takeaways are shown on the page, and an HTML
file named after the video's title is saved to the `output/` folder (also
reachable via the "Open saved HTML page" link).

### GUI

```bash
python gui.py
```

1. Paste a YouTube URL (e.g. `https://www.youtube.com/watch?v=dQw4w9WgXcQ`).
2. Optionally choose an output folder (defaults to the current directory).
3. Click **Generate**. The key takeaways appear in the window, and an HTML
   file named after the video's title is saved to the chosen folder.
4. Click **Open HTML** to view it in your browser.

### Command line

```bash
python youtube_summarizer.py
```

You'll be prompted to paste a YouTube URL, and both the key takeaways and a
paragraph summary are printed to the terminal.

### As a library

```python
from youtube_summarizer import extract_video_id, get_video_metadata, get_transcript, summarize, save_keynotes_html

url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
metadata = get_video_metadata(url)
transcript = get_transcript(extract_video_id(url))
_, keynotes = summarize(transcript, num_keynotes=8)

filepath = save_keynotes_html(metadata["title"], keynotes, output_dir=".")
print("Saved to", filepath)
```
