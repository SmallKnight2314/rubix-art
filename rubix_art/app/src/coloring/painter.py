# src/coloring/painter.py
"""
Painter – Super-samples from the original high-res image and assigns closest Rubik's color.
Now supports optional color swapping by name (e.g. swap Blue ↔ Green).
"""

from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from PIL import Image


class Painter:
    DEFAULT_PALETTE = [
        (255, 255, 255),   # White      index 0
        (255, 213,   0),   # Yellow     index 1
        (183,  18,  52),   # Red        index 2
        (255,  88,   0),   # Orange     index 3
        (  0,  70, 173),   # Blue       index 4
        (  0, 155,  72),   # Green      index 5
    ]

    def __init__(
        self,
        palette: Optional[List[Tuple[int, int, int]]] = None,
        color_swaps: Optional[Dict[str, str]] = None,
    ):
        """
        Args:
            palette:     Custom list of 6 RGB tuples (optional)
            color_swaps: Dict like {"Blue": "Green", "Green": "Blue"} to remap colors
        """
        self.palette = palette if palette else self.DEFAULT_PALETTE
        if len(self.palette) != 6:
            raise ValueError("Palette must contain exactly 6 RGB tuples")

        self.palette_np = np.array(self.palette, dtype=np.float32)
        self.names = ["White", "Yellow", "Red", "Orange", "Blue", "Green"]

        # ── Color swapping logic ─────────────────────────────────────────────
        self.index_map = list(range(6))  # default: identity mapping

        if color_swaps:
            for from_name, to_name in color_swaps.items():
                try:
                    from_idx = self.names.index(from_name)
                    to_idx   = self.names.index(to_name)
                    self.index_map[from_idx] = to_idx
                    print(f"Color swap applied: {from_name} (#{from_idx}) → {to_name} (#{to_idx})")
                except ValueError as e:
                    print(f"Warning: Cannot swap '{from_name}' → '{to_name}': {e}")

    def _average_region(
        self,
        original: Image.Image,
        x1: float, y1: float, x2: float, y2: float
    ) -> np.ndarray:
        box = (max(0, int(x1)), max(0, int(y1)), min(original.width, int(x2)), min(original.height, int(y2)))
        if box[2] <= box[0] or box[3] <= box[1]:
            return np.array([128, 128, 128], dtype=np.float32)
        crop = original.crop(box)
        arr = np.array(crop.convert("RGB"), dtype=np.float32)
        return arr.mean(axis=(0, 1))

    def paint(
        self,
        mosaic_structure: List[List[Dict]],
        original_image: Image.Image,
        metadata: Dict[str, Any],
    ) -> List[List[Dict]]:
        sf_w = metadata["scale_factor_w"]
        sf_h = metadata["scale_factor_h"]

        total = 0
        counts = [0] * 6

        for cube_row in mosaic_structure:
            for cube in cube_row:
                for sticker_row in cube["stickers"]:
                    for sticker in sticker_row:
                        rx1, ry1, rx2, ry2 = sticker["pixel_region"]
                        ox1 = rx1 * sf_w
                        oy1 = ry1 * sf_h
                        ox2 = rx2 * sf_w
                        oy2 = ry2 * sf_h

                        avg = self._average_region(original_image, ox1, oy1, ox2, oy2)

                        # Find raw closest color index
                        raw_idx = int(np.argmin(np.linalg.norm(self.palette_np - avg, axis=1)))

                        # Apply swap/remapping if defined
                        final_idx = self.index_map[raw_idx]

                        assigned_color = tuple(int(v) for v in self.palette_np[final_idx])

                        sticker["assigned_color"] = assigned_color
                        sticker["color_index"]    = final_idx
                        sticker["color_name"]     = self.names[final_idx]

                        counts[final_idx] += 1
                        total += 1

        print(f"Super-sampled {total:,} stickers from original image")
        print("Final color distribution (after swaps):")
        for i, name in enumerate(self.names):
            print(f"  {name:8}: {counts[i]:,}")

        return mosaic_structure
