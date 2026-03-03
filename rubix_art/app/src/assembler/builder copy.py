# src/assembler/builder.py
"""
Builder – Reassembles the colored mosaic structure into a final blueprint image.

Creates a large image where each sticker is a solid-colored rectangle,
and optionally draws grid lines to show cube and sticker boundaries.
"""

from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from PIL import Image, ImageDraw


class Builder:
    """
    Reconstructs the final blueprint from the colored mosaic data.

    Main method:
        .build(colored_mosaic, metadata, draw_grid_lines=True, ...)
    """

    def __init__(self):
        # Default visual style – can be overridden via parameters
        self.default_grid_color = (40, 40, 40)      # dark gray
        self.default_grid_width_cube = 1            # thicker lines between cubes
        self.default_grid_width_sticker = 1         # thin lines between stickers

    def build(
        self,
        colored_mosaic: List[List[Dict]],
        metadata: Dict[str, Any],
        draw_grid_lines: bool = True,
        grid_color: Tuple[int, int, int] = None,
        grid_width_cube: Optional[int] = None,
        grid_width_sticker: Optional[int] = None,
        background_color: Tuple[int, int, int] = (255, 255, 255),
    ) -> Image.Image:
        """
        Creates the final blueprint image.

        Args:
            colored_mosaic:     Nested structure from Painter (with assigned_color)
            metadata:           From Scaler – must contain 'sticker_grid'
            draw_grid_lines:    Whether to draw cube/sticker borders
            grid_color:         RGB tuple for grid lines (default: dark gray)
            grid_width_cube:    Thickness of lines between cubes
            grid_width_sticker: Thickness of lines between stickers inside a cube
            background_color:   Color of any potential padding (usually white)

        Returns:
            PIL.Image – the complete blueprint
        """
        # ── Extract dimensions from metadata ─────────────────────────────────
        stickers_w, stickers_h = metadata["sticker_grid"]
        sticker_px_size = metadata.get("sticker_size_px") or (
            stickers_w // metadata["num_cubes"][0]
        )

        # ── Create blank canvas ───────────────────────────────────────────────
        final_img = Image.new(
            "RGB",
            (stickers_w, stickers_h),
            color=background_color
        )
        draw = ImageDraw.Draw(final_img)

        # Use provided or default grid styles
        grid_color = grid_color or self.default_grid_color
        gw_cube = grid_width_cube or self.default_grid_width_cube
        gw_sticker = grid_width_sticker or self.default_grid_width_sticker

        # ── Fill each sticker with its assigned color ────────────────────────
        for cube_row in colored_mosaic:
            for cube in cube_row:
                for sticker_row in cube["stickers"]:
                    for sticker in sticker_row:
                        color = sticker.get("assigned_color")
                        if color is None:
                            # Fallback if something went wrong upstream
                            color = (200, 200, 200)  # light gray warning color

                        # Get pixel coordinates
                        x1, y1, x2, y2 = sticker["pixel_region"]

                        # Fill rectangle with solid color
                        draw.rectangle(
                            [x1, y1, x2-1, y2-1],   # -1 to avoid overlapping lines
                            fill=color
                        )

        # ── Optional: draw grid lines ─────────────────────────────────────────
        if draw_grid_lines:
            # Vertical lines
            for col in range(metadata["num_cubes"][0] + 1):
                x = col * (stickers_w // metadata["num_cubes"][0])
                is_cube_boundary = (col % metadata["stickers_per_cube"] == 0)
                width = gw_cube if is_cube_boundary else gw_sticker
                draw.line(
                    [(x, 0), (x, stickers_h)],
                    fill=grid_color,
                    width=width
                )

            # Horizontal lines
            for row in range(metadata["num_cubes"][1] + 1):
                y = row * (stickers_h // metadata["num_cubes"][1])
                is_cube_boundary = (row % metadata["stickers_per_cube"] == 0)
                width = gw_cube if is_cube_boundary else gw_sticker
                draw.line(
                    [(0, y), (stickers_w, y)],
                    fill=grid_color,
                    width=width
                )

        print(f"Blueprint assembled: {stickers_w}×{stickers_h} pixels")
        if draw_grid_lines:
            print(f"Grid lines added (cube: {gw_cube}px, sticker: {gw_sticker}px)")

        return final_img


# ── Quick standalone test ─────────────────────────────────────────────────────
if __name__ == "__main__":
    # Minimal dummy data to test rendering
    dummy_sticker = {
        "pixel_region": (0, 0, 50, 50),
        "assigned_color": (255, 0, 0)
    }
    dummy_cube = {"stickers": [[dummy_sticker]]}
    dummy_mosaic = [[dummy_cube]]

    dummy_metadata = {
        "sticker_grid": (50, 50),
        "num_cubes": (1, 1),
        "stickers_per_cube": 1
    }

    builder = Builder()
    img = builder.build(
        colored_mosaic=dummy_mosaic,
        metadata=dummy_metadata,
        draw_grid_lines=True,
        grid_color=(0, 0, 0),
        grid_width_cube=6,
        grid_width_sticker=2
    )

    img.show(title="Builder Test – Single Red Sticker with Grid")