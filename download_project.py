#!/usr/bin/env python3
"""
Script to download Fractalyx project from Replit to a local directory.

This script pulls the structure and files from the Replit workspace
and downloads them to the specified output directory.

Usage:
    python download_project.py /path/to/output/directory
"""

import os
import sys
import shutil
from pathlib import Path

# Define the source directories to copy
DIRECTORIES_TO_COPY = [
    "agent_system",
    "payment",
    "routes",
    "static",
    "templates",
    "uploads",
]

# Define individual files to copy
FILES_TO_COPY = [
    "app.py",
    "init_agents.py",
    "main.py",
    "models.py",
    ".gitignore",
    "README.md",
    "DEPLOYMENT.md",
]

def ensure_dir(directory):
    """Ensure a directory exists, creating it if necessary."""
    Path(directory).mkdir(parents=True, exist_ok=True)

def copy_file(src, dest):
    """Copy a file from source to destination."""
    try:
        shutil.copy2(src, dest)
        print(f"Copied: {src} -> {dest}")
    except FileNotFoundError:
        print(f"Warning: Could not copy {src} - file not found")
    except Exception as e:
        print(f"Error copying {src}: {e}")

def copy_directory(src, dest):
    """Copy a directory and its contents recursively."""
    try:
        if not os.path.exists(src):
            print(f"Warning: Source directory does not exist: {src}")
            return
            
        ensure_dir(dest)
        
        # Copy all files in the directory
        for item in os.listdir(src):
            s = os.path.join(src, item)
            d = os.path.join(dest, item)
            
            if os.path.isdir(s):
                copy_directory(s, d)
            else:
                copy_file(s, d)
                
        print(f"Copied directory: {src} -> {dest}")
    except Exception as e:
        print(f"Error copying directory {src}: {e}")

def create_directories(base_dir):
    """Create necessary directories in the destination."""
    # Create uploads directory with .gitkeep
    uploads_dir = os.path.join(base_dir, "uploads")
    ensure_dir(uploads_dir)
    
    # Create .gitkeep file in uploads directory
    with open(os.path.join(uploads_dir, ".gitkeep"), "w") as f:
        f.write("")

def create_requirements_file(dest_dir):
    """Create a requirements.txt file in the destination directory."""
    requirements = [
        "email-validator==2.1.0",
        "flask==3.0.0",
        "flask-login==0.6.3",
        "flask-sqlalchemy==3.1.1",
        "flask-wtf==1.2.1",
        "gunicorn==23.0.0",
        "psycopg2-binary==2.9.9",
        "pytest==7.4.3",
        "requests==2.31.0",
        "stripe==7.9.0",
        "werkzeug==3.0.1",
    ]
    
    with open(os.path.join(dest_dir, "requirements.txt"), "w") as f:
        f.write("\n".join(requirements))
    
    print(f"Created requirements.txt in {dest_dir}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python download_project.py /path/to/output/directory")
        sys.exit(1)
        
    output_dir = sys.argv[1]
    current_dir = os.getcwd()
    
    # Create the output directory if it doesn't exist
    ensure_dir(output_dir)
    
    # Copy directories
    for directory in DIRECTORIES_TO_COPY:
        src_dir = os.path.join(current_dir, directory)
        dest_dir = os.path.join(output_dir, directory)
        copy_directory(src_dir, dest_dir)
    
    # Copy individual files
    for file in FILES_TO_COPY:
        src_file = os.path.join(current_dir, file)
        dest_file = os.path.join(output_dir, file)
        copy_file(src_file, dest_file)
    
    # Create additional directories and files
    create_directories(output_dir)
    create_requirements_file(output_dir)
    
    print(f"\nProject files have been copied to {output_dir}")
    print("Remember to set up your environment variables as described in DEPLOYMENT.md")

if __name__ == "__main__":
    main()
