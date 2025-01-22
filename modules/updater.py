import subprocess
import json
from modules.logger_utils import setup_logger

logger = setup_logger()


def list_homebrew_upgrades():
    """
    Récupère la liste des mises à jour disponibles via Homebrew.
    Retourne une liste d'objets contenant :
    - name : Nom du package
    - current_version : Version actuelle
    - new_version : Nouvelle version
    """
    try:
        result = subprocess.run(
            ["brew", "outdated", "--json=v2"],
            capture_output=True,
            text=True,
            check=True
        )
        data = json.loads(result.stdout)
        upgrades = []

        for package in data.get("formulae", []):
            upgrades.append({
                "name": package["name"],
                "current_version": package["installed_versions"][0],
                "new_version": package["current_version"]
            })

        logger.info(f"{len(upgrades)} mises à jour disponibles via Homebrew.")
        return upgrades

    except subprocess.CalledProcessError as e:
        logger.error(f"Erreur lors de l'exécution de 'brew outdated' : {e}")
        raise RuntimeError(f"Erreur lors de la récupération des mises à jour Homebrew : {e}")

    except json.JSONDecodeError as e:
        logger.error(f"Erreur lors du parsing JSON de la sortie Homebrew : {e}")
        raise RuntimeError(f"Erreur de parsing JSON : {e}")


def update_package(package_name):
    """
    Met à jour un package spécifique via Homebrew.
    Retourne un tuple (success: bool, message: str).
    """
    try:
        subprocess.run(
            ["brew", "upgrade", package_name],
            check=True,
            capture_output=True,
            text=True
        )
        logger.info(f"{package_name} mis à jour avec succès.")
        return True, f"{package_name} mis à jour avec succès."

    except subprocess.CalledProcessError as e:
        logger.error(f"Erreur lors de la mise à jour de {package_name} : {e}")
        return False, f"Erreur lors de la mise à jour de {package_name} : {e}"


def update_all():
    """
    Met à jour tous les packages disponibles via Homebrew.
    Retourne un tuple (success: bool, message: str).
    """
    try:
        subprocess.run(
            ["brew", "upgrade"],
            check=True,
            capture_output=True,
            text=True
        )
        logger.info("Toutes les mises à jour Homebrew ont été appliquées.")
        return True, "Toutes les mises à jour Homebrew ont été appliquées."

    except subprocess.CalledProcessError as e:
        logger.error(f"Erreur lors de la mise à jour globale : {e}")
        return False, f"Erreur lors de la mise à jour globale : {e}"
