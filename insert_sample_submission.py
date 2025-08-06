"""Seed the database with a sample student submission for the assignment
named "Default Science Lesson". Run with `python seed_sample_submission.py`.
"""
from __future__ import annotations

import shutil
from pathlib import Path
import random

from backend.db import (
    all_assignments,
    all_submissions,
    insert_submission,
)

UPLOADS_DIR = (Path(__file__).parent / "backend" / "uploads").resolve()
UPLOADS_DIR.mkdir(exist_ok=True)

ASSIGNMENT_TITLE = "A1"

# ---------------------------------------------------------------------------
# Locate assignment
# ---------------------------------------------------------------------------
assignments = all_assignments()

assignment = next((a for a in assignments if a.get("title") == ASSIGNMENT_TITLE), None)
if not assignment:
    raise SystemExit(f"Assignment titled '{ASSIGNMENT_TITLE}' not found. Create it first via the UI.")

assignment_id = assignment["id"]

diagram_idx = 0
# ---------------------------------------------------------------------------
# Copy a sample audio into uploads (use repository sample)
# ---------------------------------------------------------------------------
source_audio = Path("recordings/lesson_1_answer_1754513635783.m4a")
if not source_audio.exists():
    raise SystemExit("Sample audio preprocessing/cactus.m4a not found.")

dest_name_audio = f"sample_sub_{random.randint(1000,9999)}.m4a"
shutil.copy2(source_audio, UPLOADS_DIR / dest_name_audio)

# ---------------------------------------------------------------------------
# Copy a sample image into uploads (use repository sample)
# ---------------------------------------------------------------------------
source_image = Path("backend/preprocessing/braille_aug.png")
if not source_image.exists():
    raise SystemExit("Sample image preprocessing/braille_aug.png not found.")

dest_name_image = f"sample_sub_{random.randint(1000,9999)}.png"
shutil.copy2(source_image, UPLOADS_DIR / dest_name_image)

answers = [
    {
        "diagram_idx": 0,
        "answer_type": "audio",
        "file_path": f"backend/uploads/{dest_name_audio}",
    },
    {
        "diagram_idx": 1,
        "answer_type": "image",
        "file_path": f"backend/uploads/{dest_name_image}",
    }
]

student_name = "Qasim"

submission_id = insert_submission(assignment_id, student_name, answers)
print(f"Inserted sample submission #{submission_id} for assignment '{ASSIGNMENT_TITLE}'.")
print(all_submissions())