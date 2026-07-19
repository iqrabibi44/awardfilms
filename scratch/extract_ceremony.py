# scratch/extract_ceremony.py
import json

path = r"C:\Users\Acer\.gemini\antigravity-ide\brain\163284df-fa5c-462b-b7a3-77b1d39855b7\.system_generated\logs\transcript.jsonl"
with open(path, "r", encoding="utf-8") as f:
    for i, line in enumerate(f):
        if "ceremony.php" in line and "view_file" in line:
            print(f"Line {i} matches!")
            obj = json.loads(line)
            print(obj.keys())
            if "tool_calls" in obj:
                print(obj["tool_calls"])
            if "output" in obj:
                print(obj["output"][:500])

