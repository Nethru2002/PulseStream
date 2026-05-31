import os

def format_time(seconds):
    """Converts seconds to MM:SS format"""
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes:02d}:{seconds:02d}"

def ensure_dir(directory):
    """Creates a directory if it doesn't exist"""
    if not os.path.exists(directory):
        os.makedirs(directory)

def get_resource_path(relative_path):
    """Helper to find files relative to the project root"""
    base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)