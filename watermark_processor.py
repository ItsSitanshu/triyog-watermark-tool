import os
import csv
import math
from datetime import datetime
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

class WatermarkProcessor:
    def __init__(self):
        self.supported_formats = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp', '.gif')
        self.attribution_data = {}
        self.logo_image = None
        
    def load_logo(self, logo_path):
        """Load and prepare logo image for watermarking"""
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
        """Load attribution data from CSV file"""
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
            
    def get_font(self, size=20):
        """Get appropriate font for text rendering"""
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
    
    def add_diagonal_pattern(self, overlay, img_size, watermark_text, logo_resized=None):
        """Add diagonal watermark pattern across the entire image"""
        draw = ImageDraw.Draw(overlay)
        img_width, img_height = img_size
        
        # Font size based on image size
        pattern_font_size = max(24, img_width // 40)
        pattern_font = self.get_font(pattern_font_size)
        
        # Calculate diagonal spacing
        diagonal_spacing = max(200, img_width // 8)
        
        # Use 45-degree angle for consistent diagonal pattern
        angle_rad = math.radians(45)
        
        # Calculate text dimensions for positioning
        if pattern_font:
            bbox = draw.textbbox((0, 0), watermark_text, font=pattern_font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        else:
            text_width = len(watermark_text) * 12
            text_height = 20
        
        # Calculate the diagonal of the image to ensure full coverage
        image_diagonal = math.sqrt(img_width**2 + img_height**2)
        
        # Calculate how many diagonal lines we need to cover the entire image
        # We need to cover from one corner to the opposite corner
        num_diagonals = int(image_diagonal / diagonal_spacing) + 2
        
        # Starting position - we'll start from outside the image bounds to ensure coverage
        start_offset = image_diagonal / 2
        
        # Create diagonal lines going from top-left to bottom-right direction
        for i in range(-num_diagonals, num_diagonals + 1):
            # Calculate the starting point for this diagonal line
            # Each line is offset by diagonal_spacing perpendicular to the diagonal direction
            offset_distance = i * diagonal_spacing
            
            # Calculate perpendicular offset (rotate 90 degrees from diagonal direction)
            perp_x = -math.sin(angle_rad) * offset_distance
            perp_y = math.cos(angle_rad) * offset_distance
            
            # Start from center and add perpendicular offset
            start_x = img_width / 2 + perp_x - start_offset * math.cos(angle_rad)
            start_y = img_height / 2 + perp_y - start_offset * math.sin(angle_rad)
            
            # Calculate how many text elements we need along this diagonal
            diagonal_length = image_diagonal * 2  # Extra length to ensure coverage
            num_texts_on_line = int(diagonal_length / (text_width + 50)) + 1
            
            # Place text elements along this diagonal line
            for j in range(num_texts_on_line):
                # Calculate position along the diagonal
                distance_along_diagonal = j * (text_width + 50)
                
                x = start_x + distance_along_diagonal * math.cos(angle_rad)
                y = start_y + distance_along_diagonal * math.sin(angle_rad)
                
                # Only draw if any part of the text would be visible in the image
                if (x > -text_width and x < img_width + text_width and 
                    y > -text_height and y < img_height + text_height):
                    
                    # Add semi-transparent text (0.2 opacity = 51/255)
                    if pattern_font:
                        draw.text((x, y), watermark_text, fill=(255, 255, 255, 51), font=pattern_font)
                    
                    # Add small logo at some positions (every 3rd position)
                    if logo_resized and (i + j) % 3 == 0:
                        logo_x = int(x + text_width + 20)
                        logo_y = int(y - logo_resized.height // 2)
                        
                        # Create a faint version of the logo (0.5 opacity)
                        faint_logo = logo_resized.copy()
                        # Reduce alpha channel to make it faint
                        if faint_logo.mode == 'RGBA':
                            alpha = faint_logo.split()[-1]
                            alpha = alpha.point(lambda p: int(p * 0.5))  # 50% opacity
                            faint_logo.putalpha(alpha)
                        
                        # Check if logo position is at least partially within image bounds
                        if (logo_x > -logo_resized.width and logo_x < img_width + logo_resized.width and 
                        logo_y > -logo_resized.height and logo_y < img_height + logo_resized.height):
                            overlay.paste(faint_logo, (logo_x, logo_y), faint_logo)

    def resize_logo(self, target_size, mode='normal'):
        """Resize logo based on target image size and watermark mode"""
        if not self.logo_image:
            return None
            
        img_width, img_height = target_size
        
        if mode == 'watermarked':
            # Smaller logo for watermarked mode
            logo_size = max(40, min(img_width // 20, img_height // 20))
        else:
            # Standard logo size
            logo_size = max(60, min(img_width // 15, img_height // 15))
        
        # Maintain aspect ratio
        logo_ratio = self.logo_image.width / self.logo_image.height
        if logo_ratio > 1:
            new_width = logo_size
            new_height = int(logo_size / logo_ratio)
        else:
            new_width = int(logo_size * logo_ratio)
            new_height = logo_size
            
        return self.logo_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    def add_watermark(self, image_path, output_path, watermark_text, attribution_log_path, 
                     photographer_name=None, subfolder_name=None, watermark_mode='normal'):
        """Add watermark to image with two modes: normal and watermarked"""
        try:
            with Image.open(image_path) as img:
                max_size = (1920, 1080)
                original_size = img.size
                
                # Resize if image is too large
                if img.width > max_size[0] or img.height > max_size[1]:
                    ratio = min(max_size[0] / img.width, max_size[1] / img.height)
                    new_size = (int(img.width * ratio), int(img.height * ratio))
                    img = img.resize(new_size, Image.Resampling.LANCZOS)
                
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                
                overlay = Image.new('RGBA', img.size, (255, 255, 255, 0))
                draw = ImageDraw.Draw(overlay)
                
                # Fonts for different elements
                watermark_font = self.get_font(max(16, img.width // 60))
                caption_font = self.get_font(max(12, img.width // 80))
                photographer_font = self.get_font(max(10, img.width // 90))
                
                margin = max(15, img.width // 80)
                
                # Resize logo based on mode
                logo_resized = self.resize_logo(img.size, watermark_mode)
                
                # Add diagonal pattern for watermarked mode
                if watermark_mode == 'watermarked':
                    self.add_diagonal_pattern(overlay, img.size, watermark_text, logo_resized)
                
                # Get attribution data
                filename_key = Path(image_path).name.lower()
                attribution = self.attribution_data.get(filename_key, {})
                
                # Position elements from bottom up
                current_y = img.height - margin
                
                # Add photographer info if available
                photographer_text = photographer_name or attribution.get('photographer', '')
                if photographer_text:
                    if photographer_font:
                        bbox = draw.textbbox((0, 0), f"Photo: {photographer_text}", font=photographer_font)
                        text_height = bbox[3] - bbox[1]
                    else:
                        text_height = 12
                    
                    current_y -= text_height
                    draw.text((margin, current_y), f"Photo: {photographer_text}", 
                             fill=(255, 255, 255, 200), font=photographer_font)
                    current_y -= 5  # Small gap
                
                # Add caption if available
                caption_text = attribution.get('caption', '')
                if caption_text:
                    # Word wrap caption if too long
                    max_caption_width = img.width - 2 * margin
                    if caption_font:
                        bbox = draw.textbbox((0, 0), caption_text, font=caption_font)
                        text_width = bbox[2] - bbox[0]
                        text_height = bbox[3] - bbox[1]
                    else:
                        text_width = len(caption_text) * 8
                        text_height = 14
                    
                    if text_width > max_caption_width:
                        # Simple word wrapping
                        lines = self._wrap_text(caption_text, max_caption_width, caption_font, draw)
                        
                        # Draw wrapped caption
                        for i, line in enumerate(reversed(lines)):
                            current_y -= text_height
                            draw.text((margin, current_y), line, 
                                     fill=(255, 255, 255, 220), font=caption_font)
                            if i < len(lines) - 1:
                                current_y -= 2  # Line spacing
                    else:
                        current_y -= text_height
                        draw.text((margin, current_y), caption_text, 
                                 fill=(255, 255, 255, 220), font=caption_font)
                    
                    current_y -= 8  # Gap before main watermark
                
                # Add main watermark text
                team_name = attribution.get('team_name', watermark_text)
                main_watermark = team_name or watermark_text
                
                if watermark_font:
                    bbox = draw.textbbox((0, 0), main_watermark, font=watermark_font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                else:
                    text_width = len(main_watermark) * 12
                    text_height = 18
                
                current_y -= text_height
                draw.text((margin, current_y), main_watermark, 
                         fill=(255, 255, 255, 255), font=watermark_font)
                
                # Add logo
                if logo_resized:
                    logo_x = img.width - logo_resized.width - margin
                    logo_y = img.height - logo_resized.height - margin
                    overlay.paste(logo_resized, (logo_x, logo_y), logo_resized)
                
                # Combine original image with overlay
                watermarked = Image.alpha_composite(img, overlay)
                
                # Convert back to RGB if needed for JPEG
                if output_path.lower().endswith(('.jpg', '.jpeg')):
                    watermarked = watermarked.convert('RGB')
                
                # Save the watermarked image
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                watermarked.save(output_path, quality=95, optimize=True)
                
                # Log the processing
                self.log_attribution(attribution_log_path, image_path, output_path, 
                                   attribution, photographer_name, subfolder_name, 
                                   original_size, watermarked.size)
                
                return True
                
        except Exception as e:
            print(f"Error processing {image_path}: {e}")
            return False
    
    def _wrap_text(self, text, max_width, font, draw):
        """Helper method to wrap text to fit within specified width"""
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            if font:
                test_bbox = draw.textbbox((0, 0), test_line, font=font)
                test_width = test_bbox[2] - test_bbox[0]
            else:
                test_width = len(test_line) * 8
            
            if test_width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
    
    def log_attribution(self, log_path, input_path, output_path, attribution, 
                       photographer_name, subfolder_name, original_size, final_size):
        """Log processing details to CSV file"""
        try:
            file_exists = os.path.exists(log_path)
            
            with open(log_path, 'a', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['timestamp', 'input_file', 'output_file', 'subfolder', 
                             'team_name', 'caption', 'photographer', 'original_size', 
                             'final_size', 'size_changed']
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                if not file_exists:
                    writer.writeheader()
                
                size_changed = original_size != final_size
                
                writer.writerow({
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'input_file': os.path.basename(input_path),
                    'output_file': os.path.basename(output_path),
                    'subfolder': subfolder_name or '',
                    'team_name': attribution.get('team_name', ''),
                    'caption': attribution.get('caption', ''),
                    'photographer': photographer_name or attribution.get('photographer', ''),
                    'original_size': f"{original_size[0]}x{original_size[1]}",
                    'final_size': f"{final_size[0]}x{final_size[1]}",
                    'size_changed': size_changed
                })
                
        except Exception as e:
            print(f"Error logging attribution: {e}")
    
    def process_directory(self, input_dir, output_dir, watermark_text, 
                         attribution_log_path, watermark_mode='normal'):
        """Process all images in a directory"""
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        
        if not input_path.exists():
            print(f"Input directory does not exist: {input_dir}")
            return 0
        
        processed_count = 0
        
        # Process files in root directory
        for file_path in input_path.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in self.supported_formats:
                output_file = output_path / file_path.name
                
                if self.add_watermark(str(file_path), str(output_file), watermark_text, 
                                    attribution_log_path, watermark_mode=watermark_mode):
                    processed_count += 1
                    print(f"Processed: {file_path.name}")
        
        # Process subdirectories
        for subdir in input_path.iterdir():
            if subdir.is_directory():
                sub_output_dir = output_path / subdir.name
                sub_output_dir.mkdir(parents=True, exist_ok=True)
                
                for file_path in subdir.iterdir():
                    if file_path.is_file() and file_path.suffix.lower() in self.supported_formats:
                        output_file = sub_output_dir / file_path.name
                        
                        if self.add_watermark(str(file_path), str(output_file), watermark_text, 
                                            attribution_log_path, subfolder_name=subdir.name,
                                            watermark_mode=watermark_mode):
                            processed_count += 1
                            print(f"Processed: {subdir.name}/{file_path.name}")
        
        return processed_count

    def get_supported_formats(self):
        """Return list of supported image formats"""
        return self.supported_formats
    
    def clear_attribution_data(self):
        """Clear loaded attribution data"""
        self.attribution_data.clear()
    
    def get_attribution_count(self):
        """Get count of loaded attribution entries"""
        return len(self.attribution_data)