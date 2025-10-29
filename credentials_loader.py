import os
import json
import logging

logger = logging.getLogger(__name__)

def load_credentials():
    """
    Load credentials from JSON file instead of .env file.
    
    Checks multiple possible locations:
    1. C:/tmp/sap_login/credential.json (Windows)
    2. /tmp/sap_login/credential.json (Linux)
    3. Falls back to environment variables if JSON file not found
    
    Returns:
        dict: Dictionary of credentials
    """
    credentials = {}
    
    # Possible JSON file locations
    json_paths = [
        r"C:\tmp\sap_login\credential.json",  # Windows path
        "/tmp/sap_login/credential.json",     # Linux path
        os.path.join(os.path.expanduser("~"), "tmp", "sap_login", "credential.json")  # User home directory
    ]
    
    # Try to load from JSON file
    json_loaded = False
    for json_path in json_paths:
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r') as f:
                    credentials = json.load(f)
                logger.info(f"✅ Credentials loaded from JSON file: {json_path}")
                json_loaded = True
                break
            except Exception as e:
                logger.warning(f"⚠️ Failed to load credentials from {json_path}: {e}")
    
    if not json_loaded:
        logger.warning("⚠️ No credential.json file found in any location, falling back to environment variables")
        
        # Fallback to environment variables
        credentials = {
            "SAP_B1_SERVER": os.environ.get("SAP_B1_SERVER", ""),
            "SAP_B1_USERNAME": os.environ.get("SAP_B1_USERNAME", ""),
            "SAP_B1_PASSWORD": os.environ.get("SAP_B1_PASSWORD", ""),
            "SAP_B1_COMPANY_DB": os.environ.get("SAP_B1_COMPANY_DB", ""),
            "MYSQL_HOST": os.environ.get("MYSQL_HOST", ""),
            "MYSQL_PORT": os.environ.get("MYSQL_PORT", ""),
            "MYSQL_USER": os.environ.get("MYSQL_USER", ""),
            "MYSQL_PASSWORD": os.environ.get("MYSQL_PASSWORD", ""),
            "MYSQL_DATABASE": os.environ.get("MYSQL_DATABASE", ""),
            "DATABASE_URL": os.environ.get("DATABASE_URL", ""),
            "SESSION_SECRET": os.environ.get("SESSION_SECRET", "")
        }
    
    # Set credentials as environment variables for backward compatibility
    for key, value in credentials.items():
        if value:  # Only set if value exists
            os.environ[key] = str(value)
    
    return credentials


def get_credential(key, default=None):
    """
    Get a specific credential value.
    
    Args:
        key (str): Credential key name
        default: Default value if credential not found
        
    Returns:
        str: Credential value
    """
    # First check if already loaded in environment
    value = os.environ.get(key)
    if value:
        return value
    
    # Otherwise reload credentials
    credentials = load_credentials()
    return credentials.get(key, default)
