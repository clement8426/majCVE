import platform
import subprocess
import shutil
from modules.logger_utils import setup_logger

logger = setup_logger()

def is_macos():
    return platform.system().lower() == "darwin", "macOS détecté."

def check_brew():
    return shutil.which("brew") is not None, "Homebrew est installé."

def initial_check():
    os_ok, os_message = is_macos()
    if not os_ok:
        return False, os_message
    brew_ok, brew_message = check_brew()
    if not brew_ok:
        return False, "Veuillez installer Homebrew."
    return True, "Environnement prêt pour les mises à jour."
