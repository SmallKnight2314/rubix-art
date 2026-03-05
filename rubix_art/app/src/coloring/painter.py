# src/coloring/painter.py
"""
Painter – Uses super-sampling: averages large regions directly from the ORIGINAL high-res image.
"""

from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from PIL import Image


class Painter:
    DEFAULT_PALETTE = [
        (255, 255, 255),   # White
        (255, 213,   0),   # Yellow
        (183,  18,  52),   # Red
        (255,  88,   0),   # Orange
        (  0,  70, 173),   # Blue
        (  0, 155,  72),   # Green
    ]

    def __init__(self, palette: Optional[List[Tuple[int,int,int]]] = None):
        self.palette = palette if palette else self.DEFAULT_PALETTE
        if len(self.palette) != 6:
            raise ValueError("Palette must have exactly 6 RGB tuples")
        self.palette_np = np.array(self.palette, dtype=np.float32)
        self.names = ["White", "Yellow", "Red", "Orange", "Blue", "Green"]

    def _average_region(
        self,
        original: Image.Image,
        x1: float, y1: float, x2: float, y2: float
    ) -> np.ndarray:
        """Average color over a (possibly sub-pixel) region in original image"""
        box = (max(0, int(x1)), max(0, int(y1)), min(original.width, int(x2)), min(original.height, int(y2)))
        if box[2] <= box[0] or box[3] <= box[1]:
            return np.array([128, 128, 128], dtype=np.float32)  # fallback gray
        crop = original.crop(box)
        arr = np.array(crop.convert("RGB"), dtype=np.float32)
        return arr.mean(axis=(0,1))

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

        for row_cubes in mosaic_structure:
            for cube in row_cubes:
                for row_st in cube["stickers"]:
                    for st in row_st:
                        rx1, ry1, rx2, ry2 = st["pixel_region"]
                        ox1 = rx1 * sf_w
                        oy1 = ry1 * sf_h
                        ox2 = rx2 * sf_w
                        oy2 = ry2 * sf_h

                        avg = self._average_region(original_image, ox1, oy1, ox2, oy2)

                        idx = int(np.argmin(np.linalg.norm(self.palette_np - avg, axis=1)))
                        color = tuple(int(v) for v in self.palette_np[idx])

                        st["assigned_color"] = color
                        st["color_index"]    = idx
                        st["color_name"]     = self.names[idx]

                        counts[idx] += 1
                        total += 1

        print(f"Super-sampled {total:,} stickers from original high-res source")
        print("Color distribution:", ", ".join(f"{self.names[i]}: {c:,}" for i,c in enumerate(counts)))

        return mosaic_structure
