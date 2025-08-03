"""Simple TinyDB wrapper for storing assignments and submissions locally."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from tinydb import TinyDB, Query
from tinydb.storages import JSONStorage
from tinydb.middlewares import CachingMiddleware

DB_PATH = Path(__file__).with_name("db.json")

db = TinyDB(DB_PATH, storage=CachingMiddleware(JSONStorage))
assignments_table = db.table("assignments")
submissions_table = db.table("submissions")

# ---------------------------------------------------------------------------
# Assignment helpers
# ---------------------------------------------------------------------------

def insert_assignment(title: str, diagrams: List[Dict[str, Any]]) -> int:
    doc = {"title": title, "diagrams": diagrams}
    assignment_id = assignments_table.insert(doc)
    db.storage.flush()
    return assignment_id

def get_assignment(assignment_id: int) -> Dict[str, Any] | None:
    return assignments_table.get(doc_id=assignment_id)

def all_assignments() -> List[Dict[str, Any]]:
    return [dict(a, id=a.doc_id) for a in assignments_table]

def set_diagram_context(assignment_id: int, diagram_idx: int, context_json: str):
    assignment = assignments_table.get(doc_id=assignment_id)
    if not assignment:
        return
    diagrams: list = assignment.get("diagrams", [])
    if diagram_idx < 0 or diagram_idx >= len(diagrams):
        return
    diagrams[diagram_idx]["context"] = context_json
    assignments_table.update({"diagrams": diagrams}, doc_ids=[assignment_id])
    db.storage.flush()

# ---------------------------------------------------------------------------
# Submission helpers
# ---------------------------------------------------------------------------

def insert_submission(assignment_id: int, student: str, answers: List[Dict[str, Any]]) -> int:
    doc = {"assignment_id": assignment_id, "student": student, "answers": answers}
    sub_id = submissions_table.insert(doc)
    db.storage.flush()
    return sub_id

def get_submission(sub_id: int) -> Dict[str, Any] | None:
    return submissions_table.get(doc_id=sub_id)

def all_submissions() -> List[Dict[str, Any]]:
    return [dict(s, id=s.doc_id) for s in submissions_table]

# ---------------------------------------------------------------------------
# Student profile helpers
# ---------------------------------------------------------------------------
students_table = db.table("students")

def get_or_create_student(name: str) -> Dict[str, Any]:
    """Get existing student or create new one with default profile"""
    existing = students_table.search(Query().name == name)
    if existing:
        return existing[0]
    
    # Create new student
    student_doc = {
        "name": name,
        "strengths": [],
        "challenges": []
    }
    student_id = students_table.insert(student_doc)
    db.storage.flush()
    return dict(student_doc, id=student_id)

def add_student_feedback(name: str, feedback_type: str, feedback_text: str):
    """Add strength or challenge to student profile"""
    student = get_or_create_student(name)
    
    if feedback_type == "strength":
        if feedback_text not in student.get("strengths", []):
            students_table.update(
                {"strengths": student.get("strengths", []) + [feedback_text]},
                Query().name == name
            )
    elif feedback_type == "challenge":
        if feedback_text not in student.get("challenges", []):
            students_table.update(
                {"challenges": student.get("challenges", []) + [feedback_text]},
                Query().name == name
            )
    
    db.storage.flush()

def get_all_students() -> List[Dict[str, Any]]:
    return [dict(s, id=s.doc_id) for s in students_table]
