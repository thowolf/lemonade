#!/usr/bin/env python3
"""Generate PNG icons from SVG for Lemonade Electron App"""

from PIL import Image, ImageDraw
import os

def create_lemonade_icon(size):
    """Create a Lemonade icon at specified size"""
    # Create new image with transparent background
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Scale factor
    scale = size / 512.0
    
    # Colors
    bg_color_1 = (255, 193, 7)      # FFC107
    bg_color_2 = (255, 179, 0)      # FFB300
    lemon_color_1 = (255, 229, 127) # FFE57F
    lemon_color_2 = (255, 193, 7)   # FFC107
    lemon_stroke = (245, 127, 23)   # F57F17
    leaf_color = (102, 187, 106)    # 66BB6A
    leaf_stroke = (67, 160, 71)     # 43A047
    
    # Draw rounded background gradient (approximate)
    draw.rounded_rectangle(
        [(0, 0), (size-1, size-1)],
        radius=int(100 * scale),
        fill=bg_color_1,
        outline=bg_color_1
    )
    
    # Draw lemon shapes (simplified)
    # Left lemon
    lemon_left = [
        int(180 * scale - 85 * scale),
        int(260 * scale - 95 * scale),
        int(180 * scale + 85 * scale),
        int(260 * scale + 95 * scale)
    ]
    draw.ellipse(lemon_left, fill=lemon_color_1, outline=lemon_stroke, width=int(3*scale))
    
    # Right lemon
    lemon_right = [
        int(330 * scale - 85 * scale),
        int(260 * scale - 95 * scale),
        int(330 * scale + 85 * scale),
        int(260 * scale + 95 * scale)
    ]
    draw.ellipse(lemon_right, fill=lemon_color_1, outline=lemon_stroke, width=int(3*scale))
    
    # Bridge
    bridge = [
        int(255 * scale - 40 * scale),
        int(260 * scale - 80 * scale),
        int(255 * scale + 40 * scale),
        int(260 * scale + 80 * scale)
    ]
    draw.ellipse(bridge, fill=lemon_color_1, outline=lemon_stroke, width=int(3*scale))
    
    # Draw highlights
    draw.ellipse(
        [
            int(200 * scale - 25 * scale),
            int(200 * scale - 25 * scale),
            int(200 * scale + 25 * scale),
            int(200 * scale + 25 * scale)
        ],
        fill=(255, 255, 255, 77)  # 30% opacity
    )
    draw.ellipse(
        [
            int(310 * scale - 25 * scale),
            int(200 * scale - 25 * scale),
            int(310 * scale + 25 * scale),
            int(200 * scale + 25 * scale)
        ],
        fill=(255, 255, 255, 77)
    )
    
    return img

# Create all standard sizes
output_dir = os.path.dirname(os.path.abspath(__file__))
sizes = [16, 24, 32, 48, 64, 128, 256, 512]

print("📦 Erstelle Lemonade App Icons...")
print()

for size in sizes:
    try:
        icon = create_lemonade_icon(size)
        output_path = os.path.join(output_dir, f'icon_{size}.png')
        icon.save(output_path, 'PNG')
        print(f"  ✓ icon_{size}.png ({size}x{size}px)")
    except Exception as e:
        print(f"  ✗ icon_{size}.png: {e}")

print()
print("✅ Icons erstellt!")
print()
print("📋 Verwende diese Icons in electron-builder (package.json):")
print()
print('''  "build": {
    "appId": "com.lemonade.app",
    "files": ["main.js", "preload.js", "index.html"],
    "win": {
      "target": ["nsis", "portable"],
      "icon": "src/app/assets/icon_256.png"
    },
    "mac": {
      "icon": "src/app/assets/icon_512.png"
    },
    "linux": {
      "icon": "src/app/assets/icon_512.png"
    }
  }''')
