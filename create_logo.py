from PIL import Image, ImageDraw, ImageFont
import os

# Create a new image with a white background
img = Image.new('RGB', (200, 80), color=(255, 255, 255))
d = ImageDraw.Draw(img)

# Draw a green rectangle
d.rectangle([(0, 0), (200, 80)], outline=(0, 100, 0), width=3)

# Add text
try:
    # Try to use a TrueType font if available
    font = ImageFont.truetype("arial.ttf", 24)
except IOError:
    # Fallback to default font
    font = ImageFont.load_default()

d.text((40, 30), "CSC Logo", fill=(0, 100, 0), font=font)

# Save the image
img.save('logo.png')

print("Logo created successfully!")
