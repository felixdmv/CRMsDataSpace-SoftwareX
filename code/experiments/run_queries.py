#!/usr/bin/env python3
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime

out_dir = Path(__file__).resolve().parent / "outputs"
out_dir.mkdir(parents=True, exist_ok=True)
out_file = out_dir / "answers.txt"
if out_file.exists():
    out_file.unlink()

questions = [
    "What materials are present in the waste facility?",
    "List all waste materials placed into the TSF and short descriptions.",
    "Describe how sludge from the water treatment plant is managed and its potential impacts.",
    "Which documents define reporting standards for mineral resources and reserves?",
    "According to 2023LUGTechnicalReport.pdf, what is the operating philosophy for the TSF?",
    "Summarize the monitoring instrumentation used for the TSF.",
]

env = os.environ.copy()
env["HF_MODEL"] = env.get("HF_MODEL", "google/flan-t5-base")

with out_file.open("a", encoding="utf-8") as f:
    f.write(f"=== RUN START {datetime.now().isoformat()} ===\n\n")
    for i, q in enumerate(questions, 1):
        f.write(f"--- QUESTION {i} ---\n{q}\n\n")
        print(f"Running question {i}/{len(questions)}...")
        proc = subprocess.run([
            sys.executable, "code/ask.py", q,
            "--k", "6",
            "--max-tokens", "512",
            "--detailed"
        ], capture_output=True, text=True, env=env)
        if proc.stdout:
            f.write(proc.stdout)
        if proc.stderr:
            f.write("\n[stderr]\n")
            f.write(proc.stderr)
        f.write("\n" + ("-"*60) + "\n")
    f.write(f"\n=== RUN END {datetime.now().isoformat()} ===\n")

print(f"Saved answers to {out_file}")
