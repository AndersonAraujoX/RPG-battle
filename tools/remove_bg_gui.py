import os
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageFilter, ImageChops, ImageMath, ImageDraw
import io
from image_processor import process_image, detect_background_color

class BackgroundRemovalApp:
    def __init__(self, root):
        self.root = root
        self.root.title("RPG Battle - Removedor de Fundo & Halo")
        self.root.geometry("1200x650")
        self.root.configure(bg="#1a1a1a")
        
        # Style variables
        self.bg_dark = "#1a1a1a"
        self.bg_panel = "#121212"
        self.fg_light = "#e0e0e0"
        self.accent_color = "#8a2be2" # Purple from config.py
        self.accent_active = "#a040f0"
        
        # State variables
        self.image_path = None
        self.original_image = None  # Full res PIL Image
        self.preview_original = None # Downscaled original PIL Image
        self.preview_processed = None # Downscaled processed PIL Image
        self.photo_original = None # Tkinter PhotoImage for left canvas
        self.photo_processed = None # Tkinter PhotoImage for right canvas
        
        # Image dimensions info
        self.original_size = (0, 0)
        
        # UI controls variables
        self.bg_type_var = tk.StringVar(value="auto")
        self.mode_var = tk.StringVar(value="floodfill")
        self.preview_bg_var = tk.StringVar(value="checker")
        
        self.tolerance_var = tk.IntVar(value=30)
        self.erode_var = tk.IntVar(value=1)
        self.feather_var = tk.DoubleVar(value=1.0)
        self.defringe_var = tk.IntVar(value=3)
        
        # Default load directory
        self.default_dir = "/home/anderson/Documents/projeto/RPG-battle/assets/images/characters/animation"
        
        # Build UI
        self.create_widgets()
        
        # Try to load the first image by default if it exists
        self.load_default_image()

    def create_widgets(self):
        # 1. Header Frame
        header = tk.Frame(self.root, bg=self.bg_panel, height=60, bd=1, relief=tk.FLAT)
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)
        
        title_label = tk.Label(
            header, 
            text="Removedor de Fundo & Halo (Assets de Animação)", 
            font=("Helvetica", 14, "bold"), 
            bg=self.bg_panel, 
            fg=self.fg_light
        )
        title_label.pack(side=tk.LEFT, padx=15, pady=15)
        
        self.file_label = tk.Label(
            header, 
            text="Nenhum arquivo carregado", 
            font=("Helvetica", 10, "italic"), 
            bg=self.bg_panel, 
            fg="#888888"
        )
        self.file_label.pack(side=tk.LEFT, padx=20, pady=18)
        
        # 2. Main Area Split Frame
        main_frame = tk.Frame(self.root, bg=self.bg_dark)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left Side: Previews Frame
        previews_frame = tk.Frame(main_frame, bg=self.bg_dark)
        previews_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Canvas Original
        orig_frame = tk.Frame(previews_frame, bg=self.bg_dark)
        orig_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        tk.Label(orig_frame, text="Imagem Original", font=("Helvetica", 11, "bold"), bg=self.bg_dark, fg=self.fg_light).pack(pady=5)
        self.canvas_orig = tk.Canvas(orig_frame, bg="#111111", highlightbackground=self.bg_panel, highlightthickness=2)
        self.canvas_orig.pack(fill=tk.BOTH, expand=True)
        
        # Canvas Processed
        proc_frame = tk.Frame(previews_frame, bg=self.bg_dark)
        proc_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        tk.Label(proc_frame, text="Visualização (Sem Fundo / Sem Halo)", font=("Helvetica", 11, "bold"), bg=self.bg_dark, fg=self.fg_light).pack(pady=5)
        self.canvas_proc = tk.Canvas(proc_frame, bg="#111111", highlightbackground=self.bg_panel, highlightthickness=2)
        self.canvas_proc.pack(fill=tk.BOTH, expand=True)
        
        # Right Side: Control Panel Frame
        control_panel = tk.Frame(main_frame, bg=self.bg_panel, width=340, bd=0)
        control_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        control_panel.pack_propagate(False)
        
        # Scrollable Control Content
        scroll_container = tk.LabelFrame(control_panel, text=" PARÂMETROS ", font=("Helvetica", 10, "bold"), bg=self.bg_panel, fg=self.fg_light, bd=1)
        scroll_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # File Loader Buttons
        load_btn = tk.Button(
            scroll_container, 
            text="Carregar Outra Imagem...", 
            command=self.choose_image,
            bg=self.bg_dark, 
            fg=self.fg_light, 
            activebackground=self.accent_color,
            activeforeground="white",
            relief=tk.FLAT, 
            bd=0, 
            height=2, 
            font=("Helvetica", 9, "bold")
        )
        load_btn.pack(fill=tk.X, padx=10, pady=10)
        
        # --- Background Selection ---
        group_bg = tk.LabelFrame(scroll_container, text="Fundo Original", bg=self.bg_panel, fg="#bbbbbb", bd=0)
        group_bg.pack(fill=tk.X, padx=10, pady=5)
        
        for text, val in [("Auto (Detectar)", "auto"), ("Branco", "white"), ("Preto", "black")]:
            r = tk.Radiobutton(
                group_bg, 
                text=text, 
                value=val, 
                variable=self.bg_type_var, 
                command=self.update_preview,
                bg=self.bg_panel, 
                fg=self.fg_light, 
                selectcolor=self.bg_dark, 
                activebackground=self.bg_panel,
                activeforeground=self.fg_light
            )
            r.pack(anchor=tk.W, padx=10)
            
        # --- Mode Selection ---
        group_mode = tk.LabelFrame(scroll_container, text="Modo de Remoção", bg=self.bg_panel, fg="#bbbbbb", bd=0)
        group_mode.pack(fill=tk.X, padx=10, pady=5)
        
        r_flood = tk.Radiobutton(
            group_mode, 
            text="Preenchimento (Flood Fill - Preserva internos)", 
            value="floodfill", 
            variable=self.mode_var, 
            command=self.update_preview,
            bg=self.bg_panel, 
            fg=self.fg_light, 
            selectcolor=self.bg_dark, 
            activebackground=self.bg_panel,
            activeforeground=self.fg_light
        )
        r_flood.pack(anchor=tk.W, padx=10)
        
        r_range = tk.Radiobutton(
            group_mode, 
            text="Faixa de Cores (Global - Remove todos os tons)", 
            value="range", 
            variable=self.mode_var, 
            command=self.update_preview,
            bg=self.bg_panel, 
            fg=self.fg_light, 
            selectcolor=self.bg_dark, 
            activebackground=self.bg_panel,
            activeforeground=self.fg_light
        )
        r_range.pack(anchor=tk.W, padx=10)
        
        # --- Sliders ---
        # Tolerance Slider
        lbl_tol = tk.Label(scroll_container, text="Tolerância de Fundo: 30", bg=self.bg_panel, fg=self.fg_light, anchor=tk.W)
        lbl_tol.pack(fill=tk.X, padx=10, pady=(10, 0))
        scale_tol = tk.Scale(
            scroll_container, 
            from_=0, 
            to=150, 
            orient=tk.HORIZONTAL, 
            variable=self.tolerance_var, 
            showvalue=0,
            command=lambda val: [lbl_tol.config(text=f"Tolerância de Fundo: {val}"), self.update_preview()],
            bg=self.bg_panel, 
            highlightbackground=self.bg_panel, 
            troughcolor="#333333", 
            activebackground=self.accent_color
        )
        scale_tol.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Erode Slider
        lbl_erode = tk.Label(scroll_container, text="Erosão do Halo: 1 px", bg=self.bg_panel, fg=self.fg_light, anchor=tk.W)
        lbl_erode.pack(fill=tk.X, padx=10, pady=(5, 0))
        scale_erode = tk.Scale(
            scroll_container, 
            from_=0, 
            to=5, 
            orient=tk.HORIZONTAL, 
            variable=self.erode_var, 
            showvalue=0,
            command=lambda val: [lbl_erode.config(text=f"Erosão do Halo: {val} px"), self.update_preview()],
            bg=self.bg_panel, 
            highlightbackground=self.bg_panel, 
            troughcolor="#333333", 
            activebackground=self.accent_color
        )
        scale_erode.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Feather Slider
        lbl_feather = tk.Label(scroll_container, text="Suavização (Feather): 1.0 px", bg=self.bg_panel, fg=self.fg_light, anchor=tk.W)
        lbl_feather.pack(fill=tk.X, padx=10, pady=(5, 0))
        scale_feather = tk.Scale(
            scroll_container, 
            from_=0.0, 
            to=5.0, 
            resolution=0.5,
            orient=tk.HORIZONTAL, 
            variable=self.feather_var, 
            showvalue=0,
            command=lambda val: [lbl_feather.config(text=f"Suavização (Feather): {val} px"), self.update_preview()],
            bg=self.bg_panel, 
            highlightbackground=self.bg_panel, 
            troughcolor="#333333", 
            activebackground=self.accent_color
        )
        scale_feather.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Defringe Slider
        lbl_defringe = tk.Label(scroll_container, text="Defringir Cores: 3 px", bg=self.bg_panel, fg=self.fg_light, anchor=tk.W)
        lbl_defringe.pack(fill=tk.X, padx=10, pady=(5, 0))
        scale_defringe = tk.Scale(
            scroll_container, 
            from_=0, 
            to=10, 
            orient=tk.HORIZONTAL, 
            variable=self.defringe_var, 
            showvalue=0,
            command=lambda val: [lbl_defringe.config(text=f"Defringir Cores: {val} px"), self.update_preview()],
            bg=self.bg_panel, 
            highlightbackground=self.bg_panel, 
            troughcolor="#333333", 
            activebackground=self.accent_color
        )
        scale_defringe.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # --- Preview Background Choice ---
        group_p_bg = tk.LabelFrame(scroll_container, text="Fundo de Visualização", bg=self.bg_panel, fg="#bbbbbb", bd=0)
        group_p_bg.pack(fill=tk.X, padx=10, pady=5)
        
        p_bg_frame = tk.Frame(group_p_bg, bg=self.bg_panel)
        p_bg_frame.pack(fill=tk.X)
        for text, val in [("Xadrez", "checker"), ("Cinza", "grey"), ("Branco", "white"), ("Preto", "black")]:
            r = tk.Radiobutton(
                p_bg_frame, 
                text=text, 
                value=val, 
                variable=self.preview_bg_var, 
                command=self.update_preview,
                bg=self.bg_panel, 
                fg=self.fg_light, 
                selectcolor=self.bg_dark, 
                activebackground=self.bg_panel,
                activeforeground=self.fg_light,
                font=("Helvetica", 8)
            )
            r.pack(side=tk.LEFT, padx=5)

        # Action Buttons (Save/Batch)
        btn_frame = tk.Frame(control_panel, bg=self.bg_panel)
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=10)
        
        save_btn = tk.Button(
            btn_frame, 
            text="Salvar Imagem Atual", 
            command=self.save_current_image,
            bg=self.accent_color, 
            fg="white", 
            activebackground=self.accent_active,
            activeforeground="white",
            relief=tk.FLAT, 
            bd=0, 
            height=2, 
            font=("Helvetica", 10, "bold")
        )
        save_btn.pack(fill=tk.X, pady=5)
        
        batch_btn = tk.Button(
            btn_frame, 
            text="Processar Lote (Toda a Pasta)", 
            command=self.batch_process_folder,
            bg="#2a2a2a", 
            fg=self.fg_light, 
            activebackground="#444444",
            activeforeground="white",
            relief=tk.FLAT, 
            bd=0, 
            height=2, 
            font=("Helvetica", 9, "bold")
        )
        batch_btn.pack(fill=tk.X, pady=5)

    def load_default_image(self):
        # Look for the animation directory files
        if os.path.exists(self.default_dir):
            files = [f for f in os.listdir(self.default_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            if files:
                first_img = os.path.join(self.default_dir, sorted(files)[0])
                self.load_image(first_img)

    def choose_image(self):
        initial = self.default_dir if os.path.exists(self.default_dir) else "/"
        path = filedialog.askopenfilename(
            initialdir=initial,
            title="Selecionar Imagem",
            filetypes=[("Imagens PNG/JPG", "*.png *.jpg *.jpeg *.bmp"), ("Todos os Arquivos", "*.*")]
        )
        if path:
            self.load_image(path)

    def load_image(self, path):
        try:
            self.image_path = path
            self.original_image = Image.open(path)
            self.original_size = self.original_image.size
            self.file_label.config(text=f"{os.path.basename(path)} ({self.original_size[0]}x{self.original_size[1]})")
            
            # Autodetect background color to pre-fill settings if auto is checked
            _, detected = detect_background_color(self.original_image)
            # Adjust default tolerances/settings based on filename or detection
            if "pasted image" in os.path.basename(path).lower() and "2" not in os.path.basename(path).lower():
                # Pasted image.png has black bg
                self.bg_type_var.set("black")
                self.tolerance_var.set(30)
            else:
                if detected == "white":
                    self.bg_type_var.set("white")
                    self.tolerance_var.set(40)
                else:
                    self.bg_type_var.set("black")
                    self.tolerance_var.set(30)
            
            # Recreate downscaled preview images
            # Canvas size is around 400x400 (let's resize preview to max 400x400)
            w, h = self.original_size
            ratio = min(400 / w, 400 / h)
            new_size = (int(w * ratio), int(h * ratio))
            
            self.preview_original = self.original_image.resize(new_size, Image.Resampling.LANCZOS)
            
            # Display original in canvas
            self.display_original()
            
            # Process and update preview
            self.update_preview()
        except Exception as e:
            messagebox.showerror("Erro ao Carregar Imagem", f"Não foi possível abrir a imagem:\n{e}")

    def display_original(self):
        if not self.preview_original:
            return
            
        w, h = self.preview_original.size
        # Center in canvas
        self.canvas_orig.delete("all")
        
        # Convert PIL to Tk PhotoImage using buffer
        buf = io.BytesIO()
        self.preview_original.save(buf, format='PNG')
        self.photo_original = tk.PhotoImage(data=buf.getvalue())
        
        # Canvas center coordinate
        c_w = self.canvas_orig.winfo_width()
        c_h = self.canvas_orig.winfo_height()
        if c_w < 10: c_w = 400
        if c_h < 10: c_h = 400
        
        self.canvas_orig.create_image(c_w // 2, c_h // 2, image=self.photo_original)

    def create_checkerboard(self, width, height, square_size=10):
        tile = Image.new("RGBA", (square_size * 2, square_size * 2))
        pixels = tile.load()
        c1 = (240, 240, 240, 255)
        c2 = (200, 200, 200, 255)
        for y in range(square_size * 2):
            for x in range(square_size * 2):
                if ((x // square_size) + (y // square_size)) % 2 == 0:
                    pixels[x, y] = c1
                else:
                    pixels[x, y] = c2
                    
        bg = Image.new("RGBA", (width, height))
        for y in range(0, height, square_size * 2):
            for x in range(0, width, square_size * 2):
                bg.paste(tile, (x, y))
        return bg

    def get_preview_bg(self, width, height, bg_type="checker"):
        if bg_type == "checker":
            return self.create_checkerboard(width, height)
        elif bg_type == "grey":
            return Image.new("RGBA", (width, height), (128, 128, 128, 255))
        elif bg_type == "white":
            return Image.new("RGBA", (width, height), (255, 255, 255, 255))
        else: # black
            return Image.new("RGBA", (width, height), (0, 0, 0, 255))

    def update_preview(self):
        if not self.preview_original:
            return
            
        # Get parameters
        bg_type = self.bg_type_var.get()
        mode = self.mode_var.get()
        tolerance = self.tolerance_var.get()
        erode = self.erode_var.get()
        feather = self.feather_var.get()
        defringe = self.defringe_var.get()
        preview_bg_type = self.preview_bg_var.get()
        
        # Process the downscaled original for instant real-time response
        proc, detected_color = process_image(
            self.preview_original,
            bg_type=bg_type,
            tolerance=tolerance,
            erode_pixels=erode,
            feather_pixels=feather,
            defringe_radius=defringe,
            mode=mode
        )
        
        # Generate the display image over checkered background
        w, h = proc.size
        display_img = self.get_preview_bg(w, h, preview_bg_type)
        display_img.paste(proc, (0, 0), proc)
        
        # Save to buffer and convert
        buf = io.BytesIO()
        display_img.save(buf, format='PNG')
        self.photo_processed = tk.PhotoImage(data=buf.getvalue())
        
        # Center in canvas
        self.canvas_proc.delete("all")
        c_w = self.canvas_proc.winfo_width()
        c_h = self.canvas_proc.winfo_height()
        if c_w < 10: c_w = 400
        if c_h < 10: c_h = 400
        
        self.canvas_proc.create_image(c_w // 2, c_h // 2, image=self.photo_processed)

    def save_current_image(self):
        if not self.original_image:
            messagebox.showwarning("Nenhuma Imagem", "Por favor, carregue uma imagem primeiro.")
            return
            
        # Select target file path
        initial_name = os.path.basename(self.image_path)
        base, ext = os.path.splitext(initial_name)
        default_out_name = f"{base}_clean.png"
        
        out_path = filedialog.asksaveasfilename(
            initialdir=os.path.dirname(self.image_path),
            initialfile=default_out_name,
            title="Salvar Imagem Como",
            filetypes=[("Imagem PNG", "*.png")]
        )
        
        if out_path:
            try:
                # Process the full-resolution image with UI settings
                self.root.config(cursor="wait")
                self.root.update()
                
                bg_type = self.bg_type_var.get()
                mode = self.mode_var.get()
                tolerance = self.tolerance_var.get()
                erode = self.erode_var.get()
                feather = self.feather_var.get()
                defringe = self.defringe_var.get()
                
                final_img, _ = process_image(
                    self.original_image,
                    bg_type=bg_type,
                    tolerance=tolerance,
                    erode_pixels=erode,
                    feather_pixels=feather,
                    defringe_radius=defringe,
                    mode=mode
                )
                
                final_img.save(out_path, "PNG")
                self.root.config(cursor="")
                messagebox.showinfo("Sucesso", f"Imagem salva com sucesso em:\n{out_path}")
            except Exception as e:
                self.root.config(cursor="")
                messagebox.showerror("Erro ao Salvar", f"Erro ao processar/salvar imagem:\n{e}")

    def batch_process_folder(self):
        if not os.path.exists(self.default_dir):
            messagebox.showerror("Diretório Não Encontrado", f"O diretório padrão não existe:\n{self.default_dir}")
            return
            
        files = [f for f in os.listdir(self.default_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        if not files:
            messagebox.showinfo("Nenhuma Imagem", f"Nenhuma imagem encontrada em:\n{self.default_dir}")
            return
            
        confirm = messagebox.askyesno(
            "Confirmar Processamento em Lote", 
            f"Deseja processar {len(files)} imagens da pasta:\n{self.default_dir}\n\nAs imagens limpas serão salvas na subpasta 'processed' com as configurações atuais."
        )
        
        if not confirm:
            return
            
        try:
            self.root.config(cursor="wait")
            self.root.update()
            
            out_dir = os.path.join(self.default_dir, "processed")
            os.makedirs(out_dir, exist_ok=True)
            
            bg_type = self.bg_type_var.get()
            mode = self.mode_var.get()
            tolerance = self.tolerance_var.get()
            erode = self.erode_var.get()
            feather = self.feather_var.get()
            defringe = self.defringe_var.get()
            
            count = 0
            for f in files:
                in_path = os.path.join(self.default_dir, f)
                img = Image.open(in_path)
                
                # Check custom auto-overrides per image to avoid using bad auto for specific ones
                # For pasted image (black bg), force black background
                img_bg_type = bg_type
                img_tolerance = tolerance
                
                if bg_type == "auto":
                    # Let auto detect per image
                    pass
                elif f.lower().startswith("pasted image.png") or f.lower().startswith("pasted_image.png"):
                    img_bg_type = "black"
                
                final_img, _ = process_image(
                    img,
                    bg_type=img_bg_type,
                    tolerance=img_tolerance,
                    erode_pixels=erode,
                    feather_pixels=feather,
                    defringe_radius=defringe,
                    mode=mode
                )
                
                # Save inside out_dir with same name (clean suffix is optional since it's a separate folder)
                out_path = os.path.join(out_dir, f)
                final_img.save(out_path, "PNG")
                count += 1
                
            self.root.config(cursor="")
            messagebox.showinfo(
                "Lote Concluído", 
                f"Processados {count} arquivos com sucesso!\nSalvos em:\n{out_dir}"
            )
            
            # Reload currently loaded image if it is one of the files
            if self.image_path:
                self.load_image(self.image_path)
                
        except Exception as e:
            self.root.config(cursor="")
            messagebox.showerror("Erro em Lote", f"Erro no processamento em lote:\n{e}")

# If we run this directly
if __name__ == "__main__":
    root = tk.Tk()
    app = BackgroundRemovalApp(root)
    
    # Configure grid weights to handle canvas resizing nicely
    root.update()
    # Handle resize events to redraw canvas images properly
    def on_resize(event):
        if event.widget == root:
            app.display_original()
            app.update_preview()
            
    root.bind("<Configure>", on_resize)
    root.mainloop()
