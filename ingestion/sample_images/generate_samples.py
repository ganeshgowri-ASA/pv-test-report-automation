"""
Generate Synthetic Sample Images for Testing

Creates realistic sample images for testing the image processing engine.
"""

import cv2
import numpy as np
from pathlib import Path


def generate_el_normal(output_path: str):
    """Generate normal EL image."""
    # Create base grayscale image
    image = np.ones((1080, 1920), dtype=np.uint8) * 150

    # Add solar cells (6x10 grid)
    cell_width = 150
    cell_height = 150
    spacing = 20

    for row in range(6):
        for col in range(10):
            x = col * (cell_width + spacing) + 100
            y = row * (cell_height + spacing) + 100

            # Draw cell with slight variation
            intensity = np.random.randint(180, 220)
            cv2.rectangle(image, (x, y), (x + cell_width, y + cell_height), intensity, -1)

            # Add busbar lines (bright)
            for i in range(3):
                line_x = x + (i + 1) * cell_width // 4
                cv2.line(image, (line_x, y), (line_x, y + cell_height), 230, 2)

    # Add some noise
    noise = np.random.normal(0, 5, image.shape).astype(np.int16)
    image = np.clip(image.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    cv2.imwrite(output_path, image)
    print(f"Generated: {output_path}")


def generate_el_cracked(output_path: str):
    """Generate EL image with cracks."""
    # Start with normal image
    image = np.ones((1080, 1920), dtype=np.uint8) * 150

    # Add cells
    cell_width = 150
    cell_height = 150
    spacing = 20

    for row in range(6):
        for col in range(10):
            x = col * (cell_width + spacing) + 100
            y = row * (cell_height + spacing) + 100
            intensity = np.random.randint(180, 220)
            cv2.rectangle(image, (x, y), (x + cell_width, y + cell_height), intensity, -1)

    # Add cracks (dark lines)
    cracks = [
        ((300, 200), (500, 600)),
        ((800, 300), (1000, 700)),
        ((1400, 400), (1600, 900)),
    ]

    for start, end in cracks:
        cv2.line(image, start, end, 30, 3)
        # Add jagged edges to make it look more like a crack
        for i in range(10):
            offset_x = np.random.randint(-5, 5)
            offset_y = int((end[1] - start[1]) * i / 10)
            pt1 = (start[0] + offset_x, start[1] + offset_y)
            pt2 = (start[0] + offset_x, start[1] + offset_y + 20)
            cv2.line(image, pt1, pt2, 40, 1)

    cv2.imwrite(output_path, image)
    print(f"Generated: {output_path}")


def generate_el_dark_spots(output_path: str):
    """Generate EL image with dark spots."""
    image = np.ones((1080, 1920), dtype=np.uint8) * 180

    # Add cells
    cell_width = 150
    cell_height = 150
    spacing = 20

    for row in range(6):
        for col in range(10):
            x = col * (cell_width + spacing) + 100
            y = row * (cell_height + spacing) + 100
            intensity = np.random.randint(180, 220)
            cv2.rectangle(image, (x, y), (x + cell_width, y + cell_height), intensity, -1)

    # Add dark spots
    dark_spots = [
        (400, 300, 40),
        (900, 500, 60),
        (1500, 700, 50),
        (700, 800, 35),
    ]

    for x, y, radius in dark_spots:
        cv2.circle(image, (x, y), radius, 25, -1)
        # Add gradient edge
        cv2.circle(image, (x, y), radius + 10, 60, 2)

    cv2.imwrite(output_path, image)
    print(f"Generated: {output_path}")


def generate_visual_normal(output_path: str):
    """Generate normal visual inspection image."""
    # Blue-ish color for solar panel
    image = np.ones((1080, 1920, 3), dtype=np.uint8)
    image[:, :] = [180, 120, 80]  # BGR

    # Add grid lines (silver busbars)
    for i in range(10, 1920, 190):
        cv2.line(image, (i, 0), (i, 1080), (220, 220, 220), 2)

    for j in range(10, 1080, 180):
        cv2.line(image, (0, j), (1920, j), (220, 220, 220), 2)

    # Add slight texture
    noise = np.random.normal(0, 3, image.shape).astype(np.int16)
    image = np.clip(image.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    cv2.imwrite(output_path, image)
    print(f"Generated: {output_path}")


def generate_visual_discoloration(output_path: str):
    """Generate visual image with discoloration."""
    # Start with normal
    image = np.ones((1080, 1920, 3), dtype=np.uint8)
    image[:, :] = [180, 120, 80]

    # Add grid
    for i in range(10, 1920, 190):
        cv2.line(image, (i, 0), (i, 1080), (220, 220, 220), 2)

    # Add brown/yellow discoloration patches
    discolor_regions = [
        ((300, 200), (600, 500)),
        ((1000, 400), (1400, 800)),
    ]

    for (x1, y1), (x2, y2) in discolor_regions:
        # Brown-yellow color
        overlay = image[y1:y2, x1:x2].copy()
        overlay[:, :, 0] = np.clip(overlay[:, :, 0] - 50, 0, 255)  # Less blue
        overlay[:, :, 1] = np.clip(overlay[:, :, 1] + 30, 0, 255)  # More green
        overlay[:, :, 2] = np.clip(overlay[:, :, 2] + 50, 0, 255)  # More red
        image[y1:y2, x1:x2] = overlay

    cv2.imwrite(output_path, image)
    print(f"Generated: {output_path}")


def generate_visual_bubbles(output_path: str):
    """Generate visual image with bubbles."""
    image = np.ones((1080, 1920, 3), dtype=np.uint8)
    image[:, :] = [180, 120, 80]

    # Add bubbles (circles with highlights)
    bubbles = [
        (500, 400, 50),
        (1200, 600, 40),
        (800, 800, 35),
    ]

    for x, y, radius in bubbles:
        # Bubble edge (darker)
        cv2.circle(image, (x, y), radius, (120, 80, 60), -1)
        # Highlight (lighter)
        cv2.circle(image, (x - 10, y - 10), radius // 3, (200, 160, 120), -1)

    cv2.imwrite(output_path, image)
    print(f"Generated: {output_path}")


def generate_multimeter_display(output_path: str):
    """Generate multimeter display image."""
    image = np.ones((480, 640, 3), dtype=np.uint8) * 40

    # Add digital display area (greenish)
    cv2.rectangle(image, (100, 150), (540, 300), (80, 80, 80), -1)
    cv2.rectangle(image, (110, 160), (530, 290), (40, 60, 40), -1)

    # Add reading text
    cv2.putText(image, "12.45 V", (150, 250),
                cv2.FONT_HERSHEY_SIMPLEX, 2.5, (0, 255, 0), 4)

    cv2.imwrite(output_path, image)
    print(f"Generated: {output_path}")


def generate_chamber_display(output_path: str):
    """Generate environmental chamber display."""
    image = np.ones((600, 800, 3), dtype=np.uint8) * 200

    # Display area
    cv2.rectangle(image, (50, 50), (750, 550), (100, 100, 100), -1)

    # Temperature
    cv2.putText(image, "Temperature:", (100, 150),
                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2)
    cv2.putText(image, "85.2 C", (100, 220),
                cv2.FONT_HERSHEY_SIMPLEX, 2.0, (0, 255, 255), 3)

    # Humidity
    cv2.putText(image, "Humidity:", (100, 320),
                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2)
    cv2.putText(image, "45.8 %", (100, 390),
                cv2.FONT_HERSHEY_SIMPLEX, 2.0, (0, 255, 255), 3)

    cv2.imwrite(output_path, image)
    print(f"Generated: {output_path}")


def main():
    """Generate all sample images."""
    output_dir = Path(__file__).parent

    print("Generating sample images...")

    # EL images
    generate_el_normal(str(output_dir / "el_normal.jpg"))
    generate_el_cracked(str(output_dir / "el_cracked.jpg"))
    generate_el_dark_spots(str(output_dir / "el_dark_spots.jpg"))

    # Visual inspection images
    generate_visual_normal(str(output_dir / "visual_normal.jpg"))
    generate_visual_discoloration(str(output_dir / "visual_discoloration.jpg"))
    generate_visual_bubbles(str(output_dir / "visual_bubbles.jpg"))

    # Equipment displays
    generate_multimeter_display(str(output_dir / "multimeter_reading.jpg"))
    generate_chamber_display(str(output_dir / "chamber_display.jpg"))

    print("\nAll sample images generated successfully!")
    print(f"Location: {output_dir}")


if __name__ == "__main__":
    main()
