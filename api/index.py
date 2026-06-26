import sys
import os

# Add root folder to sys.path so we can import app.py correctly on Vercel
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import app
