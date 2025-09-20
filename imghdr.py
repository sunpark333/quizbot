"""
Custom imghdr module for Python 3.13 compatibility
"""
import os
import struct
from PIL import Image

def what(file, h=None):
    """
    Determine the type of an image file
    """
    if h is None:
        if isinstance(file, str):
            with open(file, 'rb') as f:
                h = f.read(32)
        else:
            location = file.tell()
            h = file.read(32)
            file.seek(location)
    
    if not h:
        return None
    
    # Check for common image formats
    if h.startswith(b'\xff\xd8\xff'):
        return 'jpeg'
    elif h.startswith(b'\x89PNG\r\n\x1a\n'):
        return 'png'
    elif h.startswith(b'GIF87a') or h.startswith(b'GIF89a'):
        return 'gif'
    elif h.startswith(b'BM'):
        return 'bmp'
    elif h.startswith(b'II*\x00') or h.startswith(b'MM\x00*'):
        return 'tiff'
    elif h.startswith(b'RIFF') and h[8:12] == b'WEBP':
        return 'webp'
    
    # Try using Pillow for more formats
    try:
        if isinstance(file, str):
            with Image.open(file) as img:
                return img.format.lower()
        else:
            location = file.tell()
            file.seek(0)
            with Image.open(file) as img:
                result = img.format.lower()
                file.seek(location)
                return result
    except:
        return None
