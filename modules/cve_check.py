import requests
import time
import json
from dotenv import load_dotenv
import os
from modules.logger_utils import setup_logger

# Configuration du logger
logger = setup_logger()

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# Récupérer la clé API depuis le fichier .env
VULNERS_API_URL = "https://vulners.com/api/v3/search/lucene/"
VULNERS_API_KEY = os.getenv("VULNERS_API_KEY")

if not VULNERS_API_KEY:
    raise ValueError("La clé API Vulners n'est pas définie. Assurez-vous que le fichier .env est configuré.")

# Drapeau global pour arrêter les requêtes en cas d'erreur API
api_available = True

# Cache pour limiter les appels répétitifs
cve_cache = {}

def write_json_log(data, log_file="cve_analysis.log"):
    """
    Écrit les informations de CVE dans un fichier log au format JSON.
    """
    with open(log_file, "a") as file:
        json.dump(data, file, indent=4)
        file.write("\n")  # Ajouter une nouvelle ligne pour chaque entrée

def call_vulners_api(query):
    """
    Appelle l'API Vulners avec gestion des erreurs et des quotas.
    """
    headers = {
        "Content-Type": "application/json",
        "X-Api-Key": VULNERS_API_KEY
    }
    payload = {
        "query": query,
        "type": "cve"
    }

    try:
        logger.info(f"Appel API Vulners avec la requête : {payload}")
        response = requests.post(VULNERS_API_URL, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        logger.info(f"Réponse API reçue avec succès pour la requête : {query}")
        return response.json()
    except requests.exceptions.HTTPError as e:
        logger.error(f"Erreur HTTP : {e}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Erreur de connexion à l'API : {e}")
    return None

def get_cve_for_version(vendor: str, product: str, version: str):
    """
    Interroge l'API Vulners pour récupérer les CVE associées à une version spécifique.
    Retourne une liste ou un message d'erreur simplifié si l'API échoue.
    """
    global api_available

    # Si l'API est déjà marquée comme indisponible, retournez directement
    if not api_available:
        logger.warning("L'API Vulners est indisponible, arrêt des requêtes.")
        return "api cve pb"

    cache_key = f"{vendor}-{product}-{version}"
    if cache_key in cve_cache:
        logger.info(f"Utilisation du cache pour {cache_key}")
        return cve_cache[cache_key]

    query = f"{vendor} {product} {version}"
    data = call_vulners_api(query)

    if not data or data.get("result") != "OK":
        logger.warning(f"Problème avec les résultats de l'API pour {query}.")
        return "api cve pb"

    cve_items = data.get("data", {}).get("search", [])
    results = []

    for item in cve_items:
        source = item.get("_source", {})
        cve_id = source.get("id", "Unknown")
        description = source.get("description", "Aucune description.")
        cvss3 = source.get("cvss", {}).get("score", None)
        url = source.get("vhref", "")

        results.append({
            "id": cve_id,
            "score": cvss3,
            "description": description,
            "url": url
        })

    # Stocker les résultats dans le cache
    cve_cache[cache_key] = results

    # Log les résultats dans un fichier JSON
    log_data = {
        "vendor": vendor,
        "product": product,
        "version": version,
        "cve_count": len(results),
        "cve_details": results
    }
    write_json_log(log_data)

    logger.info(f"Nombre de CVE récupérées pour {query} : {len(results)}")
    time.sleep(1)  # Pause entre les appels API
    return results

def analyze_cve(current_version, new_version, vendor="apple", product="macos"):
    """
    Compare les CVE entre l'ancienne version et la nouvelle version.
    Retourne un statut simplifié si l'API échoue.
    """
    cve_current = get_cve_for_version(vendor, product, current_version)
    cve_new = get_cve_for_version(vendor, product, new_version)

    # Si une des réponses est un problème d'API, retournez un statut générique
    if cve_current == "api cve pb" or cve_new == "api cve pb":
        return "api cve pb", [], []

    # Déterminer si la mise à jour est "sûre"
    status = "sûr" if len(cve_new) < len(cve_current) else "pas sûr"

    # Log des comparaisons
    comparison_log = {
        "vendor": vendor,
        "product": product,
        "current_version": current_version,
        "new_version": new_version,
        "status": status,
        "cve_current": cve_current,
        "cve_new": cve_new
    }
    write_json_log(comparison_log)

    return status, cve_current, cve_new

# Exemple d'utilisation
if __name__ == "__main__":
    vendor = "mysql"
    product = "mysql"
    current_version = "8.0.29"
    new_version = "8.0.30"

    status, cve_current, cve_new = analyze_cve(current_version, new_version, vendor, product)

    if status == "api cve pb":
        print("Problème avec l'API Vulners. Impossible de récupérer les informations.")
    else:
        print(f"Comparaison des CVE pour {product} :")
        print(f"Statut de la mise à jour : {status}")
        print(f"CVEs dans la version actuelle ({current_version}):")
        for cve in cve_current:
            print(f"- {cve['id']}: {cve['description']} (Score: {cve['score']})")
        print(f"CVEs dans la nouvelle version ({new_version}):")
        for cve in cve_new:
            print(f"- {cve['id']}: {cve['description']} (Score: {cve['score']})")
