import sys
import os

# Add your project directory to the sys.path
# Replace 'YOUR_PYTHONANYWHERE_USERNAME' with your actual PythonAnywhere username.
project_home = '/home/YOUR_PYTHONANYWHERE_USERNAME/Life-FLow'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set the working directory to load .env correctly
os.chdir(project_home)

# Import the Flask app object as 'application' for PythonAnywhere
from app import app as application
