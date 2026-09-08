import os
from PIL import Image, ImageDraw, ImageFilter
import numpy as np

def generate_icons(src_path: str, output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    
    img = Image.open(src_path).convert('RGBA')
    arr = np.array(img)
    
    # -------------------------------------------------------------
    # 1. LOGO FULL (Trimmed to pill bounds with clean transparent margin)
    # -------------------------------------------------------------
    pill_bbox = img.getbbox()
    logo_full = img.crop(pill_bbox)
    logo_full_path = os.path.join(output_dir, 'logo_full.png')
    logo_full.save(logo_full_path, 'PNG', optimize=True)
    print(f"[OK] Saved full logo: {logo_full_path} ({logo_full.size})")

    # -------------------------------------------------------------
    # 2. EMBLEM (Isolated Triangle on Transparent Background)
    # -------------------------------------------------------------
    # Triangle region in original image
    sub_arr = arr[104:288, 98:295].copy()
    bg = np.array([2, 28, 56])  # Background color inside the pill
    diff = np.sqrt(np.sum((sub_arr[:, :, :3].astype(float) - bg.astype(float))**2, axis=2))
    
    # High-quality anti-aliased alpha threshold
    alpha = np.clip((diff - 6.0) / 22.0 * 255.0, 0, 255).astype(np.uint8)
    sub_arr[:, :, 3] = alpha
    
    emblem_raw = Image.fromarray(sub_arr)
    emblem_trimmed = emblem_raw.crop(emblem_raw.getbbox())
    
    # Create 512x512 centered transparent emblem
    emblem_512 = Image.new('RGBA', (512, 512), (0, 0, 0, 0))
    # Scale emblem to fit ~380x380
    target_w, target_h = 390, int(390 * (emblem_trimmed.height / emblem_trimmed.width))
    emblem_scaled = emblem_trimmed.resize((target_w, target_h), Image.Resampling.LANCZOS)
    
    pos_x = (512 - target_w) // 2
    pos_y = (512 - target_h) // 2
    emblem_512.paste(emblem_scaled, (pos_x, pos_y), emblem_scaled)
    
    logo_symbol_path = os.path.join(output_dir, 'logo_symbol.png')
    emblem_512.save(logo_symbol_path, 'PNG', optimize=True)
    print(f"[OK] Saved logo symbol: {logo_symbol_path} ({emblem_512.size})")

    # -------------------------------------------------------------
    # 3. APP ICON (Modern Squircle / Rounded Square Badge)
    # -------------------------------------------------------------
    # Size 512x512
    size = 512
    icon_canvas = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    
    # Create squircle rounded rectangle mask
    # Radius = 110 px for 512x512 (iOS / macOS / modern Windows 11 style)
    corner_radius = 112
    mask = Image.new('L', (size, size), 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.rounded_rectangle([(16, 16), (size - 16, size - 16)], radius=corner_radius, fill=255)
    
    # Create background with subtle dark-navy gradient matching brand
    bg_canvas = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    bg_draw = ImageDraw.Draw(bg_canvas)
    
    # Subtle gradient from top #042142 to bottom #021226
    top_color = np.array([4, 33, 66], dtype=float)
    bot_color = np.array([2, 18, 38], dtype=float)
    
    grad_arr = np.zeros((size, size, 4), dtype=np.uint8)
    for y in range(size):
        t = y / float(size)
        c = (1.0 - t) * top_color + t * bot_color
        grad_arr[y, :, 0] = int(c[0])
        grad_arr[y, :, 1] = int(c[1])
        grad_arr[y, :, 2] = int(c[2])
        grad_arr[y, :, 3] = 255
        
    bg_grad = Image.fromarray(grad_arr)
    
    # Add subtle inner border
    border_mask = Image.new('L', (size, size), 0)
    draw_border = ImageDraw.Draw(border_mask)
    draw_border.rounded_rectangle([(16, 16), (size - 16, size - 16)], radius=corner_radius, outline=255, width=3)
    
    # Paste background through mask
    icon_canvas.paste(bg_grad, (0, 0), mask)
    
    # Apply subtle border highlight (light cyan / steel blue stroke)
    border_layer = Image.new('RGBA', (size, size), (56, 189, 248, 55))
    icon_canvas.paste(border_layer, (0, 0), border_mask)
    
    # Center the emblem inside the squircle (with slight vertical visual balance)
    emblem_icon_w = 320
    emblem_icon_h = int(emblem_icon_w * (emblem_trimmed.height / emblem_trimmed.width))
    emblem_for_icon = emblem_trimmed.resize((emblem_icon_w, emblem_icon_h), Image.Resampling.LANCZOS)
    
    # Subtle drop shadow behind emblem for depth
    shadow_mask = emblem_for_icon.split()[3]
    shadow_layer = Image.new('RGBA', (emblem_icon_w + 40, emblem_icon_h + 40), (0, 0, 0, 0))
    shadow_canvas = Image.new('RGBA', (emblem_icon_w, emblem_icon_h), (0, 0, 0, 160))
    shadow_layer.paste(shadow_canvas, (20, 24), shadow_mask)
    shadow_blur = shadow_layer.filter(ImageFilter.GaussianBlur(12))
    
    ex = (size - emblem_icon_w) // 2
    ey = (size - emblem_icon_h) // 2 - 4  # Slight optical centering
    
    icon_canvas.paste(shadow_blur, (ex - 20, ey - 20), shadow_blur)
    icon_canvas.paste(emblem_for_icon, (ex, ey), emblem_for_icon)
    
    # Save icon.png (512x512)
    icon_512_path = os.path.join(output_dir, 'icon.png')
    icon_canvas.save(icon_512_path, 'PNG', optimize=True)
    print(f"[OK] Saved app icon PNG: {icon_512_path} (512x512)")
    
    # Save icon.ico (Multi-resolution Windows Icon)
    icon_ico_path = os.path.join(output_dir, 'icon.ico')
    icon_sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    icon_canvas.save(icon_ico_path, format='ICO', sizes=icon_sizes)
    print(f"[OK] Saved Windows icon ICO: {icon_ico_path} (multi-size: {icon_sizes})")
    
    # -------------------------------------------------------------
    # 4. TRANSPARENT EMBLEM ICO (Alternative pure emblem icon)
    # -------------------------------------------------------------
    emblem_ico_path = os.path.join(output_dir, 'icon_emblem.ico')
    emblem_512.save(emblem_ico_path, format='ICO', sizes=icon_sizes)
    print(f"[OK] Saved pure emblem ICO: {emblem_ico_path}")

if __name__ == '__main__':
    src = r'C:\Users\dalis\.gemini\antigravity-ide\brain\32780f21-1885-4a33-98c5-affa5a5508b2\.user_uploaded\media_1788812941394.png'
    out = r'e:\www\DaliSports-Pipeline\desktop\public'
    generate_icons(src, out)
