import pathlib
import os
import random
import yaml
from typing import List

from tqdm import tqdm

from preprocessing.braille_synthetic_photo import BraillePage, PhotoAug, _sanitize_text_lines

# ---------------------------------------------------------------------------
# Paths & constants
# ---------------------------------------------------------------------------

# Source data (unchanged)
CHUNKS_DIR = pathlib.Path("../data/chunks")
BRAILLE_DIR = pathlib.Path("../data/braille")

# Output dataset root following Ultralytics YOLO layout
DATASET_ROOT = pathlib.Path("../data/braille_yolo_hd")
TRAIN_IMAGES_DIR = DATASET_ROOT / "images" / "train"
VAL_IMAGES_DIR = DATASET_ROOT / "images" / "val"
TRAIN_LABELS_DIR = DATASET_ROOT / "labels" / "train"
VAL_LABELS_DIR = DATASET_ROOT / "labels" / "val"

# Create all directories
for dir_path in [TRAIN_IMAGES_DIR, VAL_IMAGES_DIR, TRAIN_LABELS_DIR, VAL_LABELS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# Whether to optionally apply photo augmentations (env-toggle)
AUGMENT_IMAGES = os.getenv("AUGMENT_IMAGES", "0") == "1"

# Test mode settings
TEST_SAMPLES = os.getenv("TEST_SAMPLES", None) 
DRAW_BBOXES = os.getenv("DRAW_BBOXES", None)

# Dataset split ratio (train/val)
VAL_SPLIT = 0.2

# Braille font & spacing
BRAILLE_FONT_SIZE = int(os.getenv("BRAILLE_FONT_SIZE", "48"))  # default font size
CHAR_SPACING = int(BRAILLE_FONT_SIZE * 0.4)                    # spacing between chars

# Braille properties
UNICODE_BRAILLE_BASE = 0x2800  # Unicode offset for Braille patterns
NUM_CLASSES = 64               # 0-63 inclusive (Braille has 6 cells, so we can have 2^6 = 64 patterns)
MAX_BOXES_PER_IMAGE = float('inf')       # discard pages with more than this many boxes

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def load_braille_files() -> List[pathlib.Path]:
    """Return all braille *.txt files sorted by name."""
    return sorted(BRAILLE_DIR.glob("chunk_*.txt"))


def read_text(path: pathlib.Path) -> str:
    """Return file contents stripped; empty string on error."""
    try:
        return path.read_text(encoding="utf-8").strip()
    except Exception as exc:
        print(f"[WARN] Could not read {path}: {exc}")
        return ""


def replace_spaces_with_blank_cells(s: str) -> str:
    """Replace ASCII spaces with Unicode blank Braille cell (U+2800)."""
    return s.replace(" ", "\u2800")


def wrap_lines(lines: List[str], max_cols: int) -> List[str]:
    """Wrap each line at *max_cols* to ensure fixed column width."""
    wrapped: List[str] = []
    for ln in lines:
        while len(ln) > max_cols:
            wrapped.append(ln[:max_cols])
            ln = ln[max_cols:]
        wrapped.append(ln)
    return wrapped


def draw_image_and_boxes(page: BraillePage, braille_text: str, *, max_cols: int = 24):
    """Render braille_text and return (PIL image, list[bbox], list[category_id]).

    bbox: [x, y, w, h] in absolute pixel coords.
    category_id is 0-based to follow YOLO convention.
    """
    # 1. Prepare text — use the shared sanitisation logic for consistency
    lines = _sanitize_text_lines(braille_text.split("\n"), max_cols=max_cols)

    # 2. Use the new draw_with_positions method for accurate positioning
    char_spacing = CHAR_SPACING  # pixels between characters (scaled with font size)
    img, character_positions = page.draw_with_positions(lines, max_cols=max_cols, char_spacing=char_spacing)

    # 3. Create bounding boxes from actual character positions
    boxes: List[List[int]] = []
    categories: List[int] = []
    
    padding = 3  # padding around each character for better coverage
    
    for char, x, y, char_width, char_height in character_positions:
        cat_id_0_based = ord(char) - UNICODE_BRAILLE_BASE
        
        # Only process valid Braille characters
        if 0 <= cat_id_0_based < NUM_CLASSES:
            # Create bounding box with padding
            bbox_x = x - padding
            bbox_y = y - padding
            bbox_w = char_width + padding * 2
            bbox_h = char_height + padding * 2
            
            boxes.append([bbox_x, bbox_y, bbox_w, bbox_h])
            categories.append(cat_id_0_based)  # 0-based for YOLO

    return img, boxes, categories


def convert_to_yolo_format(bbox: List[int], img_width: int, img_height: int) -> List[float]:
    """Convert absolute bbox [x, y, w, h] to normalized YOLO format [x_center, y_center, width, height]."""
    x, y, w, h = bbox
    
    # Validate bounds (should never trigger with correct logic, but safety check)
    if x < 0 or y < 0 or x + w > img_width or y + h > img_height:
        print(f"WARNING: bbox [{x}, {y}, {w}, {h}] out of bounds for image {img_width}×{img_height}")
        # Clamp to valid bounds
        x = max(0, min(x, img_width - w))
        y = max(0, min(y, img_height - h))
        w = min(w, img_width - x)
        h = min(h, img_height - y)
    
    # Convert to center coordinates
    x_center = x + w / 2
    y_center = y + h / 2
    
    # Normalize by image dimensions
    x_center_norm = x_center / img_width
    y_center_norm = y_center / img_height
    w_norm = w / img_width
    h_norm = h / img_height
    
    # Final validation - all values should be 0-1
    if not (0 <= x_center_norm <= 1 and 0 <= y_center_norm <= 1 and 0 <= w_norm <= 1 and 0 <= h_norm <= 1):
        print(f"WARNING: normalized coords out of range: [{x_center_norm:.3f}, {y_center_norm:.3f}, {w_norm:.3f}, {h_norm:.3f}]")
    
    return [x_center_norm, y_center_norm, w_norm, h_norm]


def draw_bboxes_on_image(img, bboxes: List[List[int]], categories: List[int]):
    """Draw bounding boxes on image for visual verification. Returns modified image."""
    from PIL import ImageDraw, ImageFont
    
    # Create a copy to avoid modifying original
    img_with_boxes = img.copy()
    draw = ImageDraw.Draw(img_with_boxes)
    
    # Use different colors for different classes (cycle through a few colors)
    colors = ['red', 'blue', 'green', 'orange', 'purple', 'yellow', 'cyan', 'magenta']
    
    try:
        # Try to use a small font for labels
        font = ImageFont.truetype("Arial.ttf", 12)
    except (OSError, IOError):
        # Fall back to default font
        font = ImageFont.load_default()
    
    for i, (bbox, cat) in enumerate(zip(bboxes, categories)):
        x, y, w, h = bbox
        color = colors[cat % len(colors)]
        
        # Draw rectangle
        draw.rectangle([x, y, x + w, y + h], outline=color, width=1)
        
        # Draw class label
        label = f"{cat}"
        draw.text((x, y - 12), label, fill=color, font=font)
    
    return img_with_boxes


def save_yolo_labels(labels_file: pathlib.Path, categories: List[int], bboxes: List[List[int]], 
                    img_width: int, img_height: int):
    """Save labels in YOLO format: class x_center y_center width height (normalized)."""
    with open(labels_file, 'w') as f:
        for cat, bbox in zip(categories, bboxes):
            norm_bbox = convert_to_yolo_format(bbox, img_width, img_height)
            # Format: class x_center y_center width height
            f.write(f"{cat} {norm_bbox[0]:.6f} {norm_bbox[1]:.6f} {norm_bbox[2]:.6f} {norm_bbox[3]:.6f}\n")


def create_yaml_configs():
    """Create the dataset YAML config file for Ultralytics."""
    
    # Generate class names dictionary (0-based)
    class_names = {i: f"braille_{i:02d}" for i in range(NUM_CLASSES)}
    data_yaml = {
        'path': ".",
        'train': 'images/train',
        'val': 'images/val',
        'names': [class_names[i] for i in range(NUM_CLASSES)]
    }
    data_path = DATASET_ROOT / "data.yaml"
    with open(data_path, 'w') as f:
        yaml.dump(data_yaml, f, default_flow_style=False, sort_keys=False)
    
    config = {
        'mode': 'train',
        'model': 'yolo11n.pt',
        'data': 'data.yaml',
        'imgsz': 1280,
        'format': 'tflite',
        'hsv_h': 0.03,
        'hsv_s': 0.6,
        'hsv_v': 0.4,
        'degrees': 2.0,
        'translate': 0.02,
        'scale': 0.3,
        'perspective': 0.001,
        'fliplr': 0.0,
        'flipud': 0.0,
    }
    
    cfg_path = DATASET_ROOT / "cfg.yaml"
    with open(cfg_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    return cfg_path, data_path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    print("Generating Braille YOLO-style detection dataset…")
    
    braille_files = load_braille_files()
    print(f"Found {len(braille_files):,} braille files to process.")
    
    if not braille_files:
        print("No braille files detected. Did you run convert_to_braille.py?")
        return

    # Shuffle first for random sampling
    random.shuffle(braille_files)

    # Test mode with limited samples
    if TEST_SAMPLES:
        try:
            max_samples = int(TEST_SAMPLES)
            braille_files = braille_files[:max_samples]
            print(f"🧪 TEST MODE: Limited to {len(braille_files)} samples (randomly selected)")
            if DRAW_BBOXES:
                print(f"📦 Bounding boxes will be drawn on images for verification")
        except ValueError:
            print(f"❌ Invalid TEST_SAMPLES value: {TEST_SAMPLES}. Using all files.")

    # Split into train/val sets (already shuffled)
    val_count = int(len(braille_files) * VAL_SPLIT)
    train_files = braille_files[val_count:]
    val_files = braille_files[:val_count]
    
    print(f"Train set: {len(train_files):,} files")
    print(f"Val set:   {len(val_files):,} files")

    page_maker = BraillePage(font_size=BRAILLE_FONT_SIZE, margin=30)
    photo_aug = PhotoAug()
    
    total_images = 0
    total_annotations = 0

    # Process training set
    for braille_file in tqdm(train_files, desc="Processing train set", unit="img"):
        chunk_id = braille_file.stem  # e.g. chunk_00123
        braille_text = read_text(braille_file)
        if not braille_text:
            continue

        # Generate clean image (+ optional augmentation)
        img, bboxes, cats = draw_image_and_boxes(page_maker, braille_text)
        
        # Skip samples with too many bounding boxes (exceeds model limits)
        if len(bboxes) > MAX_BOXES_PER_IMAGE:
            continue

        if AUGMENT_IMAGES:
            img = photo_aug(img)

        # Draw bounding boxes for visual verification in test mode
        if DRAW_BBOXES:
            img = draw_bboxes_on_image(img, bboxes, cats)

        # Save image
        file_name = f"{chunk_id}.jpg"
        img_path = TRAIN_IMAGES_DIR / file_name
        img.save(img_path)

        # Save corresponding label file
        label_name = f"{chunk_id}.txt"
        label_path = TRAIN_LABELS_DIR / label_name
        save_yolo_labels(label_path, cats, bboxes, img.width, img.height)

        total_images += 1
        total_annotations += len(bboxes)

    # Process validation set
    for braille_file in tqdm(val_files, desc="Processing val set", unit="img"):
        chunk_id = braille_file.stem  # e.g. chunk_00123
        braille_text = read_text(braille_file)
        if not braille_text:
            continue
        
        # Generate clean image (+ optional augmentation)
        img, bboxes, cats = draw_image_and_boxes(page_maker, braille_text)
       
        # Skip samples with too many bounding boxes (exceeds model limits)
        if len(bboxes) > MAX_BOXES_PER_IMAGE:
            if not TEST_SAMPLES:
                print(f"[SKIP] {chunk_id}: {len(bboxes)} boxes > {MAX_BOXES_PER_IMAGE}")
            continue

        if AUGMENT_IMAGES:
            img = photo_aug(img)

        # Draw bounding boxes for visual verification in test mode
        if DRAW_BBOXES:
            img = draw_bboxes_on_image(img, bboxes, cats)

        # Save image
        file_name = f"{chunk_id}.jpg"
        img_path = VAL_IMAGES_DIR / file_name
        img.save(img_path)

        # Save corresponding label file
        label_name = f"{chunk_id}.txt"
        label_path = VAL_LABELS_DIR / label_name
        save_yolo_labels(label_path, cats, bboxes, img.width, img.height)

        total_images += 1
        total_annotations += len(bboxes)

    # Create YAML config file
    cfg_path, data_path = create_yaml_configs()

    print("\n✅ Dataset generation complete! 🦉")
    print(f"Dataset root:     {DATASET_ROOT}")
    print(f"Train images:     {len(train_files):,}")
    print(f"Val images:       {len(val_files):,}")
    print(f"Total images:     {total_images:,}")
    print(f"Total annotations: {total_annotations:,}")
    print(f"Classes:          {NUM_CLASSES} (braille_00 to braille_{NUM_CLASSES-1:02d})")
    print(f"Config file:      {cfg_path}")
    
    if DRAW_BBOXES:
        print(f"\n🧪 TEST MODE NOTES:")
        print(f"  📦 Bounding boxes drawn on images for visual verification")
        print(f"  🔍 Check {TRAIN_IMAGES_DIR} and {VAL_IMAGES_DIR} to verify coordinates")
        print(f"  ⚠️  For production, remove TEST_SAMPLES to generate full dataset without boxes")
    
    print(f"\nTo train with Ultralytics:")
    print(f"  from ultralytics import YOLO")
    print(f"  model = YOLO('yolo11n.pt')")
    print(f"  model.train(data='{data_path}', epochs=100, imgsz=640)")


if __name__ == "__main__":
    random.seed(42)  # reproducibility for any future randomness
    main() 