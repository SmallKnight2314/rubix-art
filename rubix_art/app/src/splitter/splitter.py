# src/splitter/splitter.py
"""
Splitter – Divides a **super-sampled** image into a nested structure representing
Rubik's cube layout: rows/columns of cubes → each cube's visible face →
n×n sticker regions.

All pixel coordinates are in the super-sampled space.
Each sticker also stores 'final_pixel_region' for downsampled placement in Builder.
"""

from typing import List, Dict, Any
import numpy as np
from PIL import Image


class Splitter:
    def __init__(self, cube_n: int):
        if cube_n < 2:
            raise ValueError("cube_n must be at least 2")
        self.cube_n = cube_n
        self.sticker_size_px = None  # final size, will be calculated

    def split(
        self,
        scaled_image: Image.Image,
        metadata: Dict[str, Any]
    ) -> List[List[Dict]]:
        """
        Divides the super-sampled image into cubes and stickers.

        Important:
        - All 'pixel_region' keys are in **super-sampled pixel coordinates**
        - New key 'final_pixel_region' contains coordinates in the final grid
          (for Builder to place colors correctly after downsampling)
        """
        if scaled_image.mode != "RGB":
            scaled_image = scaled_image.convert("RGB")

        # ── Extract dimensions from metadata ────────────────────────────────
        num_cubes_w, num_cubes_h = metadata["num_cubes"]
        final_stickers_w, final_stickers_h = metadata["sticker_grid"]
        super_w, super_h = metadata.get("super_sample_grid", scaled_image.size)
        detail_mult = metadata.get("detail_multiplier", 1)

        # Validate image size matches super-sampled expectation
        if scaled_image.size != (super_w, super_h):
            raise ValueError(
                f"Received image size {scaled_image.size} does not match "
                f"expected super_sample_grid {super_w}×{super_h}"
            )

        # Calculate sticker size in final and super-sampled space
        final_sticker_size = final_stickers_w // num_cubes_w
        super_sticker_size = final_sticker_size * detail_mult

        if final_sticker_size * num_cubes_w != final_stickers_w:
            raise ValueError("Final sticker grid is not evenly divisible by cubes")

        self.sticker_size_px = final_sticker_size

        # ── Build nested mosaic structure ────────────────────────────────────
        mosaic: List[List[Dict]] = []

        for cube_row in range(num_cubes_h):
            row_of_cubes = []

            for cube_col in range(num_cubes_w):
                # ── Coordinates in FINAL grid (for reference / Builder) ──────
                final_y_start = cube_row * (final_stickers_h // num_cubes_h)
                final_x_start = cube_col * (final_stickers_w // num_cubes_w)
                final_y_end   = final_y_start + (final_stickers_h // num_cubes_h)
                final_x_end   = final_x_start + (final_stickers_w // num_cubes_w)

                # ── Scale up to super-sampled space ──────────────────────────
                y_start = final_y_start * detail_mult
                x_start = final_x_start * detail_mult
                y_end   = final_y_end   * detail_mult
                x_end   = final_x_end   * detail_mult

                cube_dict = {
                    "position": (cube_col, cube_row),
                    "pixel_region": (x_start, y_start, x_end, y_end),          # super-sampled
                    "final_pixel_region": (final_x_start, final_y_start, final_x_end, final_y_end),
                    "stickers": []
                }

                # ── Subdivide cube into n×n stickers (super-sampled coords) ───
                for sticker_r in range(self.cube_n):
                    sticker_row = []

                    for sticker_c in range(self.cube_n):
                        sy = y_start + sticker_r * super_sticker_size
                        sx = x_start + sticker_c * super_sticker_size
                        sy_end = sy + super_sticker_size
                        sx_end = sx + super_sticker_size

                        sticker_crop = scaled_image.crop((sx, sy, sx_end, sy_end))

                        sticker_dict = {
                            "position": (sticker_c, sticker_r),
                            "pixel_region": (sx, sy, sx_end, sy_end),           # super-sampled
                            "final_pixel_region": (
                                final_x_start + sticker_c * final_sticker_size,
                                final_y_start + sticker_r * final_sticker_size,
                                final_x_start + (sticker_c + 1) * final_sticker_size,
                                final_y_start + (sticker_r + 1) * final_sticker_size
                            ),
                            "image": sticker_crop,
                        }

                        sticker_row.append(sticker_dict)

                    cube_dict["stickers"].append(sticker_row)

                row_of_cubes.append(cube_dict)

            mosaic.append(row_of_cubes)

        print(f"Split complete: {num_cubes_h}×{num_cubes_w} cubes "
              f"({self.cube_n}×{self.cube_n} stickers per cube)")
        print(f"Working in super-sampled space: {super_w}×{super_h} px "
              f"(multiplier = {detail_mult})")

        return mosaic


# ── Test block (update path to a real image) ────────────────────────────────
if __name__ == "__main__":
    from src.scaling.scaler import Scaler

    scaler = Scaler(large_side_meters=1.0, cube_edge_meters=0.05, cube_n=3, detail_multiplier=4)
    img, meta = scaler.scale("path/to/your/test_image.jpg")   # ← CHANGE THIS

    splitter = Splitter(cube_n=3)
    structure = splitter.split(img, meta)

    # Debug print
    first_sticker = structure[0][0]["stickers"][0][0]
    print("First sticker final_pixel_region:", first_sticker["final_pixel_region"])
    print("First sticker super-sampled region:", first_sticker["pixel_region"])
