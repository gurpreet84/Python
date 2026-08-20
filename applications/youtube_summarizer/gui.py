"""
YouTube Video Summarizer - GUI
===============================

A Tkinter desktop app: paste a YouTube URL, click "Generate", and it will
fetch the video's transcript, extract key takeaways, and save a standalone
HTML page (named after the video title) containing just those keynotes as
a bulleted list.

Run with:
    python gui.py
"""

import os
import threading
import tkinter as tk
import webbrowser
from tkinter import filedialog, messagebox, scrolledtext, ttk

from youtube_summarizer import (
    extract_video_id,
    get_transcript,
    get_video_metadata,
    save_keynotes_html,
    summarize,
)

DEFAULT_KEYNOTE_COUNT = 8


class YoutubeSummarizerApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("YouTube Video Summarizer")
        self.root.geometry("700x560")
        self.root.minsize(560, 420)

        self.output_dir = os.getcwd()
        self.last_filepath = None

        self._build_ui()

    def _build_ui(self) -> None:
        padding = {"padx": 12, "pady": 6}

        url_frame = ttk.Frame(self.root)
        url_frame.pack(fill="x", **padding)

        ttk.Label(url_frame, text="YouTube URL:").pack(side="left")
        self.url_var = tk.StringVar()
        self.url_entry = ttk.Entry(url_frame, textvariable=self.url_var)
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(8, 8))
        self.url_entry.bind("<Return>", lambda _event: self.on_generate())

        self.generate_button = ttk.Button(url_frame, text="Generate", command=self.on_generate)
        self.generate_button.pack(side="left")

        dir_frame = ttk.Frame(self.root)
        dir_frame.pack(fill="x", **padding)

        ttk.Label(dir_frame, text="Save to:").pack(side="left")
        self.output_dir_var = tk.StringVar(value=self.output_dir)
        ttk.Entry(dir_frame, textvariable=self.output_dir_var, state="readonly").pack(
            side="left", fill="x", expand=True, padx=(8, 8)
        )
        ttk.Button(dir_frame, text="Choose...", command=self.on_choose_dir).pack(side="left")

        info_frame = ttk.Frame(self.root)
        info_frame.pack(fill="x", **padding)

        self.title_var = tk.StringVar(value="Title: -")
        self.author_var = tk.StringVar(value="Author: -")
        ttk.Label(info_frame, textvariable=self.title_var, font=("TkDefaultFont", 10, "bold")).pack(
            anchor="w"
        )
        ttk.Label(info_frame, textvariable=self.author_var).pack(anchor="w")

        ttk.Label(self.root, text="Key Takeaways:").pack(anchor="w", padx=12)
        self.keynotes_box = scrolledtext.ScrolledText(self.root, wrap="word", height=18)
        self.keynotes_box.pack(fill="both", expand=True, padx=12, pady=(0, 6))
        self.keynotes_box.config(state="disabled")

        bottom_frame = ttk.Frame(self.root)
        bottom_frame.pack(fill="x", **padding)

        self.status_var = tk.StringVar(value="Enter a YouTube URL and click Generate.")
        ttk.Label(bottom_frame, textvariable=self.status_var, foreground="#555").pack(side="left")

        self.open_button = ttk.Button(
            bottom_frame, text="Open HTML", command=self.on_open, state="disabled"
        )
        self.open_button.pack(side="right")

    def on_choose_dir(self) -> None:
        chosen = filedialog.askdirectory(initialdir=self.output_dir)
        if chosen:
            self.output_dir = chosen
            self.output_dir_var.set(chosen)

    def on_generate(self) -> None:
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("Missing URL", "Please enter a YouTube video URL.")
            return

        self.generate_button.config(state="disabled")
        self.open_button.config(state="disabled")
        self.status_var.set("Fetching transcript... this may take a moment.")
        self._set_keynotes_text("")

        threading.Thread(target=self._process, args=(url,), daemon=True).start()

    def _process(self, url: str) -> None:
        try:
            video_id = extract_video_id(url)
            metadata = get_video_metadata(url)
            transcript = get_transcript(video_id)
            _, keynotes = summarize(transcript, num_keynotes=DEFAULT_KEYNOTE_COUNT)
            if not keynotes:
                raise RuntimeError("Could not extract any keynotes from this video's transcript.")
            filepath = save_keynotes_html(metadata["title"], keynotes, self.output_dir)
        except Exception as exc:  # noqa: BLE001 - surface any failure to the user
            self.root.after(0, self._on_error, str(exc))
            return
        self.root.after(0, self._on_success, metadata, keynotes, filepath)

    def _on_error(self, message: str) -> None:
        self.generate_button.config(state="normal")
        self.status_var.set("Error.")
        messagebox.showerror("Error", message)

    def _on_success(self, metadata: dict, keynotes: list, filepath: str) -> None:
        self.generate_button.config(state="normal")
        self.title_var.set(f"Title: {metadata['title']}")
        self.author_var.set(f"Author: {metadata['author']}")
        self._set_keynotes_text(
            "\n\n".join(f"{i}. {point}" for i, point in enumerate(keynotes, 1))
        )
        self.status_var.set(f"Saved: {filepath}")
        self.last_filepath = filepath
        self.open_button.config(state="normal")

    def _set_keynotes_text(self, text: str) -> None:
        self.keynotes_box.config(state="normal")
        self.keynotes_box.delete("1.0", tk.END)
        self.keynotes_box.insert(tk.END, text)
        self.keynotes_box.config(state="disabled")

    def on_open(self) -> None:
        if self.last_filepath:
            webbrowser.open(f"file://{os.path.abspath(self.last_filepath)}")


def main() -> None:
    root = tk.Tk()
    YoutubeSummarizerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
