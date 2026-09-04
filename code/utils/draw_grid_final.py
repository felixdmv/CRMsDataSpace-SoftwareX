from PIL import Image, ImageDraw, ImageFont
import os

img_path = r"C:\Users\felix\OneDrive - Universidad de Burgos\Documentos\CRMsDataSpace\geo-rag-explorer\georag_final.png"
out_path = r"C:\Users\felix\OneDrive - Universidad de Burgos\Documentos\CRMsDataSpace\geo-rag-explorer\georag_final_grid.png"

if not os.path.exists(img_path):
    print("Error: Image not found.")
    exit(1)

img = Image.open(img_path).convert("RGB")
draw = ImageDraw.Draw(img)
w, h = img.size
print(f"Loaded georag_final.png with size: {w}x{h}")

# Load default font
try:
    font = ImageFont.truetype("arial.ttf", 12)
except:
    font = ImageFont.load_default()

# Draw grid lines
for x in range(0, w, 50):
    draw.line((x, 0, x, h), fill="#FF0000", width=1 if x % 100 != 0 else 2)
    draw.text((x + 2, 5), str(x), fill="#FF0000", font=font)

for y in range(0, h, 50):
    draw.line((0, y, w, y), fill="#0000FF", width=1 if y % 100 != 0 else 2)
    draw.text((5, y + 2), str(y), fill="#0000FF", font=font)

img.save(out_path)
print("Grid image saved at:", out_path)
