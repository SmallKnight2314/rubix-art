# src/image_maker.py
"""
Central orchestrator for the Rubik's cube mosaic / blueprint generator.
Coordinates the pipeline: Scaler → Splitter → Painter → Builder.
"""

from pathlib import Path
from typing import Optional, Union, Tuple, Dict

from PIL import Image

# Import classes from their respective submodules
from src.scaling.scaler import Scaler
from src.splitter.splitter import Splitter      # adjust filename if different
from src.coloring.painter import Painter        # adjust filename if different
from src.assembler.builder import Builder       # adjust filename if different


class ImageMaker:
    """
    Main coordinator class.
    Create with image path, then call .make(...) with configuration.

    Example:
        maker = ImageMaker("photos/portrait.jpg")
        output = maker.make(large_side_meters=2.4, cube_edge_meters=0.056, cube_n=3)
    """

    def __init__(
        self,
        image_path: Union[str, Path],
        # Dependency injection – mostly for testing/mocking
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

        # Will be filled during .make()
        self.scaled_image: Optional[Image.Image] = None
        self.metadata: Optional[Dict] = None

    def make(
        self,
        large_side_meters: float,
        cube_edge_meters: float,
        cube_n: int,
        output_path: Optional[Union[str, Path]] = None,
        palette: Optional[list[tuple[int, int, int]]] = None,
        show_preview: bool = False,
        draw_grid_lines: bool = True,
    ) -> Path:
        """
        Execute the full generation pipeline.

        Returns:
            Path to the saved blueprint image
        """
        if large_side_meters <= 0 or cube_edge_meters <= 0 or cube_n < 2:
            raise ValueError("Invalid physical dimensions or cube size")

        print(f"Starting mosaic generation for: {self.image_path.name}")
        print(f"Target: {large_side_meters:.2f} m long side | {cube_n}×{cube_n} cubes")

        # ── 1. Scale image to sticker-perfect resolution ──────────────────────
        scaler = self.scaler_class(
            large_side_meters=large_side_meters,
            cube_edge_meters=cube_edge_meters,
            cube_n=cube_n,
        )
        self.scaled_image, self.metadata = scaler.scale(self.image_path)

        w, h = self.scaled_image.size
        cw, ch = self.metadata["num_cubes"]
        print(f"Scaled to {w}×{h} px  →  {cw}×{ch} cubes  "
              f"({cw*cube_n}×{ch*cube_n} stickers)")

        # ── 2. Split into nested structure (cubes → faces → stickers) ─────────
        splitter = self.splitter_class(cube_n=cube_n)
        mosaic_structure = splitter.split(
            self.scaled_image,
            self.metadata
        )

        # ── 3. Assign closest Rubik's color to each sticker region ────────────
        painter = self.painter_class(palette=palette)  # None = default palette
        colored_mosaic = painter.paint(mosaic_structure)

        # ── 4. Reassemble into final blueprint image ──────────────────────────
        builder = self.builder_class()
        final_image = builder.build(
            colored_mosaic=colored_mosaic,
            metadata=self.metadata,
            draw_grid_lines=draw_grid_lines,
            # You can add more builder options later (grid color, thickness, etc.)
        )

        # ── 5. Determine output path & save ───────────────────────────────────
        if output_path is None:
            output_path = self.image_path.with_stem(
                self.image_path.stem + "_rubiks_blueprint"
            ).with_suffix(".png")
        else:
            output_path = Path(output_path)

        final_image.save(output_path, "PNG")
        print(f"Blueprint saved: {output_path}")

        if show_preview:
            try:
                final_image.show(title="Generated Rubik's Blueprint")
            except Exception as e:
                print(f"Could not open preview: {e}")

        return output_path


# ── Quick test / demo when running the file directly ────────────────────────────
if __name__ == "__main__":
    try:
        maker = ImageMaker("example/portrait.jpg")
        result_path = maker.make(
            large_side_meters=2.0,
            cube_edge_meters=0.056,
            cube_n=3,
            show_preview=True,
        )
        print("Done. Output:", result_path)
    except Exception as e:
        print("Error during test run:", e)