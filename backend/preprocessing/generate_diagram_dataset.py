import os
import json
import base64
import argparse
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel
from ollama import chat
from tqdm import tqdm

class KeyElement(BaseModel):
    name: str
    location: str
    description: str
    action: str

class DiagramAnalysis(BaseModel):
    diagram_title: str
    layout_description: str
    key_elements: List[KeyElement]
    main_process: str
    flow_details: str
    overall_summary: str

def encode_image_to_base64(image_path: str) -> str:
    """Encode image to base64 string for Ollama API."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def read_prompt_from_file(prompt_file: str) -> str:
    """Read the prompt from the diagram2json.txt file."""
    with open(prompt_file, 'r', encoding='utf-8') as f:
        return f.read().strip()

def process_image_with_ollama(image_path: str, prompt: str) -> Optional[DiagramAnalysis]:
    """Process a single image with Ollama and return structured analysis."""
    try:
        # Encode image to base64
        image_base64 = encode_image_to_base64(image_path)
        
        # Prepare the message with image and prompt
        messages = [
            {
                'role': 'user',
                'content': prompt,
                'images': [image_base64]
            }
        ]
        
        # Send request to Ollama with structured output format
        response = chat(
            messages=messages,
            model='gemma3:27b',
            format=DiagramAnalysis.model_json_schema(),
        )
        
        # Parse and validate the response
        analysis = DiagramAnalysis.model_validate_json(response.message.content)
        return analysis
        
    except Exception as e:
        print(f"Error processing {image_path}: {str(e)}")
        return None

def save_analysis(analysis: DiagramAnalysis, output_path: str, image_name: str, pbar=None):
    """Save the analysis to a JSON file."""
    output_file = os.path.join(output_path, f"{image_name}.json")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(analysis.model_dump(), f, indent=2, ensure_ascii=False)

def main():
    parser = argparse.ArgumentParser(description='Generate structured dataset from science diagrams')
    parser.add_argument('--count', type=int, default=None, 
                       help='Number of images to process (default: process all)')
    parser.add_argument('--images-dir', type=str, default='../data/ai2d/images',
                       help='Directory containing input images')
    parser.add_argument('--output-dir', type=str, default='../data/science-diagram-json',
                       help='Directory to save JSON analyses')
    parser.add_argument('--prompt-file', type=str, default='diagram2json.txt',
                       help='File containing the analysis prompt')
    
    args = parser.parse_args()
    
    # Setup paths
    images_dir = Path(args.images_dir)
    output_dir = Path(args.output_dir)
    prompt_file = Path(args.prompt_file)
    
    # Validate input directory
    if not images_dir.exists():
        print(f"Error: Images directory {images_dir} does not exist")
        return
    
    # Validate prompt file
    if not prompt_file.exists():
        print(f"Error: Prompt file {prompt_file} does not exist")
        return
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Read the prompt
    prompt = read_prompt_from_file(str(prompt_file))
    print(f"Loaded prompt from {prompt_file}")
    
    # Get list of image files
    image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff'}
    image_files = [f for f in images_dir.iterdir() 
                   if f.is_file() and f.suffix.lower() in image_extensions]
    
    # Limit number of images if specified
    if args.count is not None:
        image_files = image_files[:args.count]
        print(f"Processing {len(image_files)} images (limited by --count {args.count})")
    else:
        print(f"Processing all {len(image_files)} images")
    
    # Process each image
    processed_count = 0
    failed_count = 0
    
    # Create progress bar
    pbar = tqdm(image_files, desc="Processing images", unit="image")
    
    for image_file in pbar:
        pbar.set_postfix({"current": image_file.name})
        
        # Check if output already exists
        output_file = output_dir / f"{image_file.stem}.json"
        if output_file.exists():
            continue
        
        # Process the image
        analysis = process_image_with_ollama(str(image_file), prompt)
        
        if analysis:
            save_analysis(analysis, str(output_dir), image_file.stem, pbar)
            processed_count += 1
            pbar.set_postfix({"current": image_file.name, "processed": processed_count, "failed": failed_count})
        else:
            failed_count += 1
            pbar.write(f"Failed to process {image_file.name}")
            pbar.set_postfix({"current": image_file.name, "processed": processed_count, "failed": failed_count})
    
    print(f"\n=== Processing Complete ===")
    print(f"Successfully processed: {processed_count} images")
    print(f"Failed to process: {failed_count} images")
    print(f"Output directory: {output_dir}")

if __name__ == "__main__":
    main()
