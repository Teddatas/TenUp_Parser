"""
Système de logging pour TenUp Parser
"""

import logging
from pathlib import Path
from src.config import PROJECT_ROOT, LOG_LEVEL, LOG_FORMAT

# Créer le répertoire logs s'il n'existe pas
LOGS_DIR = PROJECT_ROOT / "logs"
LOGS_DIR.mkdir(exist_ok=True)

def setup_logger(name: str) -> logging.Logger:
    """
    Configure et retourne un logger
    
    Args:
        name: Nom du logger (généralement __name__)
    
    Returns:
        logging.Logger: Logger configuré
    """
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVEL)
    
    # Handler console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(LOG_LEVEL)
    formatter = logging.Formatter(LOG_FORMAT)
    console_handler.setFormatter(formatter)
    
    # Handler fichier
    file_handler = logging.FileHandler(
        LOGS_DIR / "tenup_parser.log",
        encoding="utf-8"
    )
    file_handler.setLevel(LOG_LEVEL)
    file_handler.setFormatter(formatter)
    
    # Éviter les duplicatas
    if not logger.handlers:
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
    
    return logger

# Logger global
logger = setup_logger(__name__)
