# braille_synthetic_photo.py
# Render Unicode-Braille to clean pages using TTF font and apply
# photo-realistic augmentations for training data generation.

from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageOps, ImageEnhance, ImageFont
import random, numpy as np
from io import BytesIO

UNICODE_BRAILLE_BASE = 0x2800
NUM_CLASSES = 64  # Braille 0–63 (6-dot)


def _sanitize_text_lines(lines, max_cols=24):
    """Apply the same normalization used during dataset generation.

    1. Replace ASCII spaces with the blank Braille cell (U+2800).
    2. Wrap each line at *max_cols* characters.
    3. Replace any non-Braille character with blank Braille cell
       to avoid missing categories.
    """
    blank_cell = "\u2800"

    def _norm_line(line):
        # 1) spaces → blank cell
        line = line.replace(" ", blank_cell)
        # 2) ensure only Braille chars
        line = "".join(
            ch if UNICODE_BRAILLE_BASE <= ord(ch) < UNICODE_BRAILLE_BASE + NUM_CLASSES else blank_cell
            for ch in line
        )
        return line

    # Wrap and normalise
    wrapped = []
    for ln in lines:
        ln = _norm_line(ln)
        while len(ln) > max_cols:
            wrapped.append(ln[:max_cols])
            ln = ln[max_cols:]
        wrapped.append(ln)
    return wrapped


class BraillePage:
    def __init__(self, font_size=48, line_spacing=1.5, margin=30, paper=(238,238,238)):
        self.font_size = font_size
        self.line_spacing = line_spacing
        self.margin = margin
        self.paper = paper
        
        font_path = "SimBraille.ttf"
        try:
            self.font = ImageFont.truetype(str(font_path), size=font_size)
        except (OSError, IOError) as e:
            print(f"Warning: Could not load SimBraille.ttf: {e}")
            print("Falling back to default font")
            self.font = ImageFont.load_default()

    def draw(self, lines, max_cols=None):
        if max_cols is not None:
            wrapped = []
            for ln in lines:
                while len(ln) > max_cols:
                    wrapped.append(ln[:max_cols])
                    ln = ln[max_cols:]
                wrapped.append(ln)
            lines = wrapped

        if not lines or all(len(line.strip()) == 0 for line in lines):
            return Image.new("RGB", (self.margin*2 + 200, self.margin*2 + 100), self.paper)
            
        temp_img = Image.new("RGB", (1, 1))
        temp_draw = ImageDraw.Draw(temp_img)
        
        max_width = 0
        line_height = temp_draw.textbbox((0, 0), "⠿", font=self.font)[3]
        
        for line in lines:
            if line.strip():
                bbox = temp_draw.textbbox((0, 0), line, font=self.font)
                line_width = bbox[2] - bbox[0]
                max_width = max(max_width, line_width)
        
        total_height = len(lines) * line_height * self.line_spacing
        W = self.margin * 2 + max_width
        H = self.margin * 2 + int(total_height)
        
        img = Image.new("RGB", (W, H), self.paper)
        draw = ImageDraw.Draw(img)
        
        y_offset = self.margin
        for line in lines:
            if line.strip():
                draw.text((self.margin, y_offset), line, font=self.font, fill=(80, 80, 80))
            y_offset += int(line_height * self.line_spacing)
        
        return img

    def draw_with_positions(self, lines, max_cols=None, char_spacing=20):
        """Draw braille text and return (image, character_positions).
        
        Args:
            lines: List of braille text lines
            max_cols: Maximum columns before wrapping
            char_spacing: Extra spacing between characters in pixels
            
        Returns:
            tuple: (PIL Image, list of (char, x, y, width, height))
        """
        if max_cols is not None:
            wrapped = []
            for ln in lines:
                while len(ln) > max_cols:
                    wrapped.append(ln[:max_cols])
                    ln = ln[max_cols:]
                wrapped.append(ln)
            lines = wrapped

        if not lines or all(len(line.strip()) == 0 for line in lines):
            empty_img = Image.new("RGB", (self.margin*2 + 200, self.margin*2 + 100), self.paper)
            return empty_img, []
            
        temp_img = Image.new("RGB", (1, 1))
        temp_draw = ImageDraw.Draw(temp_img)
        
        # Get character dimensions
        char_bbox = temp_draw.textbbox((0, 0), "⠿", font=self.font)
        char_width = char_bbox[2] - char_bbox[0]
        line_height = char_bbox[3] - char_bbox[1]
        
        # Calculate total width with spacing
        max_chars = max(len(line) for line in lines) if lines else 0
        total_width = max_chars * (char_width + char_spacing) - char_spacing if max_chars > 0 else 0
        
        # Increase line spacing for better vertical separation
        increased_line_spacing = self.line_spacing * 1.8  # 80% more vertical spacing
        total_height = len(lines) * line_height * increased_line_spacing
        
        W = self.margin * 2 + int(total_width)
        H = self.margin * 2 + int(total_height)
        
        img = Image.new("RGB", (W, H), self.paper)
        draw = ImageDraw.Draw(img)
        
        character_positions = []
        
        y_offset = self.margin
        for line in lines:
            x_offset = self.margin
            for char in line:
                # Get actual character dimensions for this specific character
                actual_bbox = temp_draw.textbbox((0, 0), char, font=self.font)
                actual_width = actual_bbox[2] - actual_bbox[0]
                actual_height = actual_bbox[3] - actual_bbox[1]
                
                # Draw the character
                draw.text((x_offset, y_offset), char, font=self.font, fill=(80, 80, 80))
                
                # Record position including top offset for accurate bbox
                char_top_offset = char_bbox[1]  # may be negative if glyph rises above baseline
                character_positions.append((char, x_offset, y_offset + char_top_offset, char_width, line_height))
                
                # Move to next character position
                x_offset += char_width + char_spacing
            
            y_offset += int(line_height * increased_line_spacing)
        
        return img, character_positions

class PhotoAug:
    # Increased probabilities for stronger photo-realistic effects.  Dirt disabled to avoid occlusion.
    cfg = dict(
        gradient     = 0.9,
        perspective  = 0.8,
        blur         = 0.5,
        noise        = 0.3,
        white_balance= 0.3,
        vignette     = 0.3,
        shadow       = 0.35,
        chrome_aberr = 0.4,
        rotate       = 0.35,
        focus_drop   = 0.5,
        background   = 0.1,
        dirt         = 0.0,
        jpeg         = 1.00)

    @staticmethod
    def gradient(img, lo=200, hi=255):
        w,h = img.size
        g   = Image.linear_gradient("L").resize((w,h))
        g   = g.rotate(random.uniform(0,360), expand=False)
        lo  = random.randint(lo, (lo+hi)//2)
        hi  = random.randint((lo+hi)//2, hi)
        g   = ImageOps.colorize(g, (lo,lo,lo), (hi,hi,hi))
        return ImageChops.multiply(img, g)

    @staticmethod
    def perspective(img, jitter=0.08, pad_frac=0.05):
        """Apply perspective skew with small padding to keep Braille fully visible."""
        # Pad canvas so skew won't clip edges
        w0, h0 = img.size
        pad = int(max(w0, h0) * pad_frac)
        if pad > 0:
            base_col = img.getpixel((0, 0))
            canvas = Image.new("RGB", (w0 + 2 * pad, h0 + 2 * pad), base_col)
            canvas.paste(img, (pad, pad))
            img = canvas

        w, h = img.size
        j = lambda: random.uniform(-jitter, jitter)
        src = [(0, 0), (w, 0), (w, h), (0, h)]
        dst = [(x + w * j(), y + h * j()) for (x, y) in src]

        A, B = [], []
        for (x, y), (u, v) in zip(src, dst):
            A += [[x, y, 1, 0, 0, 0, -u * x, -u * y],
                  [0, 0, 0, x, y, 1, -v * x, -v * y]]
            B += [u, v]
        A, B = np.asarray(A), np.asarray(B)
        coeffs = np.linalg.lstsq(A, B, rcond=None)[0]

        transformed = img.transform((w, h), Image.PERSPECTIVE, coeffs, Image.Resampling.BICUBIC)

        # Crop any uniform border introduced by padding to keep >90% occupancy
        bg = transformed.getpixel((0, 0))
        gray = transformed.convert("L")
        mask = gray.point(lambda p: 255 if abs(p - bg[0]) > 3 else 0)
        bbox = mask.getbbox()
        if bbox:
            transformed = transformed.crop(bbox)

        return transformed

    @staticmethod
    def blur(img, sigma=(0.3, 1.0)):
        return img.filter(ImageFilter.GaussianBlur(
               radius=random.uniform(*sigma)))

    @staticmethod
    def noise(img, sigma=(1,3)):
        arr = np.asarray(img).astype(np.float32)
        arr += np.random.normal(0, random.uniform(*sigma), arr.shape)
        arr  = np.clip(arr, 0, 255).astype(np.uint8)
        return Image.fromarray(arr)

    @staticmethod
    def white_balance(img, shift=(-8,8)):
        delta = random.randint(*shift) / 255.0
        r,g,b = img.split()
        r = ImageEnhance.Brightness(r).enhance(1+delta)
        b = ImageEnhance.Brightness(b).enhance(1-delta)
        return Image.merge("RGB",(r,g,b))

    @staticmethod
    def vignette(img, strength=(0.15,0.35), invert_prob=0.25):
        w, h = img.size
        y, x = np.ogrid[-1:1:h*1j, -1:1:w*1j]
        d = np.sqrt(x*x + y*y)
        d = d / d.max()

        invert = random.random() < invert_prob
        if invert:
            d = 1 - d

        f = random.uniform(*strength)
        alpha = np.clip((d**2) * f, 0, 1)

        if invert:
            alpha *= 0.5

        darker = ImageEnhance.Brightness(img).enhance(1 - f*0.7)
        mask = (alpha * 255).astype(np.uint8)
        return Image.composite(img, darker, Image.fromarray(mask, 'L'))

    @staticmethod
    def shadow(img, radius_frac=(0.15,0.4), darkness=(0.5,0.8)):
        w, h = img.size
        r = random.uniform(*radius_frac) * min(w, h)
        x0 = random.uniform(0, w)
        y0 = random.uniform(0, h)

        mask = Image.new('L', (w, h), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((x0 - r, y0 - r, x0 + r, y0 + r), fill=255)
        mask = mask.filter(ImageFilter.GaussianBlur(radius=r * 0.3))

        dark_factor = random.uniform(*darkness)
        darker = ImageEnhance.Brightness(img).enhance(dark_factor)
        return Image.composite(darker, img, mask)

    @staticmethod
    def chrome_aberr(img, shift_px=(-1, 1)):
        r, g, b = img.split()
        dx_r = random.randint(*shift_px)
        dy_r = random.randint(*shift_px)
        dx_b = random.randint(*shift_px)
        dy_b = random.randint(*shift_px)
        r = ImageChops.offset(r, dx_r, dy_r)
        b = ImageChops.offset(b, dx_b, dy_b)
        return Image.merge('RGB', (r, g, b))

    @staticmethod
    def jpeg(img, q=(75,95)):
        buf = BytesIO()
        img.save(buf,"JPEG",quality=random.randint(*q))
        return Image.open(buf)

    @staticmethod
    def rotate(img, degrees=(-2,2)):
        angle = random.uniform(*degrees)
        return img.rotate(angle, resample=Image.Resampling.BICUBIC,
                          expand=True, fillcolor=img.getpixel((0,0)))

    @staticmethod
    def focus_drop(img, sigma=(0.2,1.5)):
        w,h = img.size
        blur = img.filter(ImageFilter.GaussianBlur(radius=random.uniform(*sigma)))
        grad = np.tile(np.linspace(255,0,h, dtype=np.uint8)[:,None], (1,w))
        mask = Image.fromarray(grad, 'L')
        return Image.composite(blur, img, mask)

    @staticmethod
    def background(img, pad_frac=(0.01,0.03)):
        w,h = img.size
        pad = int(random.uniform(*pad_frac) * max(w,h))
        W,H = w+pad*2, h+pad*2
        base_col = random.randint(200,240)
        col = (base_col+random.randint(-5,5),)*3
        canvas = Image.new('RGB', (W,H), col)
        off_x = random.randint(0, pad)
        off_y = random.randint(0, pad)
        canvas.paste(img, (off_x, off_y))
        return canvas

    @staticmethod
    def dirt(img, density=0.001, darkness=(0.5,0.8)):
        w,h = img.size
        num = int(w*h*density)
        overlay = img.copy()
        draw = ImageDraw.Draw(overlay)
        for _ in range(num):
            x = random.randint(0,w-1)
            y = random.randint(0,h-1)
            r = random.randint(1,2)
            shade = int(255*random.uniform(*darkness))
            draw.ellipse((x-r,y-r,x+r,y+r), fill=(shade,shade,shade))
        alpha = 20
        return Image.blend(img, overlay, alpha/255.0)

    def __call__(self, img):
        if random.random()<self.cfg["gradient"]:      img=self.gradient(img)
        if random.random()<self.cfg["perspective"]:   img=self.perspective(img)
        if random.random()<self.cfg["blur"]:          img=self.blur(img)
        if random.random()<self.cfg["noise"]:         img=self.noise(img)
        if random.random()<self.cfg["white_balance"]: img=self.white_balance(img)
        if random.random()<self.cfg["vignette"]:      img=self.vignette(img)
        if random.random()<self.cfg["focus_drop"]:    img=self.focus_drop(img)
        if random.random()<self.cfg["shadow"]:        img=self.shadow(img)
        if random.random()<self.cfg["chrome_aberr"]:   img=self.chrome_aberr(img)
        if random.random()<self.cfg["background"]:    img=self.background(img)
        if random.random()<self.cfg["dirt"]:          img=self.dirt(img)
        if random.random()<self.cfg["jpeg"]:          img=self.jpeg(img)
        return img

if __name__ == "__main__":
    urdu = "کیکٹس بہت سا پانی ذخیرہ کر سکتا ہے کیونکہ وہ سبز ہوتے ہیں۔"
    import louis
    lines = [louis.translateString(["ur-pk-g1.utb"], urdu)]
    # Normalise text the same way as dataset generation
    lines_norm = _sanitize_text_lines(lines, max_cols=24)
    page, _ = BraillePage().draw_with_positions(lines_norm, max_cols=24, char_spacing=int(48*0.4))
    aug    = PhotoAug()

    page.save("braille_clean.png")
    aug(page.copy()).save(f"braille_aug.png")
       
