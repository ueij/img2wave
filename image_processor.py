# image_processor.py

import numpy as np
from PIL import Image

def get_image_boundaries(image_path: str, vertical_resolution: int = 512):
    fixed_width = 2048
    
    with Image.open(image_path) as img:
        img_gray = img.convert('L').resize(
            (fixed_width, vertical_resolution), 
            resample=Image.Resampling.BILINEAR
        )
        img_array = np.array(img_gray)
    
    binary_grid = img_array < 128
    center = float(vertical_resolution) / 2.0
    
    has_active = np.any(binary_grid, axis=0)
    first_y = np.argmax(binary_grid, axis=0)
    last_y = (vertical_resolution - 1) - np.argmax(binary_grid[::-1, :], axis=0)
    
    top_envelope = np.where(has_active, 1.0 - (first_y / center), 0.0).astype(np.float32)
    bottom_envelope = np.where(has_active, 1.0 - (last_y / center), 0.0).astype(np.float32)
    
    return top_envelope, bottom_envelope