# scratch/search_transcript.py
import os

root = r"C:\Users\Acer\.gemini\antigravity-ide\brain"
for r, d, files in os.walk(root):
    for f in files:
        if f == "transcript.jsonl":
            print(os.path.join(r, f))
