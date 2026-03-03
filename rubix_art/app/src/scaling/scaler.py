# src/scaling/scaler.py
"""
Scaler – Responsible for calculating the optimal discrete Rubik's cube grid
and resizing the input image to exactly match that sticker resolution.

Goal: Maximize resolution (use as many stickers/cubes as possible) while
      fitting within the desired physical size and never exceeding it.
"""

from pathlib import Path
from typing import Tuple, Dict, Union
from PIL import Image
import numpy as np


class Scaler:
    """
    Calculates optimal number of cubes and stickers, then resizes image accordingly.

    Usage in ImageMaker:
        scaler = Scaler(large_side_meters=..., cube_edge_meters=..., cube_n=...)
        scaled_image, metadata = scaler.scale(image_path)
    """

    def __init__(
        self,
        large_side_meters: float,
        cube_edge_meters: float,
        cube_n: int,                    # 3 → 3×3×3 cube (3 stickers per edge)
        sampling_factor: int = 4
    ):
        """
        Args:
            large_side_meters:  Desired physical size of the **longer** side (meters)
            cube_edge_meters:   Physical edge length of one Rubik's cube (e.g. 0.056)
            cube_n:             Number of stickers along one cube edge (3,4,5…)
        """
        if large_side_meters <= 0:
            raise ValueError("large_side_meters must be > 0")
        if cube_edge_meters <= 0:
            raise ValueError("cube_edge_meters must be > 0")
        if cube_n < 2:
            raise ValueError("cube_n must be ≥ 2")

        self.large_side_m = large_side_meters
        self.cube_m       = cube_edge_meters
        self.stickers_per_cube = cube_n     # usually 3,4,5,6,7
        self.sampling_factor = max(1, sampling_factor)

    def scale(self, image_path: Union[str, Path]) -> Tuple[Image.Image, Dict]:
        """
        Main method: resize image to optimal sticker grid.

        Returns:
            (scaled_image: PIL.Image,
             metadata: dict with grid dimensions and other info)
        """
        path = Path(image_path)
        if not path.is_file():
            raise FileNotFoundError(f"Image not found: {path}")

        # ── 1. Load original image and get aspect ratio ───────────────────────
        original = Image.open(path)
        orig_w, orig_h = original.size
        aspect_ratio = orig_w / orig_h

        # ── 2. Calculate maximum number of cubes we can fit on the long side ──
        max_cubes_long = int(np.floor(self.large_side_m / self.cube_m))
        if max_cubes_long < 1:
            raise ValueError(
                f"Desired size {self.large_side_m}m too small for cubes of {self.cube_m}m"
            )

        # ── 3. Decide orientation: which side gets max_cubes_long ─────────────
        if orig_w >= orig_h:
            # Landscape / square → width is long side
            num_cubes_w = max_cubes_long
            num_cubes_h = int(np.floor(num_cubes_w / aspect_ratio))
        else:
            # Portrait → height is long side
            num_cubes_h = max_cubes_long
            num_cubes_w = int(np.floor(num_cubes_h * aspect_ratio))

        # Ensure we have at least 1 cube in each direction
        num_cubes_w = max(1, num_cubes_w)
        num_cubes_h = max(1, num_cubes_h)

        # ── 4. Convert cubes → sticker pixels ─────────────────────────────────
        stickers_w = num_cubes_w * self.stickers_per_cube
        stickers_h = num_cubes_h * self.stickers_per_cube

        # ── 5. Resize image to exact sticker grid (high quality down/up-sampling) ─
        # LANCZOS is usually best for downscaling photos; BICUBIC also good
        scaled_image = original.resize(
            (stickers_w, stickers_h),
            resample=Image.Resampling.LANCZOS
        )

        # ── 6. Prepare metadata for downstream classes (splitter, builder, etc.) ─
        metadata = {
            "original_size":        (orig_w, orig_h),
            "aspect_ratio":         aspect_ratio,
            "num_cubes":            (num_cubes_w, num_cubes_h),
            "total_cubes":          num_cubes_w * num_cubes_h,
            "stickers_per_cube":    self.stickers_per_cube,
            "sticker_grid":         (stickers_w, stickers_h),      # ← most important
            "physical_size_m": {
                "width":  num_cubes_w * self.cube_m,
                "height": num_cubes_h * self.cube_m,
            },
            "scale_factor":         stickers_w / orig_w,           # approx
        }

        return scaled_image, metadata


# ── Optional: small test / demo when running file directly ─────────────────────
if __name__ == "__main__":
    # Example usage (for development / debugging)
    scaler = Scaler(
        large_side_meters=2.4,
        cube_edge_meters=0.056,
        cube_n=3
    )

    try:
        img, meta = scaler.scale("example/portrait.jpg")
        print("Scaled to:", img.size)
        print("Metadata:", meta)
        # img.show()  # uncomment to visually check
    except Exception as e:
        print("Error:", e)