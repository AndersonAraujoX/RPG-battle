import os
from PIL import Image, ImageFilter, ImageChops, ImageMath, ImageDraw

def remove_background_and_defringe(image_path, output_path, bg_type="auto", tolerance=30, erode_pixels=1, feather_pixels=1, defringe_radius=3):
    img = Image.open(image_path).convert("RGBA")
    width, height = img.size
    
    # 1. Determine background color
    if bg_type == "auto":
        corners = [
            img.getpixel((0, 0)),
            img.getpixel((width - 1, 0)),
            img.getpixel((0, height - 1)),
            img.getpixel((width - 1, height - 1))
        ]
        avg_r = sum(c[0] for c in corners) // 4
        avg_g = sum(c[1] for c in corners) // 4
        avg_b = sum(c[2] for c in corners) // 4
        
        if avg_r > 200 and avg_g > 200 and avg_b > 200:
            bg_color = (255, 255, 255)
        else:
            bg_color = (0, 0, 0)
    elif bg_type == "white":
        bg_color = (255, 255, 255)
    else:
        bg_color = (0, 0, 0)

    # 2. Flood fill from corners to build alpha mask
    temp_img = img.copy()
    fill_color = (255, 0, 255, 255) # magenta
    
    corners_coords = [(0, 0), (width - 1, 0), (0, height - 1), (width - 1, height - 1)]
    for x, y in corners_coords:
        try:
            ImageDraw.floodfill(temp_img, (x, y), fill_color, thresh=tolerance)
        except Exception as e:
            print(f"Error floodfilling at ({x},{y}): {e}")
            
    # Alpha mask: 0 for background, 255 for foreground
    alpha_data = []
    for pixel in temp_img.getdata():
        if pixel == fill_color:
            alpha_data.append(0)
        else:
            alpha_data.append(255)
            
    alpha_mask = Image.new("L", (width, height))
    alpha_mask.putdata(alpha_data)
    
    # Keep a copy of original alpha for defringing boundary reference
    orig_alpha = alpha_mask.copy()
    
    # 3. Erode & Feather the alpha mask
    if erode_pixels > 0:
        filter_size = erode_pixels * 2 + 1
        alpha_mask = alpha_mask.filter(ImageFilter.MinFilter(filter_size))
        
    if feather_pixels > 0:
        alpha_mask = alpha_mask.filter(ImageFilter.GaussianBlur(feather_pixels))
        
    # 4. Defringe colors of RGB channels
    r, g, b, _ = img.split()
    
    if defringe_radius > 0:
        # Premultiply
        r_pre = ImageChops.multiply(r, orig_alpha)
        g_pre = ImageChops.multiply(g, orig_alpha)
        b_pre = ImageChops.multiply(b, orig_alpha)
        
        # Blur premultiplied colors and the reference alpha
        r_blur = r_pre.filter(ImageFilter.BoxBlur(defringe_radius))
        g_blur = g_pre.filter(ImageFilter.BoxBlur(defringe_radius))
        b_blur = b_pre.filter(ImageFilter.BoxBlur(defringe_radius))
        a_blur = orig_alpha.filter(ImageFilter.BoxBlur(defringe_radius))
        
        # Un-premultiply (divide by alpha blur) to extend color outward
        r_defringed = ImageMath.eval("convert(float(r) / (float(a)/255.0 + 0.01), 'L')", r=r_blur, a=a_blur)
        g_defringed = ImageMath.eval("convert(float(g) / (float(a)/255.0 + 0.01), 'L')", g=g_blur, a=a_blur)
        b_defringed = ImageMath.eval("convert(float(b) / (float(a)/255.0 + 0.01), 'L')", b=b_blur, a=a_blur)
        
        # Blend defringed color back with original color using the original alpha channel
        # Opaque pixels keep original color; edge/transparent pixels use defringed color
        r_final = Image.composite(r, r_defringed, orig_alpha)
        g_final = Image.composite(g, g_defringed, orig_alpha)
        b_final = Image.composite(b, b_defringed, orig_alpha)
    else:
        r_final, g_final, b_final = r, g, b
        
    # Merge back RGB and the new eroded/feathered alpha mask
    final_img = Image.merge("RGBA", (r_final, g_final, b_final, alpha_mask))
    
    # Save the output
    final_img.save(output_path, "PNG")
    print(f"Saved defringed image to: {output_path}")

if __name__ == "__main__":
    path = '/home/anderson/Documents/projeto/RPG-battle/assets/images/characters/animation'
    os.makedirs('/home/anderson/Documents/projeto/RPG-battle/assets/images/characters/animation/processed', exist_ok=True)
    
    # Test on the images with defringing
    remove_background_and_defringe(
        os.path.join(path, "Aquele_anima.png"),
        os.path.join(path, "processed", "Aquele_anima_clean.png"),
        bg_type="white",
        tolerance=40,
        erode_pixels=1,
        feather_pixels=1,
        defringe_radius=3
    )
    
    remove_background_and_defringe(
        os.path.join(path, "Pasted image (2).png"),
        os.path.join(path, "processed", "Pasted_image_2_clean.png"),
        bg_type="white",
        tolerance=40,
        erode_pixels=1,
        feather_pixels=1,
        defringe_radius=3
    )
    
    remove_background_and_defringe(
        os.path.join(path, "Pasted image.png"),
        os.path.join(path, "processed", "Pasted_image_clean.png"),
        bg_type="black",
        tolerance=30,
        erode_pixels=1,
        feather_pixels=1,
        defringe_radius=3
    )
