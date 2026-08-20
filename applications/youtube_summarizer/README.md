# YouTube Video Summarizer

A small command-line application that takes a YouTube video URL and prints:

* the video's **title** and **author/channel name**
* a bulleted list of **key takeaways** (the most important sentences)
* a short **summary** of the whole video

## How it works

1. The video id is parsed out of the URL.
2. Title/author are fetched from YouTube's public `oEmbed` endpoint (no API key required).
3. The video's transcript/captions are fetched with the [`youtube-transcript-api`](https://pypi.org/project/youtube-transcript-api/) package.
4. The transcript is split into sentences and each sentence is scored by the
   normalized frequency of its (non-stopword) words — a simple, dependency-free
   extractive summarization technique. The highest-scoring sentences become the
   key takeaways, and the top sentences (restored to their original order)
   become the summary paragraph.

No external LLM/API key is required — everything runs locally once the
transcript has been downloaded.

## Requirements

* The video must have captions/subtitles available (either uploaded or
  auto-generated) for a transcript to be fetched.

## Setup

```bash
pip install -r requirements.txt
```

## Usage

```bash
python youtube_summarizer.py
```

You'll be prompted to paste a YouTube URL, e.g. `https://www.youtube.com/watch?v=dQw4w9WgXcQ`
or `https://youtu.be/dQw4w9WgXcQ`.

You can also use it as a library:

```python
from youtube_summarizer import summarize_youtube_video

result = summarize_youtube_video("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
print(result["title"], result["author"])
print(result["keynotes"])
print(result["summary"])
```
