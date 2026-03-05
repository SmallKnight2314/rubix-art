# src/scaling/scaler.py
"""
Scaler – Calculates the largest feasible grid that fits within given max physical width & height.
Preserves aspect ratio. Returns a small scaled preview + metadata for layout.
"""

from pathlib import Path
from typing import Tuple, Dict, Union
from PIL import Image
import numpy as np


class Scaler:
    def __init__(
        self,
        max_width_meters: float,
        max_height_meters: float,
        cube_edge_meters: float,
        cube_n: int,
    ):
        if max_width_meters <= 0 or max_height_meters <= 0:
            raise ValueError("max_width_meters and max_height_meters must be > 0")
        if cube_edge_meters <= 0:
            raise ValueError("cube_edge_meters must be > 0")
        if cube_n < 2:
            raise ValueError("cube_n must be ≥ 2")

        self.max_w_m = max_width_meters
        self.max_h_m = max_height_meters
        self.cube_m  = cube_edge_meters
        self.n       = cube_n  # stickers per cube edge

    def scale(self, image_path: Union[str, Path]) -> Tuple[Image.Image, Dict]:
        path = Path(image_path)
        if not path.is_file():
            raise FileNotFoundError(f"Image not found: {path}")

        original = Image.open(path)
        orig_w, orig_h = original.size
        aspect = orig_w / orig_h

        # Max cubes that fit in each dimension
        max_c_w = int(np.floor(self.max_w_m / self.cube_m))
        max_c_h = int(np.floor(self.max_h_m / self.cube_m))

        # Fit within both constraints while preserving aspect
        if orig_w >= orig_h:
            c_w = max_c_w
            c_h = min(max_c_h, int(np.floor(c_w / aspect)))
        else:
            c_h = max_c_h
            c_w = min(max_c_w, int(np.floor(c_h * aspect)))

        c_w = max(1, c_w)
        c_h = max(1, c_h)

        stickers_w = c_w * self.n
        stickers_h = c_h * self.n

        # Small preview version (used for grid layout & drawing)
        preview = original.resize((stickers_w, stickers_h), Image.Resampling.LANCZOS)

        metadata = {
            "original_size":        (orig_w, orig_h),
            "num_cubes":            (c_w, c_h),
            "sticker_grid":         (stickers_w, stickers_h),
            "stickers_per_cube":    self.n,
            "physical_size_m":      {"width": c_w * self.cube_m, "height": c_h * self.cube_m},
            "scale_factor_w":       orig_w / stickers_w,   # crucial for super-sampling
            "scale_factor_h":       orig_h / stickers_h,
        }

        return preview, metadata
