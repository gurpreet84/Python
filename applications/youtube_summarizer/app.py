"""
YouTube Video Summarizer - Web App
===================================

A local Flask web app: paste a YouTube URL in your browser, and it generates
a page of the video's key takeaways as bullets, along with a standalone HTML
file (named after the video title) saved to the `output/` folder.

Run with:
    python app.py
Then open http://127.0.0.1:5000 in your browser.
"""

import os

from flask import Flask, render_template, request, send_from_directory, url_for

from youtube_summarizer import (
    extract_video_id,
    get_transcript,
    get_video_metadata,
    save_keynotes_html,
    summarize,
)

DEFAULT_KEYNOTE_COUNT = 8
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    url = request.form.get("url", "").strip()
    if not url:
        return render_template("index.html", error="Please enter a YouTube URL.")

    try:
        video_id = extract_video_id(url)
        metadata = get_video_metadata(url)
        transcript = get_transcript(video_id)
        _, keynotes = summarize(transcript, num_keynotes=DEFAULT_KEYNOTE_COUNT)
        if not keynotes:
            raise RuntimeError("Could not extract any keynotes from this video's transcript.")
        filepath = save_keynotes_html(metadata["title"], keynotes, OUTPUT_DIR)
    except Exception as exc:  # noqa: BLE001 - surface any failure to the user
        return render_template("index.html", error=str(exc), url=url)

    return render_template(
        "result.html",
        title=metadata["title"],
        author=metadata["author"],
        keynotes=keynotes,
        filename=os.path.basename(filepath),
    )


@app.route("/output/<path:filename>")
def output_file(filename):
    return send_from_directory(OUTPUT_DIR, filename)


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    app.run(debug=False)
