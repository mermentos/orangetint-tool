import cv2
import numpy as np
import os
import logging
from app import app

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

def remove_orange_tint(image):
    """
    Remove orange tint from image using LAB color space correction
    """
    try:
        # Convert to LAB color space
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)

        # Reduce warm tones (reduce 'b' channel mean to lower yellow/blue imbalance)
        b = cv2.subtract(b, np.full(b.shape, 10, dtype=b.dtype))

        # Merge and convert back to BGR
        corrected_lab = cv2.merge((l, a, b))
        corrected = cv2.cvtColor(corrected_lab, cv2.COLOR_LAB2BGR)

        return corrected
    except Exception as e:
        logging.error(f"Error in remove_orange_tint: {str(e)}")
        return None

def process_image(filename):
    """
    Process a single image to remove orange tint
    Returns the output filename if successful, None otherwise
    """
    try:
        # Input and output paths
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Create output filename with _fixed suffix
        name, ext = os.path.splitext(filename)
        output_filename = f"{name}_fixed.png"  # Always save as PNG for quality
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        
        # Read the image
        image = cv2.imread(input_path)
        if image is None:
            logging.error(f"Could not read image: {filename}")
            return None
        
        # Process the image
        processed_image = remove_orange_tint(image)
        if processed_image is None:
            logging.error(f"Failed to process image: {filename}")
            return None
        
        # Save the processed image
        success = cv2.imwrite(output_path, processed_image)
        if not success:
            logging.error(f"Failed to save processed image: {output_filename}")
            return None
        
        logging.info(f"Successfully processed {filename} -> {output_filename}")
        return output_filename
        
    except Exception as e:
        logging.error(f"Error processing {filename}: {str(e)}")
        return None

def get_image_info(filename):
    """
    Get basic information about an image file
    """
    try:
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image = cv2.imread(input_path)
        
        if image is None:
            return None
        
        height, width, channels = image.shape
        file_size = os.path.getsize(input_path)
        
        return {
            'width': width,
            'height': height,
            'channels': channels,
            'file_size': file_size
        }
    except Exception as e:
        logging.error(f"Error getting image info for {filename}: {str(e)}")
        return None
