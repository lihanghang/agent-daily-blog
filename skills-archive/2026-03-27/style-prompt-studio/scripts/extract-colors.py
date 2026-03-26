#!/usr/bin/env python3
"""
Extract color palette from images for Retro Pop Art PPT Generator
Usage: python scripts/extract-colors.py <image_path>
"""

import sys
import json
from PIL import Image
from collections import Counter


def rgb_to_hex(rgb):
    """Convert RGB tuple to HEX string"""
    return '#{:02x}{:02x}{:02x}'.format(*rgb)


def hex_to_rgb(hex_color):
    """Convert HEX string to RGB tuple"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def get_brightness(rgb):
    """Calculate perceived brightness of a color"""
    r, g, b = rgb
    return (299 * r + 587 * g + 114 * b) / 1000


def quantize_color(rgb, factor=30):
    """Quantize color for grouping similar colors"""
    return tuple(c // factor * factor for c in rgb)


def extract_colors(image_path, num_colors=6):
    """
    Extract dominant colors from an image

    Args:
        image_path: Path to the image file
        num_colors: Number of colors to extract (default: 6)

    Returns:
        Dictionary with background color and palette
    """
    try:
        img = Image.open(image_path)
        img = img.convert('RGB')
    except FileNotFoundError:
        print(f"Error: Image not found at {image_path}")
        sys.exit(1)
    except Exception as e:
        print(f"Error opening image: {e}")
        sys.exit(1)

    # Resize for faster processing
    img_small = img.resize((100, 100))

    # Get all pixels
    pixels = list(img_small.getdata())

    # Quantize and count colors
    color_counts = Counter()
    for pixel in pixels:
        quantized = quantize_color(pixel)
        color_counts[quantized] += 1

    # Get top colors
    top_colors = color_counts.most_common(num_colors * 2)

    # Filter out very similar colors
    unique_colors = []
    min_distance = 50  # Minimum distance between colors

    for color, count in top_colors:
        is_unique = True
        for existing in unique_colors:
            distance = sum((a - b) ** 2 for a, b in zip(color, existing[0]))
            if distance < min_distance ** 2:
                is_unique = False
                break
        if is_unique:
            unique_colors.append((color, count))

    # Sort by brightness to identify background
    unique_colors.sort(key=lambda x: get_brightness(x[0]), reverse=True)

    # Assume the brightest color is the background
    background = unique_colors[0][0] if unique_colors else (245, 240, 230)

    # Get accent colors (excluding background and very dark colors)
    accent_colors = []
    for color, count in unique_colors[1:]:
        brightness = get_brightness(color)
        # Skip very dark colors (likely text) and very bright colors (background)
        if 50 < brightness < 220:
            accent_colors.append(color)
        if len(accent_colors) >= num_colors:
            break

    # If we don't have enough colors, use k-means style approach
    if len(accent_colors) < num_colors:
        # Sample colors from the image more systematically
        sample_points = [
            (25, 25), (75, 25), (50, 50),
            (25, 75), (75, 75)
        ]
        img_sample = img.resize((100, 100))
        for x_pct, y_pct in sample_points:
            if len(accent_colors) >= num_colors:
                break
            x = int(x_pct * img_sample.width / 100)
            y = int(y_pct * img_sample.height / 100)
            color = img_sample.getpixel((x, y))
            brightness = get_brightness(color)
            if 50 < brightness < 220:
                # Check if not already in list
                is_duplicate = False
                for existing in accent_colors:
                    distance = sum((a - b) ** 2 for a, b in zip(color, existing))
                    if distance < 30 ** 2:
                        is_duplicate = True
                        break
                if not is_duplicate:
                    accent_colors.append(color)

    # Build result
    result = {
        "source": image_path,
        "background": rgb_to_hex(background),
        "background_rgb": background,
        "palette": [rgb_to_hex(c) for c in accent_colors[:num_colors]],
        "palette_rgb": accent_colors[:num_colors],
        "analysis": {
            "style_suggestion": "retro-pop-art" if len(accent_colors) >= 4 else "minimal",
            "color_harmony": "analogous" if len(set(c[0] // 50 for c in accent_colors)) <= 2 else "complementary"
        }
    }

    return result


def generate_prompt(result):
    """Generate AI image generation prompt from extracted colors"""
    palette_str = " ".join(result["palette"])

    prompt = f"""
## AI Image Generation Prompt

```
Retro pop art style, 1970s aesthetic,
flat design with thick black outlines,
background: {result["background"]},
accent colors: {" ".join(result["palette"])},
geometric decorative elements,
clean grid layout,
no gradients, no shadows,
high contrast, bold typography,
--ar 16:9 --style raw
```

## Negative Prompt

```
gradients, shadows, 3d effects, realistic,
photorealistic, blurry, low contrast,
pastel colors, neon colors,
cluttered layout, thin fonts
```
"""
    return prompt


def main():
    if len(sys.argv) < 2:
        print("Usage: python extract-colors.py <image_path> [--prompt]")
        print("\nOptions:")
        print("  --prompt    Also generate AI image generation prompt")
        sys.exit(1)

    image_path = sys.argv[1]
    generate_prompt_flag = "--prompt" in sys.argv

    result = extract_colors(image_path)

    # Output JSON
    print(json.dumps(result, indent=2))

    if generate_prompt_flag:
        print("\n" + generate_prompt(result))


if __name__ == "__main__":
    main()
