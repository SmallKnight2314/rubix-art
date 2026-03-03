# src/coloring/painter.py
"""
Painter – Assigns each sticker region the closest matching color from the
standard Rubik's cube palette (or a custom one).

Uses simple RGB Euclidean distance for matching.
(For better perceptual results Delta E 2000 could be added later.)
"""

from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from PIL import Image


class Painter:
    """
    Maps average sticker colors to the nearest Rubik's cube color.

    Main method:
        .paint(mosaic_structure) → same structure but with assigned colors
    """

    # Standard modern Rubik's cube colors (RGB tuples)
    # Sources: common manufacturer values ~2020–2026 (slight variations exist)
    # Order: White, Yellow, Red, Orange, Blue, Green
    DEFAULT_PALETTE = [
        (255, 255, 255),   # White
        (255, 213,   0),   # Yellow      #FFD500
        (183,  18,  52),   # Red         #B71234   (or #C41E3A / #B90000 variants)
        (255,  88,   0),   # Orange      #FF5800
        (  0,  70, 173),   # Blue        #0046AD   (or #0051BA)
        (  0, 155,  72),   # Green       #009B48   (or #009E60)
    ]

    def __init__(self, palette: Optional[List[Tuple[int, int, int]]] = None):
        """
        Args:
            palette: Optional list of 6 RGB tuples.
                     If None → uses DEFAULT_PALETTE above.
        """
        self.palette = palette if palette is not None else self.DEFAULT_PALETTE

        if len(self.palette) != 6:
            raise ValueError("Palette must contain exactly 6 colors (RGB tuples)")

        # Pre-convert palette to NumPy array for fast distance computation
        self.palette_array = np.array(self.palette, dtype=np.float32)

        # Optional: map index → color name (for reporting / debug)
        self.color_names = ["White", "Yellow", "Red", "Orange", "Blue", "Green"]

    def _average_color(self, sticker_img: Image.Image) -> np.ndarray:
        """
        Compute mean RGB color of a sticker region (PIL Image → float32 array).
        """
        arr = np.array(sticker_img.convert("RGB"), dtype=np.float32)
        return arr.mean(axis=(0, 1))  # shape (3,)

    def _find_closest_color_index(self, color: np.ndarray) -> int:
        """
        Euclidean distance in RGB space to nearest palette color.
        Returns index into self.palette.
        """
        # (6, 3) - (1, 3) → broadcasting → (6,) distances
        distances = np.linalg.norm(self.palette_array - color, axis=1)
        return int(np.argmin(distances))

    def paint(
        self,
        mosaic_structure: List[List[Dict]]
    ) -> List[List[Dict]]:
        """
        Process the nested mosaic structure from Splitter.
        Adds 'assigned_color' (RGB tuple) and optionally 'color_name' to each sticker.

        Returns:
            The same nested list structure, but with colors assigned.
            (Modifies in-place for memory efficiency, but returns it anyway)
        """
        total_stickers = 0
        assigned_counts = [0] * 6  # how many stickers got each color

        for cube_row in mosaic_structure:
            for cube in cube_row:
                for sticker_row in cube["stickers"]:
                    for sticker in sticker_row:
                        # Get average color of this sticker patch
                        avg_color = self._average_color(sticker["image"])

                        # Find closest match
                        idx = self._find_closest_color_index(avg_color)
                        assigned_color = tuple(int(c) for c in self.palette[idx])

                        # Store result
                        sticker["assigned_color"] = assigned_color
                        sticker["color_index"]    = idx
                        sticker["color_name"]     = self.color_names[idx]

                        assigned_counts[idx] += 1
                        total_stickers += 1

                        # Optional: can remove the "image" key now to save memory
                        # del sticker["image"]   # uncomment if memory is tight

        print(f"Color assignment complete: {total_stickers:,} stickers processed")
        print("Counts per color:")
        for i, name in enumerate(self.color_names):
            print(f"  {name:8}: {assigned_counts[i]:,}")

        return mosaic_structure


# ── Quick standalone test ───────────────────────────────────────────────────────
if __name__ == "__main__":
    # Dummy structure for testing (minimal)
    dummy_sticker = {
        "image": Image.new("RGB", (16, 16), color=(200, 50, 30))  # reddish
    }
    dummy_cube = {"stickers": [[dummy_sticker]]}
    dummy_mosaic = [[dummy_cube]]

    painter = Painter()
    result = painter.paint(dummy_mosaic)

    print("Assigned color for dummy sticker:", result[0][0]["stickers"][0][0]["assigned_color"])