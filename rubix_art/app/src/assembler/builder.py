# src/assembler/builder.py
"""
Builder – Tight canvas version (no excess space on right or bottom).
Mosaic is perfectly centered, with thin padding around stickers and thicker padding around full cubes.
Ready for future labels/stats.
"""

from typing import List, Dict, Any, Tuple
from PIL import Image, ImageDraw


class Builder:
    def __init__(self):
        self.default_sticker_padding = 2          # thin dark border around each sticker
        self.default_cube_padding    = 6          # thicker border around each full cube
        self.default_padding_color   = (35, 35, 35)  # dark grey
        self.default_outer_margin    = 40         # space for future cube counts / scale markers

    def build(
        self,
        colored_mosaic: List[List[Dict]],
        metadata: Dict[str, Any],
        background_color: Tuple[int, int, int] = (255, 255, 255),
        
        sticker_padding: int = None,
        cube_padding: int = None,
        padding_color: Tuple[int, int, int] = None,
        outer_margin: int = None,
    ) -> Image.Image:
        stickers_w, stickers_h = metadata["sticker_grid"]
        num_cubes_w, num_cubes_h = metadata["num_cubes"]
        n = metadata.get("stickers_per_cube", 3)          # 3 for 3x3, 4 for 4x4, etc.

        sticker_size = stickers_w // (num_cubes_w * n)

        # Use defaults or overrides
        pad_sticker = sticker_padding if sticker_padding is not None else self.default_sticker_padding
        pad_cube    = cube_padding    if cube_padding    is not None else self.default_cube_padding
        pad_color   = padding_color   if padding_color   is not None else self.default_padding_color
        pad_outer   = outer_margin    if outer_margin    is not None else self.default_outer_margin

        # Size of one full cube block (including sticker padding)
        block_w = n * sticker_size + (n - 1) * pad_sticker
        block_h = n * sticker_size + (n - 1) * pad_sticker

        # EXACT canvas size (no excess space!)
        total_w = num_cubes_w * block_w + (num_cubes_w - 1) * pad_cube + 2 * pad_outer
        total_h = num_cubes_h * block_h + (num_cubes_h - 1) * pad_cube + 2 * pad_outer

        final_img = Image.new("RGB", (total_w, total_h), color=background_color)
        draw = ImageDraw.Draw(final_img)

        filled = 0
        y = pad_outer

        for cube_r in range(num_cubes_h):
            x = pad_outer
            if cube_r > 0:
                y += pad_cube

            for cube_c in range(num_cubes_w):
                cube = colored_mosaic[cube_r][cube_c]
                if cube_c > 0:
                    x += pad_cube

                for sr in range(n):
                    for sc in range(n):
                        sticker = cube["stickers"][sr][sc]
                        color = sticker.get("assigned_color", (200, 200, 200))

                        sx = x + sc * (sticker_size + pad_sticker) + pad_sticker
                        sy = y + sr * (sticker_size + pad_sticker) + pad_sticker

                        draw.rectangle([sx, sy, sx + sticker_size, sy + sticker_size], fill=color)
                        filled += 1

                x += block_w

            y += block_h

        print(f"Blueprint created: {total_w}×{total_h} px | {num_cubes_w}×{num_cubes_h} cubes")
        return final_img
