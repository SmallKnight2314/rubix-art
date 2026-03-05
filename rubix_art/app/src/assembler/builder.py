# src/assembler/builder.py
"""
Builder – Creates a blueprint where:
- Each sticker has thin dark padding around it (like cube plastic edges)
- Each full cube (3×3 / 4×4 / … block) has thicker padding around it
No lines drawn on top → all separation comes from padding (natural look)
"""

from typing import List, Dict, Any, Optional, Tuple
from PIL import Image, ImageDraw


class Builder:
    def __init__(self):
        self.default_background = (255, 255, 255)
        self.default_sticker_padding = 2          # thin padding around each sticker
        self.default_cube_padding    = 6          # thicker padding around whole cube
        self.default_padding_color   = (40, 40, 40)  # dark grey

    def build(
        self,
        colored_mosaic: List[List[Dict]],
        metadata: Dict[str, Any],
        background_color: Tuple[int, int, int] = None,
        
        # Padding controls
        sticker_padding: int = None,
        cube_padding: int = None,
        padding_color: Tuple[int, int, int] = None,
    ) -> Image.Image:
        stickers_w, stickers_h = metadata["sticker_grid"]
        num_cubes_w, num_cubes_h = metadata["num_cubes"]
        n = metadata.get("stickers_per_cube", 3)

        sticker_size = stickers_w // (num_cubes_w * n)
        if sticker_size * num_cubes_w * n != stickers_w or sticker_size * num_cubes_h * n != stickers_h:
            raise ValueError("Sticker grid not divisible by cubes")

        # Use defaults or overrides
        bg_color       = background_color or self.default_background
        pad_sticker    = sticker_padding if sticker_padding is not None else self.default_sticker_padding
        pad_cube       = cube_padding    if cube_padding    is not None else self.default_cube_padding
        pad_color      = padding_color   if padding_color   is not None else self.default_padding_color

        # ── Calculate total canvas size with padding ─────────────────────────
        total_sticker_pad_w = (num_cubes_w * n - 1) * pad_sticker + num_cubes_w * pad_cube * 2
        total_sticker_pad_h = (num_cubes_h * n - 1) * pad_sticker + num_cubes_h * pad_cube * 2

        canvas_w = stickers_w + total_sticker_pad_w + pad_cube * 2   # extra outer padding
        canvas_h = stickers_h + total_sticker_pad_h + pad_cube * 2

        final_img = Image.new("RGB", (canvas_w, canvas_h), color=bg_color)
        draw = ImageDraw.Draw(final_img)

        # ── Place each sticker with padding ──────────────────────────────────
        filled = 0
        current_y = pad_cube  # start with outer cube padding

        for cube_r in range(num_cubes_h):
            current_x = pad_cube

            # Add cube padding between cube rows (except first)
            if cube_r > 0:
                current_y += pad_cube

            for cube_c in range(num_cubes_w):
                cube = colored_mosaic[cube_r][cube_c]

                # Add cube padding between cubes horizontally (except first)
                if cube_c > 0:
                    current_x += pad_cube

                for sr in range(n):
                    for sc in range(n):
                        sticker = cube["stickers"][sr][sc]
                        color = sticker.get("assigned_color", (200, 200, 200))

                        # Position with both sticker and cube padding
                        x1 = current_x + sc * (sticker_size + pad_sticker) + pad_sticker
                        y1 = current_y + sr * (sticker_size + pad_sticker) + pad_sticker
                        x2 = x1 + sticker_size
                        y2 = y1 + sticker_size

                        draw.rectangle([x1, y1, x2, y2], fill=color)
                        filled += 1

                # Move to next cube horizontally
                current_x += n * sticker_size + (n - 1) * pad_sticker

            # Move to next cube row
            current_y += n * sticker_size + (n - 1) * pad_sticker

        print(f"Filled {filled} stickers with "
              f"sticker padding={pad_sticker}px and cube padding={pad_cube}px")

        return final_img
