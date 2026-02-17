#!/usr/bin/env python3

from PIL import Image


def calculate_gif_duration(image_path):
    """Calcula la duración total de un GIF en milisegundos"""
    try:
        with Image.open(image_path) as img:
            if not hasattr(img, 'n_frames') or img.n_frames <= 1:
                return 0

            total_duration = 0
            for frame in range(img.n_frames):
                img.seek(frame)
                frame_duration = img.info.get('duration', 100)
                total_duration += frame_duration

            return total_duration
    except:
        return 0
