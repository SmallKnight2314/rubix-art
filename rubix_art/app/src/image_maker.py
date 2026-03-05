# src/image_maker.py
"""
Central orchestrator for the Rubik's cube mosaic / blueprint generator.
Coordinates the pipeline: Scaler → Splitter → Painter → Builder.
"""

from pathlib import Path
from typing import Optional, Union, Dict, Tuple

from PIL import Image

# Import classes from their respective submodules
from src.scaling.scaler import Scaler
from src.splitter.splitter import Splitter
from src.coloring.painter import Painter
from src.assembler.builder import Builder


class ImageMaker:
    """
    Main coordinator class.
    Create with image path, then call .make(...) with configuration.
    """

    def __init__(
        self,
        image_path: Union[str, Path],
        scaler_class=Scaler,
        splitter_class=Splitter,
        painter_class=Painter,
        builder_class=Builder,
    ):
        self.image_path = Path(image_path).resolve()
        if not self.image_path.is_file():
            raise FileNotFoundError(f"Image not found: {self.image_path}")

        self.scaler_class   = scaler_class
        self.splitter_class = splitter_class
        self.painter_class  = painter_class
        self.builder_class  = builder_class

        self.scaled_image: Optional[Image.Image] = None
        self.metadata: Optional[Dict] = None

    def make(
        self,
        max_width_meters: float,          # ← renamed
        max_height_meters: float,         # ← new
        cube_edge_meters: float,
        cube_n: int,
        output_path: Optional[Union[str, Path]] = None,
        palette: Optional[list[tuple[int,int,int]]] = None,
        show_preview: bool = False,
        draw_grid_lines: bool = True,
        ) -> Path:
        if max_width_meters <= 0 or max_height_meters <= 0 or cube_edge_meters <= 0 or cube_n < 2:
            raise ValueError("Invalid dimensions")

        print(f"Starting – max space {max_width_meters:.2f}×{max_height_meters:.2f} m | {cube_n}×{cube_n} cubes")

        # Load original high-res once
        original_image = Image.open(self.image_path).convert("RGB")

        # Scale (now uses max w/h)
        scaler = self.scaler_class(
            max_width_meters=max_width_meters,
            max_height_meters=max_height_meters,
            cube_edge_meters=cube_edge_meters,
            cube_n=cube_n,
        )
        self.scaled_image, self.metadata = scaler.scale(self.image_path)

        w, h = self.scaled_image.size
        cw, ch = self.metadata["num_cubes"]
        print(f"Grid: {cw}×{ch} cubes → {w}×{h} stickers | physical ≈ {self.metadata['physical_size_m']['width']:.2f}×{self.metadata['physical_size_m']['height']:.2f} m")

        # Split
        splitter = self.splitter_class(cube_n=cube_n)
        mosaic_structure = splitter.split(self.scaled_image, self.metadata)

        # Paint – now with original + metadata
        #swaps = {"Blue": "Green", "Green": "Blue"}, {"Green": "White", "White": "Green"},
        swaps = False

        painter = self.painter_class(palette=None, color_swaps=swaps)
        colored_mosaic = painter.paint(
            mosaic_structure=mosaic_structure,
            original_image=original_image,
            metadata=self.metadata
        )

        # Build & save (unchanged)
        builder = self.builder_class()
        final_image = builder.build(
            colored_mosaic=colored_mosaic,
            metadata=self.metadata,
            sticker_padding=2,      # thin dark border around each sticker
            cube_padding=6,         # thicker border around each full cube
            padding_color=(40, 40, 40),  # dark grey
            background_color=(5, 5, 5)
        )

        if output_path is None:
            output_path = self.image_path.with_stem(self.image_path.stem + "_rubiks_blueprint").with_suffix(".png")
        else:
            output_path = Path(output_path)

        final_image.save(output_path)
        print(f"Saved: {output_path}")

        if show_preview:
            final_image.show(title="Rubik's Blueprint")

        return output_path


# ── Quick test / demo ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    try:
        maker = ImageMaker("example/portrait.jpg")  # ← replace with real path
        result_path = maker.make(
            large_side_meters=2.0,
            cube_edge_meters=0.056,
            cube_n=3,
            show_preview=True,
            # Example: very clean look (recommended for small mosaics)
            grid_width_cube=2,
            grid_width_sticker=0,
            grid_color=(200, 200, 200),
        )
        print("Done. Output:", result_path)
    except Exception as e:
        print("Error during test run:", e)
