import os
from PIL import Image, ImageFilter, ImageChops, ImageMath, ImageDraw

def detect_background_color(img):
    width, height = img.size
    # Sample the 4 corners
    corners = [
        img.getpixel((0, 0)),
        img.getpixel((width - 1, 0)),
        img.getpixel((0, height - 1)),
        img.getpixel((width - 1, height - 1))
    ]
    avg_r = sum(c[0] for c in corners) // 4
    avg_g = sum(c[1] for c in corners) // 4
    avg_b = sum(c[2] for c in corners) // 4
    
    # If the corners are bright, assume white background
    if avg_r > 200 and avg_g > 200 and avg_b > 200:
        return (255, 255, 255), "white"
    else:
        return (0, 0, 0), "black"

def process_image(img, bg_type="auto", tolerance=30, erode_pixels=1, feather_pixels=1.0, defringe_radius=3, mode="floodfill"):
    """
    Removes background and halo from a PIL Image.
    
    Parameters:
        img (PIL.Image): The input image.
        bg_type (str): "auto", "white", or "black".
        tolerance (int): Threshold for matching background color (0-255).
        erode_pixels (int): Amount of pixels to erode the alpha mask (0-10).
        feather_pixels (float): Gaussian blur radius for alpha mask edges (0.0 - 10.0).
        defringe_radius (int): Radius for color bleeding/defringing (0-10).
        mode (str): "floodfill" (contiguous from corners) or "range" (global color range).
        
    Returns:
        PIL.Image: The processed RGBA image.
        tuple: The detected background RGB color.
    """
    img = img.convert("RGBA")
    width, height = img.size
    
    # 1. Determine background color
    if bg_type == "auto":
        bg_color, detected_name = detect_background_color(img)
    elif bg_type == "white":
        bg_color = (255, 255, 255)
    else:
        bg_color = (0, 0, 0)
        
    # 2. Build alpha mask
    if mode == "floodfill":
        # Create a copy and floodfill from corners with a placeholder color (magenta)
        temp_img = img.copy()
        fill_color = (255, 0, 255, 255) # magenta
        
        corners_coords = [(0, 0), (width - 1, 0), (0, height - 1), (width - 1, height - 1)]
        for x, y in corners_coords:
            try:
                ImageDraw.floodfill(temp_img, (x, y), fill_color, thresh=tolerance)
            except Exception as e:
                pass
                
        # Create alpha mask from fill_color
        alpha_data = []
        for pixel in temp_img.getdata():
            if pixel == fill_color:
                alpha_data.append(0)
            else:
                alpha_data.append(255)
    else:
        # Global color range mode
        bg_r, bg_g, bg_b = bg_color[:3]
        alpha_data = []
        for pixel in img.getdata():
            r, g, b, a = pixel
            dist = ((r - bg_r)**2 + (g - bg_g)**2 + (b - bg_b)**2)**0.5
            if dist <= tolerance:
                alpha_data.append(0)
            else:
                alpha_data.append(255)
                
    alpha_mask = Image.new("L", (width, height))
    alpha_mask.putdata(alpha_data)
    
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
        # Premultiply RGB by the original alpha
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
        r_final = Image.composite(r, r_defringed, orig_alpha)
        g_final = Image.composite(g, g_defringed, orig_alpha)
        b_final = Image.composite(b, b_defringed, orig_alpha)
    else:
        r_final, g_final, b_final = r, g, b
        
    # Merge back RGB and the new eroded/feathered alpha mask
    final_img = Image.merge("RGBA", (r_final, g_final, b_final, alpha_mask))
    
    return final_img, bg_color
