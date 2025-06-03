#!/usr/bin/env python3

import tkinter as tk
from tkinter import ttk
from gui import WatermarkGUI

def main():
    root = tk.Tk()
    
    style = ttk.Style()
    try:
        style.theme_use('clam')
    except:
        pass
    
    try:
        style.configure('Accent.TButton', foreground='white', background='#0078d4')
        style.map('Accent.TButton', background=[('active', '#106ebe')])
    except:
        pass
    
    app = WatermarkGUI(root)
    
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    root.minsize(600, 500)
    root.mainloop()

if __name__ == "__main__":
    main()