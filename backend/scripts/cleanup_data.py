"""Utility script to remove assignments and/or submissions from TinyDB.

Run examples:

    # delete a single assignment and its submissions
    python cleanup_data.py --assignment 3

    # delete all assignments and submissions
    python cleanup_data.py --all
"""
from __future__ import annotations
from pprint import pprint
import argparse
from app.db import assignments_table, submissions_table, students_table, db, all_assignments, all_submissions, get_all_students

parser = argparse.ArgumentParser(description="Clean TinyDB data")
parser.add_argument("--assignment", type=int, help="Assignment ID to delete (also deletes its submissions)")
parser.add_argument("--submission", type=int, help="Submission ID to delete")
parser.add_argument("--all", action="store_true", help="Delete ALL assignments, submissions, and students")

args = parser.parse_args()

pprint(all_assignments())
print()
pprint(all_submissions())
print()
pprint(get_all_students())
print()

if args.all:
    assignments_table.truncate()
    submissions_table.truncate()
    students_table.truncate()
    db.storage.flush()
    print("Deleted all assignments, submissions, and students.")
    raise SystemExit(0)

if args.assignment:
    # delete the assignment
    if not assignments_table.contains(doc_id=args.assignment):
        print(f"Assignment {args.assignment} not found.")
    else:
        assignments_table.remove(doc_ids=[args.assignment])
        # delete related submissions
        submissions_table.remove(lambda doc: doc.get("assignment_id") == args.assignment)
        db.storage.flush()
        print(f"Deleted assignment {args.assignment} and its submissions.")
    raise SystemExit(0)

if args.submission:
    if not submissions_table.contains(doc_id=args.submission):
        print(f"Submission {args.submission} not found.")
    else:
        submissions_table.remove(doc_ids=[args.submission])
        db.storage.flush()
        print(f"Deleted submission {args.submission}.")
    raise SystemExit(0)

parser.error("Specify --assignment ID, --submission ID, or --all")
