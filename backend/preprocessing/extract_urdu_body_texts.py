# extract_urdu_body_texts.py
# Extract <body> text from XML files in data/text/ and write plain text files to data/plain/.

import argparse
import pathlib
import re
import sys
import xml.etree.ElementTree as ET
from typing import Iterable

SRC_DIR = pathlib.Path("../../data/text")
DST_DIR = pathlib.Path("../../data/plain")
DST_DIR.mkdir(parents=True, exist_ok=True)

WHITESPACE_RE = re.compile(r"\s+")

def extract_body_text(xml_path: pathlib.Path) -> str | None:
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        body_elements = [elem for elem in root.iter() if elem.tag.endswith('body')]
        
        if not body_elements:
            return None
            
        body = body_elements[0]
        text_content = " ".join(body.itertext()).strip()
        
        if not text_content:
            return None
            
        text_content = WHITESPACE_RE.sub(" ", text_content)
        return text_content
        
    except (ET.ParseError, FileNotFoundError, PermissionError):
        return None

def check_urdu_only(xml_path: pathlib.Path) -> bool:
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        non_urdu_elements = [elem for elem in root.iter() 
                           if elem.tag.endswith('contains-non-urdu-languages')]
        
        if not non_urdu_elements:
            return True
            
        element = non_urdu_elements[0]
        return element.text and element.text.strip().lower() == 'no'
        
    except (ET.ParseError, FileNotFoundError, PermissionError):
        return True

def process_xml_files(xml_files: Iterable[pathlib.Path], urdu_only: bool = False) -> tuple[int, int]:
    extracted_count = 0
    skipped_count = 0
    
    for xml_file in xml_files:
        if urdu_only and not check_urdu_only(xml_file):
            skipped_count += 1
            continue
            
        body_text = extract_body_text(xml_file)
        
        if body_text is None:
            skipped_count += 1
            continue
            
        output_file = DST_DIR / f"{xml_file.stem}.txt"
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(body_text)
            extracted_count += 1
            
        except (OSError, IOError) as e:
            print(f"Error writing {output_file}: {e}", file=sys.stderr)
            skipped_count += 1
    
    return extracted_count, skipped_count

def main():
    parser = argparse.ArgumentParser(description="Extract body text from XML files")
    parser.add_argument("--urdu-only", action="store_true",
                        help="Only extract files where <contains-non-urdu-languages> is 'No'")
    args = parser.parse_args()
    
    if not SRC_DIR.exists():
        print(f"Source directory {SRC_DIR} does not exist", file=sys.stderr)
        sys.exit(1)
    
    xml_files = list(SRC_DIR.glob("*.xml"))
    
    if not xml_files:
        print(f"No XML files found in {SRC_DIR}", file=sys.stderr)
        sys.exit(1)
    
    print(f"Processing {len(xml_files)} XML files...")
    if args.urdu_only:
        print("Filtering for Urdu-only content...")
    
    extracted_count, skipped_count = process_xml_files(xml_files, args.urdu_only)
    
    print(f"\nExtraction complete!")
    print(f"Extracted: {extracted_count} files")
    print(f"Skipped: {skipped_count} files")
    print(f"Output directory: {DST_DIR}")

if __name__ == "__main__":
    main() 