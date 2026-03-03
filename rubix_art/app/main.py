# main.py
"""
Rubik's Cube Artwork Generator - GUI
Connects to the ImageMaker pipeline.
"""

import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
from PIL import Image, ImageTk
from src.image_maker import ImageMaker          # adjust if needed (e.g. from image_maker import ...)
import os
# import webbrowser                             # uncomment if you want to auto-open result


class RubiksArtworkApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Rubik's Cube Artwork Generator")
        self.root.geometry("880x720")
        self.root.resizable(True, True)
        self.root.configure(bg="#f0f0f0")

        # ── Style ─────────────────────────────────────────────────────────────
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TLabel",       background="#f0f0f0", font=("Segoe UI", 10))
        style.configure("TButton",      font=("Segoe UI", 10, "bold"))
        style.configure("Header.TLabel", font=("Segoe UI", 14, "bold"))
        style.map("TButton", background=[("active", "#d0e0ff")])

        # ── Variables ─────────────────────────────────────────────────────────
        self.image_path = tk.StringVar(value="No image selected")
        self.full_image_path = ""                   # full path kept here
        self.preview_photo = None                   # prevents GC of preview image

        self.desired_large_dim_m = tk.DoubleVar(value=2.0)
        self.cube_edge_m = tk.DoubleVar(value=0.056)  # ≈5.6 cm – standard 3×3
        self.cube_type_var = tk.StringVar(value="3x3")

        # ── Layout ────────────────────────────────────────────────────────────
        main_frame = ttk.Frame(root, padding="20 20 20 20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="Rubik's Cube Mosaic Creator", style="Header.TLabel").pack(pady=(0, 15))

        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 20))

        self._build_input_section(left_frame)

        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self._build_preview_section(right_frame)

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=20)

        ttk.Button(btn_frame, text="Select Image", command=self.select_image).pack(side=tk.LEFT, padx=10)

        self.process_btn = ttk.Button(btn_frame, text="Generate Blueprint",
                                      command=self.start_processing, state="disabled")
        self.process_btn.pack(side=tk.LEFT, padx=10)

        ttk.Button(btn_frame, text="Quit", command=root.quit).pack(side=tk.RIGHT, padx=10)

    def _build_input_section(self, parent):
        inputs = ttk.LabelFrame(parent, text=" Configuration ", padding=15)
        inputs.pack(fill=tk.X, pady=10)

        row = 0
        ttk.Label(inputs, text="Largest side (meters):").grid(row=row, column=0, sticky="w", pady=6)
        ttk.Entry(inputs, textvariable=self.desired_large_dim_m, width=12).grid(row=row, column=1, sticky="w")
        row += 1

        ttk.Label(inputs, text="Cube type:").grid(row=row, column=0, sticky="w", pady=6)
        cube_types = ["2x2", "3x3", "4x4", "5x5", "6x6", "7x7"]
        ttk.Combobox(inputs, textvariable=self.cube_type_var, values=cube_types,
                     state="readonly", width=10).grid(row=row, column=1, sticky="w")
        row += 1

        ttk.Label(inputs, text="Cube edge length (m):").grid(row=row, column=0, sticky="w", pady=6)
        ttk.Entry(inputs, textvariable=self.cube_edge_m, width=12).grid(row=row, column=1, sticky="w")
        ttk.Label(inputs, text="(e.g. 0.056 for standard 3×3, often 0.060–0.065 for bigger cubes)").grid(
            row=row, column=2, sticky="w", padx=8)
        row += 1

        ttk.Label(inputs, text="Sticker grid:").grid(row=row, column=0, sticky="w", pady=6)
        ttk.Label(inputs, text="auto (n×n per cube)").grid(row=row, column=1, columnspan=2, sticky="w")

        self.status_var = tk.StringVar(value="Ready. Please select an image.")
        ttk.Label(inputs, textvariable=self.status_var, foreground="gray", wraplength=320).grid(
            row=row+1, column=0, columnspan=3, pady=12, sticky="w")

    def _build_preview_section(self, parent):
        preview_frame = ttk.LabelFrame(parent, text=" Original Image Preview ", padding=10)
        preview_frame.pack(fill=tk.BOTH, expand=True)

        self.preview_label = ttk.Label(preview_frame,
                                       text="No image loaded\n\nSelect an image to begin",
                                       foreground="gray", justify="center")
        self.preview_label.pack(expand=True)

        ttk.Label(preview_frame, textvariable=self.image_path, wraplength=380,
                  foreground="#555").pack(pady=8, fill=tk.X)

    def select_image(self):
        file_path = filedialog.askopenfilename(
            title="Select Input Image",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.tiff"), ("All files", "*.*")]
        )
        if not file_path:
            return

        try:
            img = Image.open(file_path)
            img.thumbnail((380, 380), Image.Resampling.LANCZOS)
            self.preview_photo = ImageTk.PhotoImage(img)       # keep ref → no GC

            self.preview_label.configure(image=self.preview_photo, text="")
            self.image_path.set(os.path.basename(file_path))
            self.full_image_path = file_path

            self.process_btn.config(state="normal")
            self.status_var.set("Image loaded. Adjust parameters then click Generate.")

        except Exception as e:
            messagebox.showerror("Error", f"Cannot load image:\n{e}")
            self.status_var.set("Failed to load image.")

    def start_processing(self):
        if not self.full_image_path:
            messagebox.showwarning("No Image", "Please select an image first.")
            return

        try:
            large_m = self.desired_large_dim_m.get()
            edge_m  = self.cube_edge_m.get()
            n_str   = self.cube_type_var.get()
            n       = int(n_str.split("x")[0])

            if large_m <= 0 or edge_m <= 0 or n < 2:
                raise ValueError("Dimensions must be positive and cube n ≥ 2")

            self.status_var.set("Processing... please wait (may take a while)")

            # ── Run pipeline ──────────────────────────────────────────────────
            maker = ImageMaker(self.full_image_path)
            output_path = maker.make(
                large_side_meters   = large_m,
                cube_edge_meters    = edge_m,
                cube_n              = n,
                # show_preview     = True,             # useful during dev
                # output_path      = None,             # auto = original_name_rubiks_blueprint.png
            )

            msg = f"Blueprint generated!\n\nSaved to:\n{output_path}"
            messagebox.showinfo("Success", msg)
            self.status_var.set(f"Done – {output_path.name}")

            # Optional: auto open result (uncomment if desired)
            # webbrowser.open(f"file://{output_path}")

        except ValueError as ve:
            messagebox.showerror("Input Error", str(ve))
            self.status_var.set("Invalid input values")
        except Exception as e:
            messagebox.showerror("Processing Error", f"Failed to generate blueprint:\n{str(e)}")
            self.status_var.set("Error during generation")
        finally:
            self.process_btn.config(state="normal")  # always re-enable


if __name__ == "__main__":
    root = tk.Tk()
    app = RubiksArtworkApp(root)
    root.mainloop()