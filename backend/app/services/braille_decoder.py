# braille_decoder.py
# Convert class IDs back to original Braille and then to Urdu text.
# Reverses all transformations applied during dataset generation.

import louis
from typing import List, Tuple, Optional
import pathlib
import re

# Constants from dataset generation (must match generate_full_dataset.py)
UNICODE_BRAILLE_BASE = 0x2800  # Unicode offset for Braille patterns
NUM_CLASSES = 64               # 0-63 inclusive (original range)
MAX_BRAILLE_CHAR = 0x28FF      # Maximum possible braille character (U+28FF)
BLANK_CELL = "\u2800"          # Unicode blank Braille cell (represents space)

class BrailleDecoder:
    def __init__(self, louis_table: str = 'ur-pk-g1.utb'):
        """
        Initialize the Braille decoder.
        
        Args:
            louis_table: Louis table for Urdu Grade-1 Braille
        """
        self.louis_table = louis_table
        
        # Verify Louis table is available
        try:
            test_braille = "⠠⠁"  # Simple test character
            louis.backTranslateString([self.louis_table], test_braille)
        except Exception as e:
            print(f"Warning: Could not load Louis table '{louis_table}': {e}")
            print("Make sure liblouis is installed with Urdu table support")
    
    def class_ids_to_braille_chars(self, class_ids: List[int]) -> List[str]:
        """
        Convert class IDs to Braille Unicode characters.
        
        Args:
            class_ids: List of class IDs (0-63) from object detection model
            
        Returns:
            List of Braille Unicode characters
        """
        braille_chars = []
        for class_id in class_ids:
            if 0 <= class_id < NUM_CLASSES:
                # Convert class ID back to Unicode Braille character
                unicode_point = UNICODE_BRAILLE_BASE + class_id
                braille_char = chr(unicode_point)
                braille_chars.append(braille_char)
            else:
                print(f"Warning: Invalid class ID {class_id}, using blank cell")
                braille_chars.append(BLANK_CELL)
        
        return braille_chars
    
    def reconstruct_lines_from_positions(self, 
                                       detections: List[Tuple[int, float, float]], 
                                       line_height_threshold: float = 0.05) -> List[str]:
        """
        Reconstruct Braille text lines from detection positions.
        
        Args:
            detections: List of (class_id, x_center_norm, y_center_norm) tuples
            line_height_threshold: Normalized threshold for line separation
            
        Returns:
            List of Braille text lines
        """
        if not detections:
            return []
        
        # Sort by y-coordinate first (top to bottom), then x-coordinate (left to right)
        sorted_detections = sorted(detections, key=lambda d: (d[2], d[1]))
        
        # Group detections into lines based on y-coordinate proximity
        lines = []
        current_line = []
        current_y = sorted_detections[0][2]
        
        for class_id, x, y in sorted_detections:
            # If y-coordinate differs significantly, start a new line
            if abs(y - current_y) > line_height_threshold:
                if current_line:
                    # Sort current line by x-coordinate and convert to characters
                    current_line.sort(key=lambda d: d[1])  # Sort by x
                    line_chars = self.class_ids_to_braille_chars([d[0] for d in current_line])
                    lines.append("".join(line_chars))
                
                current_line = [(class_id, x, y)]
                current_y = y
            else:
                current_line.append((class_id, x, y))
        
        # Add the last line
        if current_line:
            current_line.sort(key=lambda d: d[1])  # Sort by x
            line_chars = self.class_ids_to_braille_chars([d[0] for d in current_line])
            lines.append("".join(line_chars))
        
        return lines
    
    def restore_spaces_from_blank_cells(self, braille_text: str) -> str:
        """
        Convert Unicode blank Braille cells back to ASCII spaces.
        This reverses the replace_spaces_with_blank_cells transformation.
        
        Args:
            braille_text: Braille text with blank cells
            
        Returns:
            Braille text with ASCII spaces
        """
        return braille_text.replace(BLANK_CELL, " ")
    
    def clean_braille_text(self, braille_text: str) -> str:
        """
        Clean braille text by removing non-standard braille characters.
        
        Args:
            braille_text: Raw braille text
            
        Returns:
            Cleaned braille text with only valid braille characters
        """
        cleaned = ""
        for char in braille_text:
            char_code = ord(char)
            # Keep valid Braille characters (U+2800 to U+283F) and spaces
            if (UNICODE_BRAILLE_BASE <= char_code < UNICODE_BRAILLE_BASE + NUM_CLASSES) or char == " ":
                cleaned += char
            elif char in ['\n', '\r']:  # Keep line breaks
                cleaned += char
            # Skip other characters (like the special sequences we see in the test)
        
        return cleaned

    def _normalise_aspirates(self, txt: str) -> str:
        """Normalize HEH variants that liblouis returns incorrectly."""
        # Handle specific patterns where liblouis returns « instead of proper characters
        
        # Pattern 1: Replace « that should be ھ (aspirated consonant marker)
        # Look for consonant + « patterns 
        aspirated_pattern = r'([بپتٹثجچحخددڈذرڑزژسشصضطظعغفقکگلمنوہء])«'
        txt = re.sub(aspirated_pattern, r'\1ھ', txt)
        
        # Pattern 2: Replace standalone « at word end that should be ؟
        txt = re.sub(r'«(?=\s|$)', '؟', txt)
        
        # Clean up any remaining « characters
        txt = txt.replace('«', '')
        
        return txt
    
    def braille_to_urdu(self, braille_text: str) -> Optional[str]:
        """
        Convert Braille text back to Urdu using liblouis.
        
        Args:
            braille_text: Braille Unicode text
            
        Returns:
            Urdu text or None if conversion fails
        """
        try:
            # First clean the braille text
            cleaned_braille = self.clean_braille_text(braille_text)
            
            # Then restore spaces from blank cells
            braille_with_spaces = self.restore_spaces_from_blank_cells(cleaned_braille)
            
            # Use liblouis to back-translate
            urdu_text = louis.backTranslateString([self.louis_table], braille_with_spaces)
            
            # Clean up the result
            if urdu_text:
                # Remove common encoding artifacts
                urdu_text = urdu_text.replace('\35', '').replace('/', '')
                # Collapse aspirated consonant sequences (ڈ ھ → ڈھ)
                urdu_text = self._normalise_aspirates(urdu_text)
                urdu_text = urdu_text.strip()
                
            return urdu_text if urdu_text else None
            
        except Exception as e:
            print(f"Error converting Braille to Urdu: {e}")
            print(f"Braille text was: {braille_text[:100]}...")
            return None
    
    def decode_from_class_ids(self, class_ids: List[int]) -> Tuple[str, Optional[str]]:
        """
        Full pipeline: Convert class IDs to Braille and then to Urdu.
        Assumes class IDs are already sorted by position (y then x).
        
        Args:
            class_ids: Sorted list of class IDs from detection model
            
        Returns:
            Tuple of (braille_text, urdu_text)
        """
        # Convert class IDs to Braille characters
        braille_chars = self.class_ids_to_braille_chars(class_ids)
        braille_text = "".join(braille_chars)
        
        # Convert Braille to Urdu
        urdu_text = self.braille_to_urdu(braille_text)
        
        return braille_text, urdu_text
    
    def decode_from_detections(self, 
                             detections: List[Tuple[int, float, float]], 
                             line_height_threshold: float = 0.05) -> Tuple[List[str], List[str]]:
        """
        Full pipeline: Convert detections with positions to multi-line Braille and Urdu.
        
        Args:
            detections: List of (class_id, x_center_norm, y_center_norm) tuples
            line_height_threshold: Normalized threshold for line separation
            
        Returns:
            Tuple of (braille_lines, urdu_lines)
        """
        # Reconstruct lines from positions
        braille_lines = self.reconstruct_lines_from_positions(detections, line_height_threshold)
        
        # Convert each line to Urdu
        urdu_lines = []
        for braille_line in braille_lines:
            urdu_line = self.braille_to_urdu(braille_line)
            urdu_lines.append(urdu_line if urdu_line is not None else "")
        
        return braille_lines, urdu_lines


def demo_usage():
    """Demonstrate usage of the BrailleDecoder."""
    decoder = BrailleDecoder()
    
    # Example 1: Simple class ID list (already sorted)
    print("=== Example 1: Simple sorted class IDs ===")
    class_ids = [32, 5, 45, 1, 37, 21, 5]  # Example class IDs
    braille_text, urdu_text = decoder.decode_from_class_ids(class_ids)
    print(f"Class IDs: {class_ids}")
    print(f"Braille: {braille_text}")
    print(f"Urdu: {urdu_text}")
    print()
    
    # Example 2: Detections with positions (needs sorting and line reconstruction)
    print("=== Example 2: Detections with positions ===")
    detections = [
        (32, 0.1, 0.2),   # class_id, x_center_norm, y_center_norm
        (5, 0.2, 0.2),    # Same line
        (45, 0.3, 0.2),   # Same line
        (1, 0.1, 0.6),    # Different line
        (37, 0.2, 0.6),   # Same as above
        (0, 0.15, 0.2),   # Back to first line (blank cell/space)
    ]
    
    braille_lines, urdu_lines = decoder.decode_from_detections(detections)
    print(f"Detections: {detections}")
    print("Reconstructed lines:")
    for i, (braille, urdu) in enumerate(zip(braille_lines, urdu_lines)):
        print(f"  Line {i+1}: '{braille}' → '{urdu}'")


if __name__ == "__main__":
    demo_usage()