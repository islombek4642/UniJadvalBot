import os
import sys
import subprocess
import venv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_venv(venv_dir=".venv"):
    """Creates a virtual environment if it doesn't exist."""
    if not os.path.exists(venv_dir):
        logger.info(f"Creating virtual environment in {venv_dir}...")
        venv.create(venv_dir, with_pip=True)
        logger.info("Virtual environment created.")
    else:
        logger.info("Virtual environment already exists.")

def get_python_executable(venv_dir=".venv"):
    """Returns the path to the python executable within the venv."""
    if sys.platform == "win32":
        return os.path.join(venv_dir, "Scripts", "python.exe")
    return os.path.join(venv_dir, "bin", "python")

def install_dependencies(python_exe, requirements_file="requirements.txt"):
    """Installs dependencies from requirements.txt."""
    if os.path.exists(requirements_file):
        logger.info("Installing dependencies...")
        subprocess.check_call([python_exe, "-m", "pip", "install", "-r", requirements_file])
        logger.info("Dependencies installed.")
    else:
        logger.warning(f"{requirements_file} not found. Skipping dependency installation.")

def start_bot(python_exe, main_script="main.py"):
    """Starts the bot."""
    if os.path.exists(main_script):
        logger.info(f"Starting the bot using {main_script}...")
        subprocess.check_call([python_exe, main_script])
    else:
        logger.error(f"{main_script} not found. Cannot start the bot.")

if __name__ == "__main__":
    VENV_NAME = ".venv"
    
    try:
        setup_venv(VENV_NAME)
        python_bin = get_python_executable(VENV_NAME)
        install_dependencies(python_bin)
        
        # Check for .env file
        if not os.path.exists(".env"):
            logger.warning(".env file not found! Please create it from .env.example before running.")
            if os.path.exists(".env.example"):
                import shutil
                shutil.copy(".env.example", ".env")
                logger.info("Created .env from .env.example. Please fill in your BOT_TOKEN.")
            sys.exit(1)

        start_bot(python_bin)
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        sys.exit(1)
