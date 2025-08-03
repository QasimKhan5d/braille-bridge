# convert_to_braille.py
# Convert cleaned Urdu text chunks to Grade-1 Braille using liblouis.

import pathlib
from typing import Optional
from tqdm import tqdm

import louis
from utils.text_clean import clean_source

SRC_DIR = pathlib.Path("../../data/chunks")
DST_DIR = pathlib.Path("../../data/braille")
DST_DIR.mkdir(parents=True, exist_ok=True)

def to_braille(text):
    return louis.translateString(['ur-pk-g1.utb'] , text)

def to_text(braille):
    return louis.backTranslateString(['ur-pk-g1.utb'] , braille)

def convert_text_to_braille(text: str) -> Optional[str]:
    """Clean *text*, convert to Grade-1 Braille, ensure only 6-dot cells.

    Returns None if the text is empty after cleaning or if liblouis
    outputs any 8-dot patterns (which would break the 64-class mapping).
    """
    try:
        # 1️⃣  pre-clean: remove ASCII / punctuation we don't model
        text = clean_source(text.strip())
        if not text:
            return None

        # 2️⃣  Urdu → Braille
        braille = to_braille(text)
        if not braille or len(braille.strip()) == 0:
            return None

        # 3️⃣  Validation: keep only 6-dot patterns (0–63) + spaces
        for ch in braille:
            if ch == ' ':
                continue  # ASCII spaces are fine
            val = ord(ch) - 0x2800
            if val < 0 or val >= 64:
                # Skip this piece of text; caller treats None as conversion failure
                return None

        return braille.strip()

    except Exception as e:
        print(f"Error converting text to Braille: {e}")
        print(f"Text was: {text[:100]}…")
        return None


            



def main():
    chunk_files = sorted(SRC_DIR.glob("chunk_*.txt"))
    
    if not chunk_files:
        print(f"No chunk files found in {SRC_DIR}")
        return
        
    print(f"Converting {len(chunk_files)} text chunks to Grade-1 Braille...")
    
    converted_count = 0
    failed_count = 0
    
    for chunk_file in tqdm(chunk_files, desc="Converting to Braille", unit="file"):
        try:
            with open(chunk_file, 'r', encoding='utf-8') as f:
                urdu_text = f.read().strip()
                
            if not urdu_text:
                print(f"Skipping empty file: {chunk_file.name}")
                failed_count += 1
                continue
                
            braille_text = convert_text_to_braille(urdu_text)
            
            if braille_text is None:
                failed_count += 1
                continue
                
            braille_file = DST_DIR / chunk_file.name
            with open(braille_file, 'w', encoding='utf-8') as f:
                f.write(braille_text + '\n')
                
            converted_count += 1
                
        except Exception as e:
            print(f"Error processing {chunk_file.name}: {e}")
            failed_count += 1
            continue
    
    print(f"\nConversion complete!")
    print(f"Successfully converted: {converted_count} files")
    print(f"Failed conversions: {failed_count} files")
    print(f"Output directory: {DST_DIR}")
    
    if converted_count > 0:
        print(f"\nSample conversions:")
        sample_files = sorted(DST_DIR.glob("chunk_*.txt"))[:3]
        
        for sample_file in sample_files:
            orig_file = SRC_DIR / sample_file.name
            with open(orig_file, 'r', encoding='utf-8') as f:
                orig_text = f.read().strip()
                
            with open(sample_file, 'r', encoding='utf-8') as f:
                braille_text = f.read().strip()
                
            print(f"\n{sample_file.name}:")
            print(f"Original: {orig_text}")
            print(f"Braille:  {braille_text}")

if __name__ == "__main__":
    main() 