# image_processor.py

import os
import numpy as np
from PIL import Image

def get_image_boundaries(
    image_path: str, 
    width: int = 2048,
    height: int = 512,
    threshold: int = 128,
    grayscale_method: str = "luminance_601",
    invert: bool = False,
    debug_path: str = None
):
    clamped_threshold = max(0, min(255, int(threshold)))
    
    with Image.open(image_path) as img:
        if img.mode != 'RGB':
            img = img.convert('RGB')
            
        img_resized = img.resize(
            (width, height), 
            resample=Image.Resampling.BILINEAR
        )
        
        if grayscale_method == "luminance_601":
            img_gray = np.array(img_resized.convert('L'))
        else:
            img_array = np.array(img_resized)
            if grayscale_method == "luminance_709":
                weights = np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
                img_gray = np.dot(img_array.astype(np.float32), weights).astype(np.uint8)
            elif grayscale_method == "average":
                img_gray = img_array.mean(axis=2, dtype=np.float32).astype(np.uint8)
            elif grayscale_method == "lightness":
                max_c = np.max(img_array, axis=2).astype(np.float32)
                min_c = np.min(img_array, axis=2).astype(np.float32)
                img_gray = ((max_c + min_c) * 0.5).astype(np.uint8)
            else:
                weights = np.array([0.299, 0.587, 0.114], dtype=np.float32)
                img_gray = np.dot(img_array.astype(np.float32), weights).astype(np.uint8)

    if invert:
        binary_grid = img_gray >= clamped_threshold
    else:
        binary_grid = img_gray < clamped_threshold
    
    scaling_factor = 2.0 / (height - 1)
    has_active = np.any(binary_grid, axis=0)
    first_y = np.argmax(binary_grid, axis=0)
    last_y = (height - 1) - np.argmax(binary_grid[::-1, :], axis=0)
    
    top_env = np.where(has_active, 1.0 - (first_y * scaling_factor), 0.0).astype(np.float32)
    bottom_env = np.where(has_active, 1.0 - (last_y * scaling_factor), 0.0).astype(np.float32)
    
    if debug_path:
        base, ext = os.path.splitext(debug_path)
        bin_path = f"{base}_binarized{ext}"
        fill_path = f"{base}_filled{ext}"
        
        debug_bin = (~binary_grid).astype(np.uint8) * 255
        Image.fromarray(debug_bin).save(bin_path)
        print(f"Binarized debug image saved to: {bin_path}")
        
        r_indices = np.arange(height)[:, None]
        filled_grid = has_active & (r_indices >= first_y) & (r_indices <= last_y)
        
        debug_fill = (~filled_grid).astype(np.uint8) * 255
        Image.fromarray(debug_fill).save(fill_path)
        print(f"Filled-in boundary debug image saved to: {fill_path}")
        
    return top_env, bottom_env