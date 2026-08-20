"""
YouTube Video Summarizer
========================

Takes a YouTube video URL, fetches its transcript, and produces:
  * the video's title and author/channel name
  * a short list of "keynotes" (the most important sentences)
  * a paragraph-style summary of the whole video

Fetches metadata via YouTube's public oEmbed endpoint (no API key needed)
and the transcript via the `youtube-transcript-api` package. Summarization
is done with a lightweight, dependency-free extractive algorithm: sentences
are scored by the frequency of their (non-stopword) words, and the
highest-scoring sentences are selected for the keynotes/summary.

Install dependencies:
    pip install -r requirements.txt

Usage:
    python youtube_summarizer.py
    (then paste a YouTube URL when prompted)
"""

import json
import re
import sys
import urllib.parse
import urllib.request
from collections import Counter
from urllib.error import HTTPError, URLError

try:
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api._errors import NoTranscriptFound, TranscriptsDisabled
except ImportError:
    YouTubeTranscriptApi = None

STOPWORDS = set(
    """a about above after again against all am an and any are aren't as at be
    because been before being below between both but by can't cannot could
    couldn't did didn't do does doesn't doing don't down during each few for
    from further had hadn't has hasn't have haven't having he he'd he'll he's
    her here here's hers herself him himself his how how's i i'd i'll i'm
    i've if in into is isn't it it's its itself let's me more most mustn't
    my myself no nor not of off on once only or other ought our ours
    ourselves out over own same shan't she she'd she'll she's should
    shouldn't so some such than that that's the their theirs them
    themselves then there there's these they they'd they'll they're they've
    this those through to too under until up very was wasn't we we'd we'll
    we're we've were weren't what what's when when's where where's which
    while who who's whom why why's with won't would wouldn't you you'd
    you'll you're you've your yours yourself yourselves""".split()
)

VIDEO_ID_PATTERN = re.compile(
    r"(?:v=|\/videos\/|embed\/|youtu\.be\/|\/v\/|\/e\/|watch\?v=|\/watch\?.*v=)([^#&?\n]{11})"
)


def extract_video_id(url: str) -> str:
    """Extract the 11-character YouTube video id from a URL.

    >>> extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    'dQw4w9WgXcQ'
    >>> extract_video_id("https://youtu.be/dQw4w9WgXcQ")
    'dQw4w9WgXcQ'
    >>> extract_video_id("not a url")
    Traceback (most recent call last):
        ...
    ValueError: Could not extract a video id from URL: not a url
    """
    match = VIDEO_ID_PATTERN.search(url)
    if match:
        return match.group(1)
    raise ValueError(f"Could not extract a video id from URL: {url}")


def get_video_metadata(url: str) -> dict:
    """Fetch the video title and channel/author name via YouTube's oEmbed API."""
    oembed_url = "https://www.youtube.com/oembed?" + urllib.parse.urlencode(
        {"url": url, "format": "json"}
    )
    try:
        with urllib.request.urlopen(oembed_url, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
        return {
            "title": data.get("title", "Unknown title"),
            "author": data.get("author_name", "Unknown author"),
        }
    except (URLError, HTTPError, ValueError):
        return {"title": "Unknown title", "author": "Unknown author"}


def get_transcript(video_id: str) -> str:
    """Fetch and flatten the video transcript into a single string of text."""
    if YouTubeTranscriptApi is None:
        raise ImportError(
            "youtube-transcript-api is required. Install with: "
            "pip install youtube-transcript-api"
        )
    try:
        segments = YouTubeTranscriptApi.get_transcript(video_id)
    except TranscriptsDisabled as exc:
        raise RuntimeError("Transcripts are disabled for this video.") from exc
    except NoTranscriptFound as exc:
        raise RuntimeError("No transcript could be found for this video.") from exc
    return " ".join(segment["text"].strip() for segment in segments if segment["text"].strip())


def split_sentences(text: str) -> list:
    """Split text into sentences on ., !, or ? followed by whitespace."""
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def score_sentences(sentences: list) -> list:
    """Score each sentence by the average normalized frequency of its words."""
    word_freq = Counter()
    for sentence in sentences:
        for word in re.findall(r"[a-z']+", sentence.lower()):
            if word not in STOPWORDS:
                word_freq[word] += 1

    if not word_freq:
        return [0.0] * len(sentences)

    max_freq = max(word_freq.values())
    normalized_freq = {word: count / max_freq for word, count in word_freq.items()}

    scores = []
    for sentence in sentences:
        words = re.findall(r"[a-z']+", sentence.lower())
        if not words:
            scores.append(0.0)
            continue
        scores.append(sum(normalized_freq.get(word, 0.0) for word in words) / len(words))
    return scores


def summarize(text: str, num_summary_sentences: int = 5, num_keynotes: int = 5):
    """Return (summary, keynotes) extracted from the given text.

    `summary` is the top-scoring sentences joined in their original order.
    `keynotes` is the top-scoring sentences ordered by importance (highest first).
    """
    sentences = split_sentences(text)
    if not sentences:
        return "", []

    scores = score_sentences(sentences)
    ranked_indices = sorted(range(len(sentences)), key=lambda i: scores[i], reverse=True)

    summary_indices = sorted(ranked_indices[: min(num_summary_sentences, len(sentences))])
    summary = " ".join(sentences[i] for i in summary_indices)

    keynote_count = min(num_keynotes, len(sentences))
    keynote_indices = ranked_indices[:keynote_count]
    keynotes = [sentences[i] for i in keynote_indices]

    return summary, keynotes


def summarize_youtube_video(
    url: str, num_summary_sentences: int = 5, num_keynotes: int = 5
) -> dict:
    """Fetch a YouTube video's metadata and transcript, then summarize it."""
    video_id = extract_video_id(url)
    metadata = get_video_metadata(url)
    transcript = get_transcript(video_id)
    summary, keynotes = summarize(transcript, num_summary_sentences, num_keynotes)
    return {
        "title": metadata["title"],
        "author": metadata["author"],
        "summary": summary,
        "keynotes": keynotes,
    }


def main() -> None:
    url = input("Enter a YouTube video URL: ").strip()
    if not url:
        print("No URL provided.")
        sys.exit(1)

    try:
        result = summarize_youtube_video(url)
    except Exception as exc:  # noqa: BLE001 - surface any failure to the user
        print(f"Error: {exc}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print(f"Title:  {result['title']}")
    print(f"Author: {result['author']}")
    print("=" * 60)

    print("\nKey Takeaways:")
    for i, point in enumerate(result["keynotes"], 1):
        print(f"  {i}. {point}")

    print("\nSummary:")
    print(f"  {result['summary']}")


if __name__ == "__main__":
    main()
