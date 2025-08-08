# yolo_to_text.py
# Convert YOLO detection results to Urdu text using the braille decoder

from ultralytics import YOLO
from app.services.braille_decoder import BrailleDecoder
from typing import List, Tuple
import pathlib
from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt

class YOLOBrailleReader:
    def __init__(self, model_path: str, confidence_threshold: float = 0.5, imgsz: int = 1280):
        """
        Initialize YOLO Braille reader.
        
        Args:
            model_path: Path to trained YOLO model
            confidence_threshold: Minimum confidence for detections
            imgsz: Input image size (should match training configuration)
        """
        self.model = YOLO(model_path)
        self.confidence_threshold = confidence_threshold
        self.imgsz = imgsz
        self.decoder = BrailleDecoder()
        
    def preprocess_image(self, image_path: str) -> Image.Image:
        """
        Preprocess image to match training conditions.
        
        Args:
            image_path: Path to input image
            
        Returns:
            Preprocessed PIL Image
        """
        # Load image
        img = Image.open(image_path).convert('RGB')
        
        # Resize to match training size (1280x1280)
        # Use letterboxing to maintain aspect ratio
        img_ratio = img.width / img.height
        target_ratio = 1.0  # Square target
        
        if img_ratio > target_ratio:
            # Image is wider than target
            new_width = self.imgsz
            new_height = int(self.imgsz / img_ratio)
        else:
            # Image is taller than target
            new_height = self.imgsz
            new_width = int(self.imgsz * img_ratio)
        
        # Resize maintaining aspect ratio
        img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Create square canvas with padding
        canvas = Image.new('RGB', (self.imgsz, self.imgsz), (238, 238, 238))  # Same paper color as training
        
        # Center the resized image on the canvas
        x_offset = (self.imgsz - new_width) // 2
        y_offset = (self.imgsz - new_height) // 2
        canvas.paste(img_resized, (x_offset, y_offset))
        
        return canvas
    
    def draw_detections_on_image(self, img: Image.Image, detections: List[Tuple[int, float, float, float]]) -> Image.Image:
        """
        Draw bounding boxes on image based on YOLO detections.
        
        Args:
            img: PIL Image
            detections: List of (class_id, x_center_norm, y_center_norm, confidence)
            
        Returns:
            PIL Image with bounding boxes drawn
        """
        img_with_boxes = img.copy()
        draw = ImageDraw.Draw(img_with_boxes)
        
        # Colors for different classes
        colors = ['red', 'blue', 'green', 'orange', 'purple', 'yellow', 'cyan', 'magenta']
        
        try:
            font = ImageFont.truetype("Arial.ttf", 12)
        except (OSError, IOError):
            font = ImageFont.load_default()
        
        for class_id, x_center_norm, y_center_norm, confidence in detections:
            # Convert normalized coordinates to pixel coordinates
            x_center = x_center_norm * img.width
            y_center = y_center_norm * img.height
            
            # Estimate bounding box size (approximate character size)
            box_width = 30  # Approximate character width
            box_height = 40  # Approximate character height
            
            # Calculate box coordinates
            x1 = x_center - box_width // 2
            y1 = y_center - box_height // 2
            x2 = x_center + box_width // 2
            y2 = y_center + box_height // 2
            
            # Ensure box is within image bounds
            x1 = max(0, min(x1, img.width - box_width))
            y1 = max(0, min(y1, img.height - box_height))
            x2 = min(img.width, x1 + box_width)
            y2 = min(img.height, y1 + box_height)
            
            # Draw rectangle
            color = colors[class_id % len(colors)]
            draw.rectangle([x1, y1, x2, y2], outline=color, width=2)
            
            # Draw class label
            label = f"{class_id}"
            draw.text((x1, y1 - 15), label, fill=color, font=font)
        
        return img_with_boxes
        
    def extract_detections(self, results) -> List[Tuple[int, float, float, float]]:
        """
        Extract relevant detection data from YOLO results.
        
        Args:
            results: YOLO results object
            
        Returns:
            List of (class_id, x_center_norm, y_center_norm, confidence) tuples
        """
        detections = []
        
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for i in range(len(boxes)):
                    # Get normalized coordinates (already in 0-1 range)
                    x_center_norm = float(boxes.xywhn[i][0])
                    y_center_norm = float(boxes.xywhn[i][1])
                    confidence = float(boxes.conf[i])
                    class_id = int(boxes.cls[i])
                    
                    if confidence >= self.confidence_threshold:
                        detections.append((class_id, x_center_norm, y_center_norm, confidence))
        
        return detections
    
    def predict_and_decode(self, 
                          image_path: str,
                          line_height_threshold: float = 0.05,
                          show_intermediate: bool = False) -> Tuple[List[str], List[str]]:
        """
        Run YOLO prediction and decode to Urdu text.
        
        Args:
            image_path: Path to input image
            line_height_threshold: Threshold for separating text lines
            show_intermediate: Whether to print intermediate results
            
        Returns:
            Tuple of (braille_lines, urdu_lines)
        """
        # Preprocess image to match training conditions
        preprocessed_img = self.preprocess_image(image_path)
        
        if show_intermediate:
            print(f"Original image size: {Image.open(image_path).size}")
            print(f"Preprocessed image size: {preprocessed_img.size}")
        
        # Run YOLO inference on preprocessed image
        results = self.model(preprocessed_img)
        
        # Extract detections
        detections = self.extract_detections(results)
        
        if show_intermediate:
            print(f"Found {len(detections)} detections above confidence threshold")
            print("Sample detections (class_id, x, y, conf):")
            for det in detections[:5]:  # Show first 5
                print(f"  {det}")
            if len(detections) > 5:
                print(f"  ... and {len(detections) - 5} more")
            
            # Display image with bounding boxes
            if detections:
                img_with_boxes = self.draw_detections_on_image(preprocessed_img, detections)
                plt.figure(figsize=(12, 8))
                plt.imshow(img_with_boxes)
                plt.title(f"Detected {len(detections)} braille characters")
                plt.axis('off')
                plt.show()
        
        # Convert to format needed by decoder (remove confidence)
        detection_positions = [(class_id, x, y) for class_id, x, y, conf in detections]
        
        # Decode to text
        braille_lines, urdu_lines = self.decoder.decode_from_detections(
            detection_positions, 
            line_height_threshold
        )
        
        return braille_lines, urdu_lines
    
    def process_image(self, image_path: str, verbose: bool = False) -> str:
        """
        Process a single image and return the recognized Urdu text.
        
        Args:
            image_path: Path to input image
            verbose: Whether to print detailed output
            
        Returns:
            Recognized Urdu text (all lines joined)
        """
        if verbose:
            print(f"Processing: {image_path}")
        
        braille_lines, urdu_lines = self.predict_and_decode(
            image_path, 
            show_intermediate=verbose
        )
        
        if verbose:
            print("\nRecognition results:")
            for i, (braille, urdu) in enumerate(zip(braille_lines, urdu_lines)):
                print(f"Line {i+1}:")
                print(f"  Braille: {braille}")
                print(f"  Urdu: {urdu}")
        
        # Join all lines
        full_urdu_text = "\n".join(urdu_lines)
        
        return full_urdu_text
    
    def process_directory(self, input_dir: str, output_dir: str = None):
        """
        Process all images in a directory.
        
        Args:
            input_dir: Directory containing input images
            output_dir: Directory to save text files (optional)
        """
        input_path = pathlib.Path(input_dir)
        
        if output_dir:
            output_path = pathlib.Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
        
        # Find all image files
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
        image_files = [f for f in input_path.glob('*') 
                      if f.suffix.lower() in image_extensions]
        
        print(f"Found {len(image_files)} images in {input_dir}")
        
        for image_file in image_files:
            print(f"\n{'='*50}")
            
            try:
                urdu_text = self.process_image(str(image_file))
                
                if output_dir:
                    # Save text to file
                    text_file = output_path / f"{image_file.stem}.txt"
                    with open(text_file, 'w', encoding='utf-8') as f:
                        f.write(urdu_text)
                    print(f"Saved text to: {text_file}")
                else:
                    print(f"[{image_file.stem}] Urdu text: {urdu_text}")
                
            except Exception as e:
                print(f"Error processing {image_file}: {e}")


def main():
    """Example usage of YOLOBrailleReader."""
    
    # Model path - update this to your trained model
    model_path = "yolo11n.pt"  # or path to your trained .pt file
    
    if not pathlib.Path(model_path).exists():
        print(f"Model not found: {model_path}")
        print("Please provide the path to your trained YOLO model")
        return
    
    # Initialize reader with same image size as training (1280x1280)
    reader = YOLOBrailleReader(model_path, confidence_threshold=0.3, imgsz=1280)
    
    # Example 1: Process a single image
    print("=== Single Image Processing ===")
    # image_path = "/Users/qasim.khan/Documents/gemma3nImpactChallenge/data/braille_yolo_hd/images/train/chunk_00000.jpg"
    image_path = "/Users/qasim.khan/Documents/gemma3nImpactChallenge/braille-bridge/preprocessing/braille_aug.png"
    
    if pathlib.Path(image_path).exists():
        urdu = reader.process_image(image_path, verbose=True)
        print(urdu) 
    else:
        print(f"Example image not found: {image_path}")
        print("Update the image_path to point to a valid braille image")
    
    # Example 2: Process directory (uncomment to use)
    # print("\n=== Directory Processing ===")
    # reader.process_directory("../data/braille_yolo_hd/images/val", "output_texts")


if __name__ == "__main__":
    main()