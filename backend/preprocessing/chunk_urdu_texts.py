# chunk_urdu_texts.py
# Clean and chunk Urdu texts into sentence-based segments for Braille training.

import pathlib
import re
import unicodedata
from typing import List, Optional
from tqdm import tqdm

SRC_DIR = pathlib.Path("../data/plain")
DST_DIR = pathlib.Path("../data/chunks")
DST_DIR.mkdir(parents=True, exist_ok=True)

MIN_CHARS = 30
MAX_CHARS = 80
TARGET_CHUNKS = None  # No limit on chunks

def clean_urdu_text(text: str) -> Optional[str]:
    if not text or len(text.strip()) < 500:
        return None
    
    text = unicodedata.normalize('NFC', text)
    
    try:
        text = text.encode('utf-8', 'ignore').decode('utf-8')
    except UnicodeError:
        return None
    
    text = text.replace('.', '۔')
    text = text.replace(',', '،')
    text = text.replace(';', '؛')
    text = text.replace('?', '؟')
    
    text = re.sub(r'[\"\"\"''()[\\]{}]', '', text)
    text = re.sub(r'[\\.]{2,}', '', text)
    text = re.sub(r'[-—–]{2,}', ' ', text)
    text = re.sub(r'[#@%&*+=<>|\\\\\\/]', '', text)
    text = re.sub(r'\\s+', ' ', text).strip()
    
    return text

def sanitize_for_braille(text: str) -> str:
    text = re.sub(r'[\\u064B-\\u065F\\u0670\\u06D6-\\u06ED]', '', text)
    text = re.sub(r'[\\u200B\\u200C\\u200D\\u200E\\u200F\\u061C]', '', text)
    text = re.sub(r'[\\u00A0]', ' ', text)
    text = re.sub(r'ـ', '', text)
    text = re.sub(r'[a-zA-Z]', '', text)
    text = re.sub(r'[%٪]', 'فی صد', text)
    text = re.sub(r'\\r\\n|\\r|\\n', '\\n', text)
    text = re.sub(r'\\s+', ' ', text).strip()
    return text

def clean_sentence_punctuation(sentence: str) -> str:
    sentence = re.sub(r'[\"\"\"''()[\\]{}]', '', sentence)
    sentence = re.sub(r'[\\.]{2,}', '', sentence)
    sentence = re.sub(r'[-—–]{2,}', ' ', sentence)
    sentence = re.sub(r'[#@%&*+=<>|\\\\\\/]', '', sentence)
    sentence = re.sub(r'\\s+', ' ', sentence).strip()
    return sentence

def split_into_sentences(text: str) -> List[str]:
    sentences = re.split(r'[۔؟؍]', text)
    return [s.strip() for s in sentences if s.strip()]

def chunk_sentences(sentences: List[str]) -> List[str]:
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        if not sentence:
            continue
            
        sentence = clean_sentence_punctuation(sentence)
        sentence = sanitize_for_braille(sentence)
        
        if not sentence:
            continue
            
        if len(sentence) >= MIN_CHARS and len(sentence) <= MAX_CHARS:
            chunks.append(sentence)
        elif len(sentence) > MAX_CHARS:
            words = sentence.split()
            temp_chunk = ""
            for word in words:
                if len(temp_chunk + " " + word) <= MAX_CHARS:
                    temp_chunk = temp_chunk + " " + word if temp_chunk else word
                else:
                    if len(temp_chunk) >= MIN_CHARS:
                        chunks.append(temp_chunk)
                    temp_chunk = word
            if len(temp_chunk) >= MIN_CHARS:
                chunks.append(temp_chunk)
        else:
            if len(current_chunk + " " + sentence) <= MAX_CHARS:
                current_chunk = current_chunk + " " + sentence if current_chunk else sentence
            else:
                if len(current_chunk) >= MIN_CHARS:
                    chunks.append(current_chunk)
                current_chunk = sentence
    
    if len(current_chunk) >= MIN_CHARS:
        chunks.append(current_chunk)
    
    return chunks

def main():
    print(f"Processing Urdu text files from {SRC_DIR}...")
    
    text_files = list(SRC_DIR.glob("*.txt"))
    print(f"Found {len(text_files)} text files")
    
    all_chunks = []
    processed_files = 0
    
    for text_file in tqdm(text_files, desc="Processing files", unit="file"):
        try:
            with open(text_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            cleaned_text = clean_urdu_text(content)
            if not cleaned_text:
                continue
                
            sentences = split_into_sentences(cleaned_text)
            chunks = chunk_sentences(sentences)
            all_chunks.extend(chunks)
            processed_files += 1
            
        except Exception as e:
            print(f"Error processing {text_file}: {e}")
            continue
    
    if TARGET_CHUNKS and len(all_chunks) > TARGET_CHUNKS:
        import random
        all_chunks = random.sample(all_chunks, TARGET_CHUNKS)
    
    for i, chunk in enumerate(tqdm(all_chunks, desc="Saving chunks", unit="chunk")):
        chunk_file = DST_DIR / f"chunk_{i:05d}.txt"
        with open(chunk_file, 'w', encoding='utf-8') as f:
            f.write(chunk + "\\n")
    
    stats_content = f"""Urdu Text Chunking Statistics

Source files processed: {processed_files}
Total chunks generated: {len(all_chunks)}
Character range: {MIN_CHARS}-{MAX_CHARS}
Average length: {sum(len(c) for c in all_chunks) / len(all_chunks):.1f}

Sample chunks:
{chr(10).join(f'  {chunk[:100]}{"..." if len(chunk) > 100 else ""}' for chunk in all_chunks[:5])}
"""
    
    with open("../data/chunk_stats.txt", 'w', encoding='utf-8') as f:
        f.write(stats_content)
    
    print(f"\\n✅ Chunking complete!")
    print(f"Generated {len(all_chunks)} chunks from {processed_files} files")
    print(f"Saved to: {DST_DIR}")
    print(f"Statistics saved to: ../data/chunk_stats.txt")

if __name__ == "__main__":
    main() 