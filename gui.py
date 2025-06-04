import os
import sys
import threading
import subprocess
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from watermark_processor import WatermarkProcessor

class WatermarkGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Triyog Watermarker")
        self.root.geometry("700x600")
        self.root.resizable(True, True)
        
        try:
            self.root.iconbitmap('icon.ico')
        except:
            pass
        
        self.processor = WatermarkProcessor()
        self.actual_output_folder = None
        self.setup_ui()
        
    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        title_label = ttk.Label(main_frame, text="Triyog Watermarking Tool", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 10))
        
        subtitle_label = ttk.Label(main_frame, text="PhotoStory Competition Watermarker - Dual Output Mode", 
                                  font=('Arial', 10))
        subtitle_label.grid(row=1, column=0, columnspan=3, pady=(0, 20))
        
        ttk.Label(main_frame, text="Input Folder:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.input_folder_var = tk.StringVar()
        input_entry = ttk.Entry(main_frame, textvariable=self.input_folder_var, width=50)
        input_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=(10, 5), pady=5)
        ttk.Button(main_frame, text="Browse", 
                  command=self.browse_input_folder).grid(row=2, column=2, pady=5)
        
        ttk.Label(main_frame, text="Logo File (PNG):").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.logo_file_var = tk.StringVar()
        logo_entry = ttk.Entry(main_frame, textvariable=self.logo_file_var, width=50)
        logo_entry.grid(row=3, column=1, sticky=(tk.W, tk.E), padx=(10, 5), pady=5)
        ttk.Button(main_frame, text="Browse", 
                  command=self.browse_logo_file).grid(row=3, column=2, pady=5)
        
        ttk.Label(main_frame, text="Watermark Text:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.watermark_var = tk.StringVar(value="PNJWEW2025")
        ttk.Entry(main_frame, textvariable=self.watermark_var, width=50).grid(
            row=4, column=1, sticky=(tk.W, tk.E), padx=(10, 5), pady=5)
        
        ttk.Label(main_frame, text="Parent Output Folder:").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.output_folder_var = tk.StringVar()
        output_entry = ttk.Entry(main_frame, textvariable=self.output_folder_var, width=50)
        output_entry.grid(row=5, column=1, sticky=(tk.W, tk.E), padx=(10, 5), pady=5)
        ttk.Button(main_frame, text="Browse", 
                  command=self.browse_output_folder).grid(row=5, column=2, pady=5)
        
        info_label = ttk.Label(main_frame, text="(Output will create 'output_normal' and 'output_wm' subfolders)", 
                              font=('Arial', 8), foreground='gray')
        info_label.grid(row=6, column=1, sticky=tk.W, padx=(10, 5))
        
        ttk.Label(main_frame, text="Attribution CSV (Optional):").grid(row=7, column=0, sticky=tk.W, pady=5)
        self.csv_file_var = tk.StringVar()
        csv_entry = ttk.Entry(main_frame, textvariable=self.csv_file_var, width=50)
        csv_entry.grid(row=7, column=1, sticky=(tk.W, tk.E), padx=(10, 5), pady=5)
        ttk.Button(main_frame, text="Browse", 
                  command=self.browse_csv_file).grid(row=7, column=2, pady=5)
        
        options_frame = ttk.LabelFrame(main_frame, text="Options", padding="10")
        options_frame.grid(row=8, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 10))
        
        self.preserve_structure_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Preserve folder structure in output", 
                       variable=self.preserve_structure_var).grid(row=0, column=0, sticky=tk.W)
        
        progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding="10")
        progress_frame.grid(row=9, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 10))
        progress_frame.columnconfigure(0, weight=1)
        
        self.progress_var = tk.StringVar(value="Ready to start watermarking...")
        self.progress_label = ttk.Label(progress_frame, textvariable=self.progress_var)
        self.progress_label.grid(row=0, column=0, sticky=tk.W)
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate')
        self.progress_bar.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=10, column=0, columnspan=3, pady=20)
        
        self.start_button = ttk.Button(button_frame, text="Start Dual Watermarking", 
                                      command=self.start_processing, style='Accent.TButton')
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.open_normal_button = ttk.Button(button_frame, text="Open Normal Folder", 
                                           command=self.open_normal_folder, state='disabled')
        self.open_normal_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.open_wm_button = ttk.Button(button_frame, text="Open Watermarked Folder", 
                                       command=self.open_wm_folder, state='disabled')
        self.open_wm_button.pack(side=tk.LEFT)
        
        status_frame = ttk.LabelFrame(main_frame, text="Status Log", padding="10")
        status_frame.grid(row=11, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        status_frame.columnconfigure(0, weight=1)
        status_frame.rowconfigure(0, weight=1)
        
        self.status_text = tk.Text(status_frame, height=8, wrap=tk.WORD)
        status_scrollbar = ttk.Scrollbar(status_frame, orient=tk.VERTICAL, command=self.status_text.yview)
        self.status_text.configure(yscrollcommand=status_scrollbar.set)
        
        self.status_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        status_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        main_frame.rowconfigure(11, weight=1)
        
        self.log_status("Welcome to Triyog Enhanced Dual-Output Watermarking Tool!")
        self.log_status("✨ Features: Two output modes - Normal and Watermarked")
        self.log_status("📁 Normal: Simple attributions and small watermark")
        self.log_status("🔒 Watermarked: Diagonal pattern protection with faint logo overlay")
        self.log_status("🏷️ Supports: JPG, PNG, BMP, TIFF, WEBP, GIF files")
        
    def browse_input_folder(self):
        folder = filedialog.askdirectory(title="Select Input Folder (with photographer subfolders)")
        if folder:
            self.input_folder_var.set(folder)
            self.log_status(f"Input folder selected: {folder}")
            
    def browse_logo_file(self):
        file = filedialog.askopenfilename(
            title="Select Logo File (PNG recommended)",
            filetypes=[("PNG files", "*.png"), ("Image files", "*.png *.jpg *.jpeg"), ("All files", "*.*")]
        )
        if file:
            self.logo_file_var.set(file)
            self.log_status(f"Logo file selected: {file}")
            
    def browse_output_folder(self):
        folder = filedialog.askdirectory(title="Select Parent Output Folder")
        if folder:
            self.output_folder_var.set(folder)
            self.log_status(f"Parent output folder selected: {folder}")
            self.log_status("Images will be saved in 'output_normal' and 'output_wm' subfolders")
            
    def browse_csv_file(self):
        file = filedialog.askopenfilename(
            title="Select Attribution CSV File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if file:
            self.csv_file_var.set(file)
            self.log_status(f"Attribution CSV selected: {file}")
            
    def log_status(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.status_text.see(tk.END)
        self.root.update_idletasks()
        
    def validate_inputs(self):
        if not self.input_folder_var.get():
            messagebox.showerror("Error", "Please select an input folder")
            return False
            
        if not os.path.exists(self.input_folder_var.get()):
            messagebox.showerror("Error", "Input folder does not exist")
            return False
            
        if not self.output_folder_var.get():
            messagebox.showerror("Error", "Please select a parent output folder")
            return False
            
        if not self.watermark_var.get().strip():
            messagebox.showerror("Error", "Please enter watermark text")
            return False
            
        logo_file = self.logo_file_var.get()
        if logo_file and not os.path.exists(logo_file):
            messagebox.showerror("Error", "Logo file does not exist")
            return False
            
        return True
        
    def start_processing(self):
        if not self.validate_inputs():
            return
            
        self.start_button.config(state='disabled')
        self.open_normal_button.config(state='disabled')
        self.open_wm_button.config(state='disabled')
        
        self.status_text.delete(1.0, tk.END)
        self.log_status("🚀 Starting dual-output watermarking process...")
        
        processing_thread = threading.Thread(target=self.process_images)
        processing_thread.daemon = True
        processing_thread.start()
        
    def process_images(self):
        try:
            input_folder = self.input_folder_var.get()
            parent_output_folder = self.output_folder_var.get()
            watermark_text = self.watermark_var.get().strip()
            csv_file = self.csv_file_var.get()
            logo_file = self.logo_file_var.get()
            preserve_structure = self.preserve_structure_var.get()
            
            # Create both output folders
            normal_output_folder = os.path.join(parent_output_folder, "output_normal")
            wm_output_folder = os.path.join(parent_output_folder, "output_wm")
            
            if logo_file and os.path.exists(logo_file):
                if self.processor.load_logo(logo_file):
                    self.log_status(f"✅ Logo loaded successfully: {Path(logo_file).name}")
                else:
                    self.log_status("❌ Failed to load logo, continuing without logo")
            
            # Create output directories
            Path(normal_output_folder).mkdir(parents=True, exist_ok=True)
            Path(wm_output_folder).mkdir(parents=True, exist_ok=True)
            self.log_status(f"📁 Normal output folder created: {normal_output_folder}")
            self.log_status(f"📁 Watermarked output folder created: {wm_output_folder}")
            
            if csv_file and os.path.exists(csv_file):
                count = self.processor.load_attribution_csv(csv_file)
                self.log_status(f"📊 Loaded attribution data for {count} files")
            
            self.log_status("🔍 Scanning for images in all subfolders...")
            image_files = self.processor.find_all_images(input_folder)
            
            if not image_files:
                self.log_status("❌ No supported image files found in input folder or subfolders")
                messagebox.showwarning("Warning", "No supported image files found")
                return
                
            self.log_status(f"🖼️ Found {len(image_files)} images to process")
            
            photographers = set(img['photographer'] for img in image_files if img['photographer'])
            if photographers:
                self.log_status(f"👥 Photographers found: {', '.join(photographers)}")
            
            # Double the progress bar maximum since we're processing each image twice
            self.progress_bar.config(maximum=len(image_files) * 2)
            
            normal_log_path = Path(normal_output_folder) / "watermarking_log.csv"
            wm_log_path = Path(wm_output_folder) / "watermarking_log.csv"
            
            success_count_normal = 0
            success_count_wm = 0
            
            for i, img_info in enumerate(image_files):
                img_file = img_info['path']
                photographer = img_info['photographer']
                subfolder = img_info['subfolder']
                relative_path = img_info['relative_path']
                
                # Determine output paths for both versions
                if photographer:
                    normal_photographer_folder = Path(normal_output_folder) / photographer
                    wm_photographer_folder = Path(wm_output_folder) / photographer
                    normal_photographer_folder.mkdir(parents=True, exist_ok=True)
                    wm_photographer_folder.mkdir(parents=True, exist_ok=True)
                    normal_output_file = normal_photographer_folder / img_file.name
                    wm_output_file = wm_photographer_folder / img_file.name
                else:
                    normal_output_file = Path(normal_output_folder) / img_file.name
                    wm_output_file = Path(wm_output_folder) / img_file.name
                
                # Process normal version
                progress_text = f"Processing Normal {i+1}/{len(image_files)}: {img_file.name}"
                if photographer:
                    progress_text += f" (📸 {photographer})"
                    
                self.progress_var.set(progress_text)
                self.progress_bar.config(value=i*2 + 1)
                self.root.update_idletasks()
                
                self.log_status(f"⚡ Processing Normal: {img_file.name}" + (f" by {photographer}" if photographer else ""))
                
                if self.processor.add_watermark(str(img_file), str(normal_output_file), 
                                            watermark_text, str(normal_log_path), 
                                            photographer, subfolder, watermark_mode='normal'):
                    success_count_normal += 1
                    self.log_status(f"✅ Normal saved: {normal_output_file.relative_to(Path(normal_output_folder))}")
                else:
                    self.log_status(f"❌ Normal failed: {img_file.name}")
                
                # Process watermarked version
                progress_text = f"Processing Watermarked {i+1}/{len(image_files)}: {img_file.name}"
                if photographer:
                    progress_text += f" (📸 {photographer})"
                    
                self.progress_var.set(progress_text)
                self.progress_bar.config(value=i*2 + 2)
                self.root.update_idletasks()
                
                self.log_status(f"🔒 Processing Watermarked: {img_file.name}" + (f" by {photographer}" if photographer else ""))
                
                if self.processor.add_watermark(str(img_file), str(wm_output_file), 
                                            watermark_text, str(wm_log_path), 
                                            photographer, subfolder, watermark_mode='watermarked'):
                    success_count_wm += 1
                    self.log_status(f"✅ Watermarked saved: {wm_output_file.relative_to(Path(wm_output_folder))}")
                else:
                    self.log_status(f"❌ Watermarked failed: {img_file.name}")
            
            self.progress_var.set(f"🎉 Complete! Normal: {success_count_normal}/{len(image_files)}, Watermarked: {success_count_wm}/{len(image_files)}")
            self.log_status(f"🎊 Processing complete!")
            self.log_status(f"📊 Normal version: {success_count_normal}/{len(image_files)} images")
            self.log_status(f"📊 Watermarked version: {success_count_wm}/{len(image_files)} images")
            self.log_status(f"📁 Normal output: {normal_output_folder}")
            self.log_status(f"📁 Watermarked output: {wm_output_folder}")
            
            messagebox.showinfo("Complete", 
                            f"Dual watermarking complete! 🎉\n\n"
                            f"Normal version: {success_count_normal}/{len(image_files)} images\n"
                            f"Watermarked version: {success_count_wm}/{len(image_files)} images\n\n"
                            f"Output folders:\n"
                            f"• Normal: {normal_output_folder}\n"
                            f"• Watermarked: {wm_output_folder}\n\n"
                            f"Features:\n"
                            f"• Normal: Simple attributions and small watermark\n"
                            f"• Watermarked: Diagonal pattern protection")
            
            self.actual_normal_folder = normal_output_folder
            self.actual_wm_folder = wm_output_folder
            self.open_normal_button.config(state='normal')
            self.open_wm_button.config(state='normal')
            
        except Exception as e:
            self.log_status(f"💥 Error: {str(e)}")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
        finally:
            self.start_button.config(state='normal')
            self.progress_bar.config(value=0)
            self.progress_var.set("Ready to start watermarking...")
            
    def open_normal_folder(self):
        if hasattr(self, 'actual_normal_folder') and self.actual_normal_folder and os.path.exists(self.actual_normal_folder):
            try:
                if sys.platform == "win32":
                    os.startfile(self.actual_normal_folder)
                elif sys.platform == "darwin":  # macOS
                    subprocess.run(["open", self.actual_normal_folder])
                else:  # Linux
                    subprocess.run(["xdg-open", self.actual_normal_folder])
                self.log_status(f"📂 Opened normal output folder: {self.actual_normal_folder}")
            except Exception as e:
                self.log_status(f"❌ Could not open folder: {str(e)}")
                messagebox.showerror("Error", f"Could not open normal folder: {str(e)}")
        else:
            messagebox.showwarning("Warning", "No normal output folder available or folder doesn't exist")
    
    def open_wm_folder(self):
        if hasattr(self, 'actual_wm_folder') and self.actual_wm_folder and os.path.exists(self.actual_wm_folder):
            try:
                if sys.platform == "win32":
                    os.startfile(self.actual_wm_folder)
                elif sys.platform == "darwin":  # macOS
                    subprocess.run(["open", self.actual_wm_folder])
                else:  # Linux
                    subprocess.run(["xdg-open", self.actual_wm_folder])
                self.log_status(f"📂 Opened watermarked output folder: {self.actual_wm_folder}")
            except Exception as e:
                self.log_status(f"❌ Could not open folder: {str(e)}")
                messagebox.showerror("Error", f"Could not open watermarked folder: {str(e)}")
        else:
            messagebox.showwarning("Warning", "No watermarked output folder available or folder doesn't exist")
