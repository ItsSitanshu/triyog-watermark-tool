import os
import csv
from datetime import datetime
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

class WatermarkProcessor:
    def __init__(self):
        self.supported_formats = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp', '.gif')
        self.attribution_data = {}
        self.logo_image = None
        
    def load_logo(self, logo_path):
        try:
            with Image.open(logo_path) as logo:
                if logo.mode != 'RGBA':
                    logo = logo.convert('RGBA')
                self.logo_image = logo.copy()
            return True
        except Exception as e:
            print(f"Error loading logo: {e}")
            return False
        
    def load_attribution_csv(self, csv_path):
        try:
            with open(csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    filename = row.get('filename', '').lower()
                    self.attribution_data[filename] = {
                        'team_name': row.get('team_name', ''),
                        'caption': row.get('caption', ''),
                        'photographer': row.get('photographer', '')
                    }
            return len(self.attribution_data)
        except Exception as e:
            print(f"Error loading CSV: {e}")
            return 0
            
    def get_font(self, size=20):
        font_paths = [
            "arial.ttf",
            "Arial.ttf", 
            "/System/Library/Fonts/Arial.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "C:\\Windows\\Fonts\\arial.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        ]
        
        for font_path in font_paths:
            try:
                return ImageFont.truetype(font_path, size)
            except:
                continue
        
        try:
            return ImageFont.load_default()
        except:
            return None
    
    def add_watermark(self, image_path, output_path, watermark_text, attribution_log_path, photographer_name=None, subfolder_name=None):
        try:
            with Image.open(image_path) as img:
                max_size = (1920, 1080)
                original_size = img.size
                
                if img.width > max_size[0] or img.height > max_size[1]:
                    ratio = min(max_size[0] / img.width, max_size[1] / img.height)
                    new_size = (int(img.width * ratio), int(img.height * ratio))
                    img = img.resize(new_size, Image.Resampling.LANCZOS)
                
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                
                overlay = Image.new('RGBA', img.size, (255, 255, 255, 0))
                draw = ImageDraw.Draw(overlay)
                
                watermark_font = self.get_font(max(16, img.width // 60))
                caption_font = self.get_font(max(12, img.width // 80))
                photographer_font = self.get_font(max(10, img.width // 90))
                
                margin = max(15, img.width // 80)
                
                logo_resized = self.resize_logo(img.size, max_logo_ratio=0.09)
                if logo_resized:
                    logo_x = margin
                    logo_y = img.height - logo_resized.height - margin
                    overlay.paste(logo_resized, (logo_x, logo_y), logo_resized)
                
                final_watermark_text = watermark_text
                if subfolder_name:
                    final_watermark_text = f"{watermark_text}"
                
                if watermark_font and final_watermark_text:
                    bbox = draw.textbbox((0, 0), final_watermark_text, font=watermark_font)
                    w_width = bbox[2] - bbox[0]
                    w_height = bbox[3] - bbox[1]
                    
                    w_x = img.width - w_width - margin
                    w_y = img.height - w_height - margin
                    
                    padding = 6
                    bg_x1 = w_x - padding
                    bg_y1 = w_y - padding
                    bg_x2 = w_x + w_width + padding
                    bg_y2 = w_y + w_height + padding
                    
                    draw.rectangle([bg_x1, bg_y1, bg_x2, bg_y2], fill=(0, 0, 0, 100))
                    draw.text((w_x, w_y), final_watermark_text, fill=(255, 255, 255, 220), font=watermark_font)
                
                filename = Path(image_path).name.lower()
                attribution = self.attribution_data.get(filename, {})
                
                photographer = photographer_name or attribution.get('photographer', '')
                if photographer and photographer_font:
                    photographer_text = f"{photographer}"
                    p_bbox = draw.textbbox((0, 0), photographer_text, font=photographer_font)
                    p_width = p_bbox[2] - p_bbox[0]
                    p_height = p_bbox[3] - p_bbox[1]
                    
                    p_x = img.width - p_width - margin
                    p_y = margin
                    
                    padding = 4
                    draw.rectangle([p_x - padding, p_y - padding, 
                                p_x + p_width + padding, p_y + p_height + padding], 
                                fill=(0, 0, 0, 80))
                    
                    draw.text((p_x, p_y), photographer_text, 
                            fill=(255, 255, 255, 200), font=photographer_font)
                
                if attribution.get('caption') and caption_font:
                    caption_text = attribution['caption']
                    c_bbox = draw.textbbox((0, 0), caption_text, font=caption_font)
                    c_width = c_bbox[2] - c_bbox[0]
                    c_height = c_bbox[3] - c_bbox[1]
                    
                    c_x = (img.width - c_width) // 2
                    c_y = img.height - c_height - margin - 50
                    
                    padding = 5
                    draw.rectangle([c_x - padding, c_y - padding, 
                                c_x + c_width + padding, c_y + c_height + padding], 
                                fill=(0, 0, 0, 120))
                    
                    draw.text((c_x, c_y), caption_text, 
                            fill=(255, 255, 255, 200), font=caption_font)
                
                watermarked = Image.alpha_composite(img, overlay)
                
                output_ext = Path(output_path).suffix.lower()
                if output_ext in ['.jpg', '.jpeg']:
                    final_image = Image.new('RGB', watermarked.size, (255, 255, 255))
                    final_image.paste(watermarked, mask=watermarked.split()[-1] if watermarked.mode == 'RGBA' else None)
                    watermarked = final_image
                elif output_ext in ['.png', '.tiff']:
                    pass
                else:
                    if watermarked.mode == 'RGBA':
                        final_image = Image.new('RGB', watermarked.size, (255, 255, 255))
                        final_image.paste(watermarked, mask=watermarked.split()[-1])
                        watermarked = final_image
                
                output_path_obj = Path(output_path)
                output_path_obj.parent.mkdir(parents=True, exist_ok=True)
                
                save_kwargs = {}
                if output_ext in ['.jpg', '.jpeg']:
                    save_kwargs = {
                        'quality': 85,
                        'optimize': True,
                        'progressive': True
                    }
                elif output_ext == '.png':
                    save_kwargs = {
                        'optimize': True,
                        'compress_level': 6
                    }
                elif output_ext == '.webp':
                    save_kwargs = {
                        'quality': 85,
                        'method': 6
                    }
                
                watermarked.save(output_path, **save_kwargs)
                
                self.log_attribution(attribution_log_path, Path(image_path).name, 
                                attribution.get('team_name', 'N/A'),
                                attribution.get('caption', 'N/A'),
                                final_watermark_text, photographer)
                
                return True
                
        except Exception as e:
            print(f"Error processing {image_path}: {e}")
            return False

    def resize_logo(self, image_size, max_logo_ratio=0.12):
        if not self.logo_image:
            return None
            
        img_width, img_height = image_size
        max_logo_width = int(img_width * max_logo_ratio)
        max_logo_height = int(img_height * max_logo_ratio)
        
        logo_width, logo_height = self.logo_image.size
        scale_w = max_logo_width / logo_width
        scale_h = max_logo_height / logo_height
        scale = min(scale_w, scale_h)
        
        new_width = max(50, min(200, int(logo_width * scale)))
        new_height = max(50, min(200, int(logo_height * scale)))
        
        return self.logo_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    def log_attribution(self, log_path, filename, team_name, caption, watermark_text, photographer):
        try:
            file_exists = os.path.exists(log_path)
            
            with open(log_path, 'a', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['filename', 'photographer', 'team_name', 'caption', 'date_processed', 'watermark_text']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                if not file_exists:
                    writer.writeheader()
                
                writer.writerow({
                    'filename': filename,
                    'photographer': photographer or 'N/A',
                    'team_name': team_name,
                    'caption': caption,
                    'date_processed': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'watermark_text': watermark_text
                })
        except Exception as e:
            print(f"Error logging to CSV: {e}")

    def find_all_images(self, root_folder):
        image_files = []
        root_path = Path(root_folder)
        
        for file_path in root_path.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in self.supported_formats:
                photographer_folder = file_path.parent.name
                if photographer_folder != root_path.name:
                    photographer_name = photographer_folder
                    subfolder_name = photographer_folder
                else:
                    photographer_name = None
                    subfolder_name = None
                    
                image_files.append({
                    'path': file_path,
                    'photographer': photographer_name,
                    'subfolder': subfolder_name,
                    'relative_path': file_path.relative_to(root_path)
                })
        
        return image_files