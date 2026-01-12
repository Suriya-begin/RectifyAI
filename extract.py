import easyocr
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# ------------- CONFIG YOU CHANGE ------------- #

img_path = r"D:\waa\image_arch.png"                 # input image
out_path = r"D:\waa\image_arch_corrected_lik.png"  # output image

# Wrong -> Correct strings (must match EasyOCR output exactly on the left)
REPLACEMENTS = {
    "Positonial": "Positional",
    "LLM architecture Architecture": "LLM architecture",
    "LM Head": "LLM Head",
}

font_path = r"C:\Windows\Fonts\segoeui.ttf"         # font to draw with

# ------------- NO NEED TO EDIT BELOW ------------- #

# 1. Run EasyOCR
reader = easyocr.Reader(['en'])   # English
results = reader.readtext(img_path, detail=1)  # [ [bbox, text, conf], ... ]

print("Detected boxes:\n")
for bbox, text, conf in results:
    print(f"Text: {text!r} | Conf: {conf:.2f} | BBox: {bbox}")

# 2. Load image for drawing (PIL)
cv_img = cv2.imread(img_path)
if cv_img is None:
    raise FileNotFoundError(img_path)

pil_img = Image.fromarray(cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB))
draw = ImageDraw.Draw(pil_img)

for bbox, text, conf in results:
    original = text.strip()
    if not original:
        continue

    # Check if this text needs to be changed
    if original not in REPLACEMENTS:
        continue

    new_text = REPLACEMENTS[original]
    print(f"Replacing '{original}' -> '{new_text}'")

    # --------- ORIGINAL bbox (no padding) ---------
    xs = [int(p[0]) for p in bbox]
    ys = [int(p[1]) for p in bbox]
    x_min0, y_min0, x_max0, y_max0 = min(xs), min(ys), max(xs), max(ys)

    # Center of the original text region
    cx = (x_min0 + x_max0) // 2
    cy = (y_min0 + y_max0) // 2

    # --------- padded box only for cleaning background ---------
    pad = 2
    x_min = x_min0 - pad
    y_min = y_min0 - pad
    x_max = x_max0 + pad
    y_max = y_max0 + pad

    # ---- sample background + text color from this region ----
    roi = np.array(pil_img.crop((x_min, y_min, x_max, y_max)))
    gray = roi.mean(axis=2)

    # Background: light pixels
    bg_color = (255, 255, 255)
    mask_bg = gray > 200
    if np.any(mask_bg):
        bg_color = tuple(roi[mask_bg].mean(axis=0).astype(int))

    # Text: dark pixels
    text_color = (0, 0, 0)
    mask_fg = gray < 120
    if np.any(mask_fg):
        text_color = tuple(roi[mask_fg].mean(axis=0).astype(int))

    # ---- erase old text region ----
    draw.rectangle([x_min, y_min, x_max, y_max], fill=bg_color)

    # ---- choose font and auto-fit inside ORIGINAL box ----
    max_width = x_max0 - x_min0
    max_height = y_max0 - y_min0

    font_size = max_height
    try:
        font = ImageFont.truetype(font_path, font_size)
    except OSError:
        font = ImageFont.load_default()

    while True:
        bbox_text = draw.textbbox((0, 0), new_text, font=font)
        text_w = bbox_text[2] - bbox_text[0]
        text_h = bbox_text[3] - bbox_text[1]

        if text_w <= max_width and text_h <= max_height:
            break

        font_size -= 1
        if font_size <= 6:
            break
        font = ImageFont.truetype(font_path, font_size)

    # Final size
    bbox_text = draw.textbbox((0, 0), new_text, font=font)
    text_w = bbox_text[2] - bbox_text[0]
    text_h = bbox_text[3] - bbox_text[1]

    # --------- CENTER the corrected text on the original center ---------
    horizontal_bias = 0   # tweak if you want slight left/right shift
    vertical_bias = -1    # tiny upward shift to sit nicer on baseline

    text_x = cx - text_w // 2 + horizontal_bias
    text_y = cy - text_h // 2 + vertical_bias

    draw.text((text_x, text_y), new_text, font=font, fill=text_color)

# 3. Save final image
out_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
cv2.imwrite(out_path, out_img)
print(f"\nSaved corrected image to {out_path}")
