import tkinter as tk
from tkinter import filedialog, colorchooser, messagebox
from tkinter import ttk
import os
from pathlib import Path
import io
import math

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

class WatermarkApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Watermarker")
        self.root.geometry("400x340") # Small, concise window
        self.root.resizable(False, False)
        self.root.configure(bg="#ffffff") # Modern white background

        # Set up modern styling
        self.setup_styles()

        # Variables
        self.pdf_path = tk.StringVar()
        self.watermark_text = tk.StringVar()
        self.watermark_color = tk.StringVar(value="#000000") # Default black
        self.opacity = tk.IntVar(value=50) # Default 50%

        self.create_widgets()

    def setup_styles(self):
        style = ttk.Style()
        # Use 'clam' as a base because it is flat and easily customizable
        style.theme_use('clam') 
        
        # General styling
        style.configure('.', background='#ffffff', foreground='#1f2937', font=('Segoe UI', 10))
        
        # Labels
        style.configure('TLabel', background='#ffffff')
        style.configure('Header.TLabel', font=('Segoe UI', 16, 'bold'), foreground='#111827')
        style.configure('Sub.TLabel', font=('Segoe UI', 9), foreground='#6b7280')
        
        # Buttons
        style.configure('TButton', font=('Segoe UI', 10), padding=5, focuscolor='', borderwidth=1, bordercolor='#d1d5db', lightcolor='#f3f4f6', darkcolor='#f3f4f6')
        style.map('TButton', background=[('active', '#e5e7eb')])
        
        # Primary Action Button
        style.configure('Primary.TButton', font=('Segoe UI', 10, 'bold'), background='#2563eb', foreground='#ffffff', bordercolor='#1d4ed8')
        style.map('Primary.TButton', background=[('active', '#1d4ed8')])

        # Entry and Scale
        style.configure('TEntry', padding=5, borderwidth=1)
        style.configure('TScale', background='#ffffff', troughcolor='#e5e7eb')

    def create_widgets(self):
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill='both', expand=True)

        # Header
        ttk.Label(main_frame, text="Watermark Setup", style='Header.TLabel').grid(row=0, column=0, columnspan=2, sticky='w', pady=(0, 15))

        # 1. Select PDF File
        ttk.Label(main_frame, text="Target File:").grid(row=1, column=0, sticky='w', pady=5)
        
        file_frame = ttk.Frame(main_frame)
        file_frame.grid(row=1, column=1, sticky='we', pady=5)
        
        ttk.Button(file_frame, text="Browse...", command=self.select_file, width=10).pack(side='right', padx=(5, 0))
        self.lbl_file = ttk.Label(file_frame, text="No file selected...", style='Sub.TLabel')
        self.lbl_file.pack(side='right', fill='x', expand=True)

        # 2. Watermark Input
        ttk.Label(main_frame, text="Watermark Text:").grid(row=2, column=0, sticky='w', pady=10)
        ttk.Entry(main_frame, textvariable=self.watermark_text).grid(row=2, column=1, sticky='we', pady=10)

        # 3. Color Picker
        ttk.Label(main_frame, text="Text Color:").grid(row=3, column=0, sticky='w', pady=5)
        
        color_frame = ttk.Frame(main_frame)
        color_frame.grid(row=3, column=1, sticky='w', pady=5)
        
        # Using standard tk.Button here because ttk.Button doesn't support direct bg color overriding easily
        self.btn_color = tk.Button(color_frame, bg=self.watermark_color.get(), width=4, height=1, relief="flat", borderwidth=1, command=self.pick_color, cursor="hand2")
        self.btn_color.pack(side='left')
        self.lbl_color_hex = ttk.Label(color_frame, text=self.watermark_color.get(), style='Sub.TLabel')
        self.lbl_color_hex.pack(side='left', padx=(10, 0))

        # 4. Opacity Slider
        ttk.Label(main_frame, text="Opacity:").grid(row=4, column=0, sticky='w', pady=10)
        
        opacity_frame = ttk.Frame(main_frame)
        opacity_frame.grid(row=4, column=1, sticky='we', pady=10)
        
        ttk.Scale(opacity_frame, from_=0, to=100, orient='horizontal', variable=self.opacity).pack(side='left', fill='x', expand=True)
        ttk.Label(opacity_frame, textvariable=self.opacity, width=4, anchor='e').pack(side='right', padx=(5, 0))

        # Grid column configuration for responsiveness
        main_frame.columnconfigure(1, weight=1)

        # Submit Button
        ttk.Button(main_frame, text="Generate Watermarked PDF", style='Primary.TButton', command=self.process_pdf).grid(row=5, column=0, columnspan=2, sticky='we', pady=(20, 0))

    def select_file(self):
        filepath = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if filepath:
            self.pdf_path.set(filepath)
            # Truncate long filenames to keep UI clean
            filename = Path(filepath).name
            display_name = (filename[:25] + '...') if len(filename) > 28 else filename
            self.lbl_file.config(text=display_name, style='TLabel')

    def pick_color(self):
        color_code = colorchooser.askcolor(title="Choose Watermark Color")
        if color_code[1]: 
            self.watermark_color.set(color_code[1])
            self.btn_color.config(bg=color_code[1])
            self.lbl_color_hex.config(text=color_code[1])

    def find_thai_font(self):
        """Automatically hunts for reliable Thai fonts on Windows."""
        windows_font_dir = r"C:\Windows\Fonts"
        
        reliable_thai_fonts = [
            ("Tahoma", "tahoma.ttf"),
            ("LeelawadeeUI", "LeelawUI.ttf"),
            ("AngsanaNew", "angsa.ttf"),
            ("CordiaNew", "cordia.ttf")
        ]

        for font_name, font_file in reliable_thai_fonts:
            full_path = os.path.join(windows_font_dir, font_file)
            if os.path.exists(full_path):
                return font_name, full_path
                
        return None, None

    def create_watermark_page(self, text, color_hex, opacity, width, height, font_name):
        """Generates a single PDF page with dynamic text scaling."""
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=(width, height))

        can.setFillColor(HexColor(color_hex))
        can.setFillAlpha(opacity / 100.0)

        # --- DYNAMIC FONT SCALING LOGIC ---
        max_font_size = 80 
        page_diagonal = math.sqrt(width**2 + height**2)
        max_allowed_width = page_diagonal * 0.8 

        test_size = 100
        test_width = pdfmetrics.stringWidth(text, font_name, test_size)

        if test_width > 0:
            optimal_size = int((max_allowed_width / test_width) * test_size)
            final_font_size = min(max_font_size, optimal_size)
        else:
            final_font_size = max_font_size

        can.setFont(font_name, final_font_size)

        # --- DRAWING ---
        can.translate(width / 2, height / 2)
        can.rotate(45)
        can.drawCentredString(0, 0, text)

        can.save()
        packet.seek(0)
        return packet

    def process_pdf(self):
        input_path = self.pdf_path.get()
        text = self.watermark_text.get()

        if not input_path:
            messagebox.showwarning("Missing Information", "Please browse and select a PDF file first.")
            return
        if not text:
            messagebox.showwarning("Missing Information", "Please enter the text you want to use as a watermark.")
            return

        # Handle Fonts
        font_name, font_path = self.find_thai_font()
        
        if font_name and font_path:
            try:
                pdfmetrics.registerFont(TTFont(font_name, font_path))
            except Exception as e:
                messagebox.showerror("Font Error", f"Found font {font_name} but failed to load it.\n{e}")
                return
        else:
            messagebox.showerror(
                "System Error", 
                "Could not find standard system fonts required to process international text properly."
            )
            return

        try:
            reader = PdfReader(input_path)
            writer = PdfWriter()

            for page in reader.pages:
                page_width = float(page.mediabox.width)
                page_height = float(page.mediabox.height)

                watermark_packet = self.create_watermark_page(
                    text, 
                    self.watermark_color.get(), 
                    self.opacity.get(), 
                    page_width, 
                    page_height,
                    font_name
                )
                
                watermark_reader = PdfReader(watermark_packet)
                watermark_page = watermark_reader.pages[0]

                page.merge_page(watermark_page)
                writer.add_page(page)

            downloads_folder = str(Path.home() / "Downloads")
            original_filename = Path(input_path).stem
            output_filename = f"{original_filename}-watermark.pdf"
            output_path = os.path.join(downloads_folder, output_filename)

            with open(output_path, "wb") as output_file:
                writer.write(output_file)

            messagebox.showinfo("Success!", f"Your watermarked file is ready!\n\nSaved to: {output_path}")

        except Exception as e:
            messagebox.showerror("Processing Error", f"An unexpected error occurred:\n{str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = WatermarkApp(root)
    root.mainloop()