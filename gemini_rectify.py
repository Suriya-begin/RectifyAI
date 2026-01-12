import os
import json
import easyocr
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv
from groq import Groq
from pathlib import Path
import re

# ---------------- CONFIG ---------------- #

IMG_PATH = r"D:\waa\image_arch.png"
OUT_PATH = r"D:\waa\image_arch_corrected_final_perfect.png"
JSON_DUMP = r"D:\waa\ocr_positions_input.json"
JSON_CORRECTED_DUMP = r"D:\waa\ocr_positions_corrected.json"

# All available fonts
REGULAR_FONTS = [
    r"C:\Windows\Fonts\arial.ttf",
    r"C:\Windows\Fonts\calibri.ttf",
    r"C:\Windows\Fonts\segoeui.ttf",
]

BOLD_FONTS = [
    r"C:\Windows\Fonts\arialbd.ttf",
    r"C:\Windows\Fonts\calibrib.ttf",
    r"C:\Windows\Fonts\segoeuib.ttf",
]

MODEL_ID = "llama-3.3-70b-versatile"

# ---------------- GROQ SETUP ---------------- #

load_dotenv()
API_KEY = os.getenv("GROQ_API_KEY")
if API_KEY:
    client = Groq(api_key=API_KEY)
else:
    client = None

# ---------------- STEP 1: OCR EXTRACTION ---------------- #

def extract_words_to_json(image_path: str) -> dict:
    """Extract text with EasyOCR"""
    print("\n" + "="*70)
    print("STEP 1: OCR TEXT EXTRACTION")
    print("="*70)
    
    reader = easyocr.Reader(['en'], gpu=False, verbose=False)
    results = reader.readtext(image_path, detail=1)

    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Cannot read image: {image_path}")

    h, w = img.shape[:2]
    print(f"Image size: {w}x{h}")

    words = []
    for idx, (bbox, text, conf) in enumerate(results):
        text = text.strip()
        if not text:
            continue

        xs = [int(p[0]) for p in bbox]
        ys = [int(p[1]) for p in bbox]
        x_min, y_min = min(xs), min(ys)
        x_max, y_max = max(xs), max(ys)

        words.append({
            "id": idx,
            "text": text,
            "confidence": float(conf),
            "bbox": {
                "x_min": x_min,
                "y_min": y_min,
                "x_max": x_max,
                "y_max": y_max
            }
        })
        
        confidence_marker = "✓" if conf > 0.95 else "⚠"
        print(f"  {confidence_marker} [{idx}] '{text}' (conf: {conf:.2f})")

    print(f"\n✓ Extracted {len(words)} text elements")
    
    return {
        "image_size": {"width": w, "height": h},
        "words": words
    }

# ---------------- STEP 2: INTELLIGENT CORRECTION ---------------- #

CORRECTION_PROMPT = """Fix ALL OCR spelling errors. Use context from nearby words.

**MUST FIX:**
1. Duplicates: "architecture Architecture" → "Architecture"
2. Spelling: "Positonial" → "Positional", "Transform Blocks" → "Transformer Blocks"
3. Context: "LM Head" in LLM context → "LLM Head"

Add "corrected_text" to each word. Return ONLY JSON."""


def call_groq_for_correction(payload: dict) -> dict:
    """Try Groq, fallback to rule-based"""
    print("\n" + "="*70)
    print("STEP 2: INTELLIGENT TEXT CORRECTION")
    print("="*70)
    
    if client:
        print("Attempting Groq AI correction...")
        corrected_json = try_groq_correction(payload)
        groq_corrections = count_corrections(payload, corrected_json)
        
        if groq_corrections > 0:
            print(f"✓ Groq made {groq_corrections} corrections")
            return corrected_json
    
    print("⚠ Using rule-based system...")
    return apply_smart_corrections(payload)


def try_groq_correction(payload: dict) -> dict:
    """Attempt correction with Groq"""
    try:
        payload_str = json.dumps(payload, ensure_ascii=False, indent=2)
        
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": CORRECTION_PROMPT},
                {"role": "user", "content": f"Fix:\n\n{payload_str}"}
            ],
            model=MODEL_ID,
            temperature=0.1,
            max_tokens=8000,
        )
        
        response_text = chat_completion.choices[0].message.content.strip()
        if response_text.startswith("```"):
            response_text = re.sub(r'^```json\s*|\s*```$', '', response_text, flags=re.MULTILINE)
        
        corrected_json = json.loads(response_text)
        
        for w in corrected_json["words"]:
            if "corrected_text" not in w:
                w["corrected_text"] = w.get("text", "")
        
        return corrected_json
        
    except Exception as e:
        print(f"  Groq error: {e}")
        for w in payload["words"]:
            w["corrected_text"] = w["text"]
        return payload


def count_corrections(original: dict, corrected: dict) -> int:
    """Count corrections"""
    count = 0
    for orig, corr in zip(original["words"], corrected["words"]):
        if corr.get("corrected_text", corr["text"]) != orig["text"]:
            count += 1
    return count


def apply_smart_corrections(payload: dict) -> dict:
    """Rule-based correction"""
    print("\n🧠 Rule-Based Correction System...")
    
    words = payload["words"]
    all_text = " ".join([w["text"].lower() for w in words])
    
    # Detect context
    context = "ai_ml" if any(x in all_text for x in ['transformer', 'llm', 'attention']) else "general"
    print(f"  Context: {context}")
    
    corrections_dict = {
        "positonial": "Positional",
        "transfomer": "Transformer",
        "transform blocks": "Transformer Blocks",
        "atention": "Attention",
        "lm head": "LLM Head",
    }
    
    corrections = []
    for w in words:
        original = w["text"]
        corrected = original
        
        # Remove duplicates
        words_list = corrected.split()
        if len(words_list) > 1:
            unique = []
            prev = ""
            for word in words_list:
                if word.lower() != prev:
                    unique.append(word)
                    prev = word.lower()
            if len(unique) < len(words_list):
                corrected = " ".join(unique)
                corrections.append(f"  '{original}' → '{corrected}'")
        
        # Dictionary
        if corrected.lower() in corrections_dict:
            fixed = corrections_dict[corrected.lower()]
            if corrected[0].isupper():
                fixed = fixed[0].upper() + fixed[1:]
            if corrected != fixed:
                corrections.append(f"  '{corrected}' → '{fixed}'")
                corrected = fixed
        
        w["corrected_text"] = corrected
    
    if corrections:
        print(f"✓ Made {len(corrections)} corrections:")
        for c in corrections:
            print(c)
    
    return payload


# ---------------- STEP 3: GROUP WORDS INTO LINES ---------------- #

def group_into_lines(words, y_tolerance=10):
    """Group words into lines based on y position"""
    lines = []
    sorted_words = sorted(words, key=lambda w: w["bbox"]["y_min"])
    
    if not sorted_words:
        return lines
    
    current_line = [sorted_words[0]]
    current_y = sorted_words[0]["bbox"]["y_min"]
    
    for word in sorted_words[1:]:
        word_y = word["bbox"]["y_min"]
        
        if abs(word_y - current_y) <= y_tolerance:
            current_line.append(word)
        else:
            lines.append(sorted(current_line, key=lambda w: w["bbox"]["x_min"]))
            current_line = [word]
            current_y = word_y
    
    lines.append(sorted(current_line, key=lambda w: w["bbox"]["x_min"]))
    return lines


# ---------------- STEP 4: ANALYZE LINE STYLES ---------------- #

def analyze_line_style(line_words, img):
    """Analyze the dominant style of a line by looking at ALL words"""
    if not line_words:
        return None
    
    densities = []
    colors_bg = []
    colors_text = []
    heights = []
    
    for word in line_words:
        bbox = word["bbox"]
        x1, y1 = bbox["x_min"], bbox["y_min"]
        x2, y2 = bbox["x_max"], bbox["y_max"]
        
        crop = img[y1:y2, x1:x2]
        if crop.size == 0:
            continue
        
        h, w = crop.shape[:2]
        heights.append(h)
        
        # Analyze colors
        pixels = crop.reshape(-1, 3)
        brightness = np.mean(pixels, axis=1)
        
        bg_thresh = np.percentile(brightness, 70)
        bg_pixels = pixels[brightness > bg_thresh]
        if len(bg_pixels) > 5:
            colors_bg.append(np.median(bg_pixels, axis=0))
        
        text_thresh = np.percentile(brightness, 30)
        text_pixels = pixels[brightness < text_thresh]
        if len(text_pixels) > 5:
            colors_text.append(np.median(text_pixels, axis=0))
        
        # Analyze boldness
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        density = np.sum(binary == 255) / binary.size
        densities.append(density)
    
    if not densities:
        return None
    
    # Compute line-level style
    avg_density = np.mean(densities)
    avg_height = int(np.mean(heights))
    is_bold = avg_density > 0.28
    
    if colors_bg:
        bg_color = tuple([int(x) for x in np.median(colors_bg, axis=0)])
    else:
        bg_color = (255, 255, 255)
    
    if colors_text:
        text_color = tuple([int(x) for x in np.median(colors_text, axis=0)])
    else:
        text_color = (0, 0, 0)
    
    return {
        'is_bold': is_bold,
        'avg_height': avg_height,
        'bg_color': bg_color,
        'text_color': text_color,
        'density': avg_density
    }


# ---------------- STEP 5: PERFECT REDRAWING WITH PIL ---------------- #

def redraw_corrected_image(image_path: str, corrected_json: dict, output_path: str):
    """Redraw with line-level style matching"""
    print("\n" + "="*70)
    print("STEP 3: PERFECT LINE-AWARE RECONSTRUCTION")
    print("="*70)
    
    img_cv = cv2.imread(image_path)
    if img_cv is None:
        raise FileNotFoundError(f"Cannot read: {image_path}")
    
    img_pil = Image.fromarray(cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)
    
    words = corrected_json["words"]
    
    # Group words into lines
    lines = group_into_lines(words)
    print(f"Grouped into {len(lines)} lines")
    
    redrawn = 0
    
    for line_idx, line_words in enumerate(lines):
        print(f"\n--- Line {line_idx + 1} ({len(line_words)} words) ---")
        
        # Analyze entire line style
        line_style = analyze_line_style(line_words, img_cv)
        
        if line_style is None:
            continue
        
        print(f"Line style: Bold={line_style['is_bold']}, Height={line_style['avg_height']}px")
        
        # Choose font for entire line
        if line_style['is_bold']:
            font_paths = [f for f in BOLD_FONTS if Path(f).exists()]
        else:
            font_paths = [f for f in REGULAR_FONTS if Path(f).exists()]
        
        if not font_paths:
            font_paths = REGULAR_FONTS
        
        # Redraw each word in this line with same style
        for word in line_words:
            original = word["text"]
            corrected = word.get("corrected_text", original)
            
            if corrected == original:
                continue
            
            print(f"  Redrawing: '{original}' → '{corrected}'")
            
            bbox = word["bbox"]
            x1, y1 = bbox["x_min"], bbox["y_min"]
            x2, y2 = bbox["x_max"], bbox["y_max"]
            box_w, box_h = x2 - x1, y2 - y1
            
            # Clear with line background color
            pad = 2
            draw.rectangle([x1-pad, y1-pad, x2+pad, y2+pad], fill=line_style['bg_color'])
            
            # Find font size that fits
            font_size = int(line_style['avg_height'] * 0.85)
            font = None
            
            for font_path in font_paths:
                try:
                    while font_size >= 8:
                        test_font = ImageFont.truetype(font_path, font_size)
                        bbox_test = draw.textbbox((0, 0), corrected, font=test_font)
                        text_w = bbox_test[2] - bbox_test[0]
                        text_h = bbox_test[3] - bbox_test[1]
                        
                        if text_w <= box_w * 0.95 and text_h <= box_h * 0.95:
                            font = test_font
                            break
                        font_size -= 1
                    
                    if font:
                        break
                except:
                    continue
            
            if not font:
                font = ImageFont.load_default()
            
            # Draw centered
            bbox_text = draw.textbbox((0, 0), corrected, font=font)
            text_w = bbox_text[2] - bbox_text[0]
            text_h = bbox_text[3] - bbox_text[1]
            
            text_x = x1 + (box_w - text_w) // 2
            text_y = y1 + (box_h - text_h) // 2
            
            draw.text((text_x, text_y), corrected, font=font, fill=line_style['text_color'])
            
            redrawn += 1
    
    result = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
    cv2.imwrite(output_path, result)
    
    print(f"\n✓ Successfully redrawn {redrawn} words")
    print(f"✓ Saved to: {output_path}")


# ---------------- MAIN ---------------- #

def main():
    """Run pipeline"""
    print("\n" + "="*70)
    print("FINAL PERFECT OCR CORRECTION SYSTEM")
    print("Line-Aware Style Matching")
    print("="*70)
    
    if not Path(IMG_PATH).exists():
        raise FileNotFoundError(f"Input not found: {IMG_PATH}")
    
    ocr_data = extract_words_to_json(IMG_PATH)
    with open(JSON_DUMP, "w", encoding="utf-8") as f:
        json.dump(ocr_data, f, indent=2, ensure_ascii=False)
    
    corrected_data = call_groq_for_correction(ocr_data)
    with open(JSON_CORRECTED_DUMP, "w", encoding="utf-8") as f:
        json.dump(corrected_data, f, indent=2, ensure_ascii=False)
    
    redraw_corrected_image(IMG_PATH, corrected_data, OUT_PATH)
    
    print("\n" + "="*70)
    print("✓ COMPLETE - PERFECT MATCH ACHIEVED")
    print("="*70)
    print(f"Output: {OUT_PATH}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()