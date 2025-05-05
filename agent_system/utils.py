import logging
import os
import base64
import re
from typing import Optional, Dict, List, Any
from datetime import datetime
import random
import string

logger = logging.getLogger(__name__)


def generate_unique_id(prefix: str = "") -> str:
    """
    Generate a unique ID with an optional prefix.
    
    Args:
        prefix (str): An optional prefix for the ID
        
    Returns:
        str: A unique ID
    """
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_str = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
    return f"{prefix}{timestamp}{random_str}"


def save_uploaded_image(image_data: str, upload_dir: str = "uploads") -> Optional[str]:
    """
    Save an uploaded image and return the path.
    
    Args:
        image_data (str): Base64-encoded image data
        upload_dir (str): Directory to save the image in
        
    Returns:
        Optional[str]: Path to the saved image, or None if saving failed
    """
    try:
        # Create the upload directory if it doesn't exist
        os.makedirs(upload_dir, exist_ok=True)
        
        # Extract the base64 data
        if "base64," in image_data:
            image_data = image_data.split("base64,")[1]
        
        # Generate a filename
        filename = f"{generate_unique_id('img_')}.jpg"
        filepath = os.path.join(upload_dir, filename)
        
        # Decode and save the image
        with open(filepath, "wb") as f:
            f.write(base64.b64decode(image_data))
        
        logger.info(f"Saved uploaded image to {filepath}")
        return filepath
        
    except Exception as e:
        logger.exception(f"Error saving uploaded image: {str(e)}")
        return None


def extract_structured_data(text: str) -> Dict[str, Any]:
    """
    Extract structured data from text, looking for key-value pairs.
    
    Args:
        text (str): The text to parse
        
    Returns:
        Dict[str, Any]: Extracted data
    """
    data = {}
    
    # Look for key-value pairs in the format "Key: Value"
    pattern = r"([A-Za-z\s]+):\s*(.+?)(?=\n[A-Za-z\s]+:|$)"
    matches = re.findall(pattern, text, re.DOTALL)
    
    for key, value in matches:
        key = key.strip().lower().replace(" ", "_")
        value = value.strip()
        data[key] = value
    
    return data


def format_timestamp(timestamp: datetime) -> str:
    """
    Format a timestamp for display.
    
    Args:
        timestamp (datetime): The timestamp to format
        
    Returns:
        str: The formatted timestamp
    """
    return timestamp.strftime("%Y-%m-%d %H:%M:%S")


def parse_priority(priority_str: str) -> str:
    """
    Parse a priority string into a standardized format.
    
    Args:
        priority_str (str): The priority string
        
    Returns:
        str: Standardized priority (HIGH, MEDIUM, LOW, CRITICAL)
    """
    priority_str = priority_str.upper().strip()
    
    if priority_str in ["HIGH", "H"]:
        return "HIGH"
    elif priority_str in ["MEDIUM", "MED", "M"]:
        return "MEDIUM"
    elif priority_str in ["LOW", "L"]:
        return "LOW"
    elif priority_str in ["CRITICAL", "CRIT", "C"]:
        return "CRITICAL"
    else:
        # Default to medium
        return "MEDIUM"
