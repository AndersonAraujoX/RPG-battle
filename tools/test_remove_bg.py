import os
from PIL import Image, ImageFilter, ImageDraw

def remove_background_and_halo(image_path, output_path, bg_type="auto", tolerance=30, erode_pixels=1, feather_pixels=1):
    # Load image and convert to RGBA
    img = Image.open(image_path).convert("RGBA")
    width, height = img.size
    
    # 1. Determine background color if auto
    if bg_type == "auto":
        # Sample the 4 corners
        corners = [
            img.getpixel((0, 0)),
            img.getpixel((width - 1, 0)),
            img.getpixel((0, height - 1)),
            img.getpixel((width - 1, height - 1))
        ]
        # Average the corner colors
        avg_r = sum(c[0] for c in corners) // 4
        avg_g = sum(c[1] for c in corners) // 4
        avg_b = sum(c[2] for c in corners) // 4
        
        if avg_r > 200 and avg_g > 200 and avg_b > 200:
            bg_color = (255, 255, 255)
            print(f"{os.path.basename(image_path)}: Detected WHITE background (avg corner: {avg_r}, {avg_g}, {avg_b})")
        else:
            bg_color = (0, 0, 0)
            print(f"{os.path.basename(image_path)}: Detected BLACK/DARK background (avg corner: {avg_r}, {avg_g}, {avg_b})")
    elif bg_type == "white":
        bg_color = (255, 255, 255)
    else:
        bg_color = (0, 0, 0)

    # 2. Create the initial mask
    # We will do a flood fill from the corners using PIL's ImageDraw.floodfill.
    # To do this, we create a temporary grayscale image where background pixels are white (255) and others are black (0).
    # Then we floodfill from the corners to find the contiguous background.
    
    # We start by calculating color distance to the background color
    bg_r, bg_g, bg_b = bg_color[:3]
    
    # Create a mask of pixels that match the background color within tolerance
    mask_data = []
    for pixel in img.getdata():
        r, g, b, a = pixel
        dist = ((r - bg_r)**2 + (g - bg_g)**2 + (b - bg_b)**2)**0.5
        if dist <= tolerance:
            mask_data.append(255) # background candidate
        else:
            mask_data.append(0)   # foreground
            
    mask = Image.new("L", (width, height))
    mask.putdata(mask_data)
    
    # To make it contiguous (flood fill), we can flood fill with a different value (e.g. 128) starting from corners.
    # Let's floodfill from (0,0), (width-1, 0), (0, height-1), (width-1, height-1)
    # But floodfill only fills contiguous pixels of the same value. In our mask, candidates are 255.
    # So we floodfill value 255 starting from corners.
    # Wait, if the corner itself is not 255 (e.g. due to tolerance, though usually it is), we should make sure we start from a background pixel.
    # A cleaner way is to create an image of the background and flood fill it.
    # Let's just create a binary mask of background by flood filling the original image!
    # PIL's floodfill can fill with tolerance.
    # Let's make a copy of the image and flood fill it with a special color, say (255, 0, 255) (magenta), starting from corners.
    temp_img = img.copy()
    fill_color = (255, 0, 255, 255)
    
    # Flood fill from corners
    corners_coords = [(0, 0), (width - 1, 0), (0, height - 1), (width - 1, height - 1)]
    for x, y in corners_coords:
        try:
            ImageDraw.floodfill(temp_img, (x, y), fill_color, thresh=tolerance)
        except Exception as e:
            print(f"Floodfill error at ({x},{y}): {e}")
            
    # Now, any pixel that has the fill_color in temp_img is part of the background.
    # Let's build the alpha mask from this: 0 for background (magenta), 255 for foreground (others).
    alpha_data = []
    for pixel in temp_img.getdata():
        if pixel == fill_color:
            alpha_data.append(0)
        else:
            alpha_data.append(255)
            
    alpha_mask = Image.new("L", (width, height))
    alpha_mask.putdata(alpha_data)
    
    # 3. Remove the halo (Erosion)
    # To remove the halo, we want to shrink the foreground mask (erode the white area).
    # In PIL, we can use MinFilter. MinFilter(3) erodes by 1 pixel. MinFilter(5) erodes by 2 pixels.
    if erode_pixels > 0:
        filter_size = erode_pixels * 2 + 1
        alpha_mask = alpha_mask.filter(ImageFilter.MinFilter(filter_size))
        
    # 4. Smooth the edges (Feathering)
    # We can apply a Gaussian blur to the mask to feather the edges.
    if feather_pixels > 0:
        alpha_mask = alpha_mask.filter(ImageFilter.GaussianBlur(feather_pixels))
        
    # 5. Apply the alpha mask back to the image
    r, g, b, _ = img.split()
    final_img = Image.merge("RGBA", (r, g, b, alpha_mask))
    
    # Save the result
    final_img.save(output_path, "PNG")
    print(f"Saved: {output_path}")

if __name__ == "__main__":
    path = '/home/anderson/Documents/projeto/RPG-battle/assets/images/characters/animation'
    os.makedirs('/home/anderson/Documents/projeto/RPG-battle/assets/images/characters/animation/processed', exist_ok=True)
    
    # Test on the images
    remove_background_and_halo(
        os.path.join(path, "Aquele_anima.png"),
        os.path.join(path, "processed", "Aquele_anima_clean.png"),
        bg_type="white",
        tolerance=40,
        erode_pixels=1,
        feather_pixels=1
    )
    
    remove_background_and_halo(
        os.path.join(path, "Pasted image (2).png"),
        os.path.join(path, "processed", "Pasted_image_2_clean.png"),
        bg_type="white",
        tolerance=40,
        erode_pixels=1,
        feather_pixels=1
    )
    
    remove_background_and_halo(
        os.path.join(path, "Pasted image.png"),
        os.path.join(path, "processed", "Pasted_image_clean.png"),
        bg_type="black",
        tolerance=30,
        erode_pixels=1,
        feather_pixels=1
    )
