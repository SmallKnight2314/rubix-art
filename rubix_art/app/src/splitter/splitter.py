# src/splitter/splitter.py
"""
Splitter – Divides a scaled image into a nested structure representing
Rubik's cube layout: rows/columns of cubes → each cube's visible face →
n×n sticker regions.

The output structure is passed to the Painter for color assignment.
"""

from typing import List, Dict, Any, Tuple
import numpy as np
from PIL import Image


class Splitter:
    """
    Splits scaled image into cube → sticker hierarchy.

    Main method:
        .split(scaled_image: PIL.Image, metadata: dict) → nested structure
    """

    def __init__(self, cube_n: int):
        """
        Args:
            cube_n: number of stickers along one edge of a cube (3,4,5...)
        """
        if cube_n < 2:
            raise ValueError("cube_n must be at least 2")
        self.cube_n = cube_n
        self.sticker_size_px = None   # will be set from metadata

    def split(
        self,
        scaled_image: Image.Image,
        metadata: Dict[str, Any]
    ) -> List[List[Dict]]:
        """
        Main method: divide image into grid of cubes, each containing n×n stickers.

        Args:
            scaled_image: PIL Image already resized to exact sticker resolution
            metadata:      dict from Scaler containing at least:
                           - 'num_cubes': (width_in_cubes, height_in_cubes)
                           - 'sticker_grid': (total_width_px, total_height_px)
                           - 'stickers_per_cube': same as cube_n

        Returns:
            mosaic: list of rows, each row is list of cube-dicts

        Structure example (for 3×3 cubes):
        mosaic[row][col] = {
            'position':   (cube_col, cube_row),
            'pixel_region': (x_start, y_start, x_end, y_end),
            'stickers':   list[list[dict]]   # n rows × n cols of sticker dicts
        }

        Each sticker dict:
            {
                'position': (sticker_r, sticker_c),
                'pixel_region': (sx, sy, sx+size, sy+size),
                'image': PIL.Image  # cropped sub-region (small!)
            }
        """

        # ── Validate inputs ───────────────────────────────────────────────────
        if scaled_image.mode != "RGB":
            scaled_image = scaled_image.convert("RGB")

        img_array = np.array(scaled_image)  # shape: (h, w, 3)

        num_cubes_w, num_cubes_h = metadata["num_cubes"]
        stickers_w, stickers_h   = metadata["sticker_grid"]
        stickers_per_cube        = metadata.get("stickers_per_cube", self.cube_n)

        if stickers_w != img_array.shape[1] or stickers_h != img_array.shape[0]:
            raise ValueError("Scaled image dimensions do not match metadata sticker grid")

        if stickers_per_cube != self.cube_n:
            raise ValueError("Metadata cube_n does not match Splitter configuration")

        sticker_px_size = stickers_w // num_cubes_w
        if sticker_px_size * num_cubes_w != stickers_w:
            raise ValueError("Sticker grid is not evenly divisible by cubes")

        self.sticker_size_px = sticker_px_size

        # ── Build nested structure ────────────────────────────────────────────
        mosaic: List[List[Dict]] = []

        for cube_row in range(num_cubes_h):
            row_of_cubes = []

            for cube_col in range(num_cubes_w):
                # Pixel coordinates of this cube's face
                y_start = cube_row * stickers_h // num_cubes_h
                y_end   = y_start + stickers_h // num_cubes_h
                x_start = cube_col * stickers_w // num_cubes_w
                x_end   = x_start + stickers_w // num_cubes_w

                cube_dict = {
                    "position": (cube_col, cube_row),
                    "pixel_region": (x_start, y_start, x_end, y_end),
                    "stickers": []
                }

                # ── Subdivide this cube into n×n stickers ─────────────────────
                for sticker_r in range(self.cube_n):
                    sticker_row = []

                    for sticker_c in range(self.cube_n):
                        sy = y_start + sticker_r * sticker_px_size
                        sx = x_start + sticker_c * sticker_px_size

                        # Crop small sticker region (view, not copy → memory efficient)
                        # For real processing we usually convert to array slice anyway
                        sticker_crop = scaled_image.crop(
                            (sx, sy, sx + sticker_px_size, sy + sticker_px_size)
                        )

                        sticker_dict = {
                            "position": (sticker_c, sticker_r),   # column, row inside cube
                            "pixel_region": (sx, sy, sx + sticker_px_size, sy + sticker_px_size),
                            "image": sticker_crop,                # small PIL crop
                            # You can add "array": img_array[sy:sy+size, sx:sx+size] later
                        }

                        sticker_row.append(sticker_dict)

                    cube_dict["stickers"].append(sticker_row)

                row_of_cubes.append(cube_dict)

            mosaic.append(row_of_cubes)

        print(f"Split complete: {num_cubes_h} rows × {num_cubes_w} columns of cubes")
        print(f"Each cube contains {self.cube_n}×{self.cube_n} = {self.cube_n**2} stickers")

        return mosaic


# ── Minimal test when running file directly ─────────────────────────────────────
if __name__ == "__main__":
    from src.scaling.scaler import Scaler

    # Dummy test – assumes you have an image
    scaler = Scaler(large_side_meters=1.0, cube_edge_meters=0.05, cube_n=3)
    dummy_img, meta = scaler.scale("example/test.jpg")   # replace with real path

    splitter = Splitter(cube_n=3)
    structure = splitter.split(dummy_img, meta)

    # Quick inspection
    print("First cube, first row of stickers:")
    print(structure[0][0]["stickers"][0])