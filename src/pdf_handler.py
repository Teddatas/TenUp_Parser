"""
Gestionnaire de fichiers PDF
Gère le chargement et la conversion des PDF en formats exploitables
"""

import pdfplumber
from pathlib import Path
from typing import Optional, List
from src.logger import setup_logger

logger = setup_logger(__name__)


class PDFHandler:
    """Classe pour gérer les fichiers PDF"""
    
    @staticmethod
    def extract_text(pdf_path: str) -> Optional[str]:
        """
        Extrait tout le texte d'un PDF
        
        Args:
            pdf_path: Chemin vers le fichier PDF
        
        Returns:
            str: Texte complet du PDF ou None si erreur
        """
        try:
            pdf_path = Path(pdf_path)
            if not pdf_path.exists():
                logger.error(f"Fichier PDF introuvable : {pdf_path}")
                return None
            
            with pdfplumber.open(pdf_path) as pdf:
                text = ""
                for page_num, page in enumerate(pdf.pages, 1):
                    page_text = page.extract_text()
                    if page_text:
                        text += f"\n--- Page {page_num} ---\n{page_text}"
                
                logger.info(f"✓ PDF extrait : {pdf.pages.__len__()} pages")
                return text
        
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction du PDF : {e}")
            return None
    
    @staticmethod
    def extract_tables(pdf_path: str) -> Optional[List[list]]:
        """
        Extrait les tableaux d'un PDF
        
        Args:
            pdf_path: Chemin vers le fichier PDF
        
        Returns:
            List: Liste de tableaux trouvés dans le PDF
        """
        try:
            with pdfplumber.open(pdf_path) as pdf:
                tables = []
                for page_num, page in enumerate(pdf.pages, 1):
                    page_tables = page.extract_tables()
                    if page_tables:
                        for table in page_tables:
                            tables.append(table)
                        logger.info(f"✓ {len(page_tables)} tableau(x) trouvé(s) page {page_num}")
                
                return tables if tables else None
        
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction des tableaux : {e}")
            return None
    
    @staticmethod
    def get_pdf_info(pdf_path: str) -> Optional[dict]:
        """
        Récupère les informations du PDF
        
        Args:
            pdf_path: Chemin vers le fichier PDF
        
        Returns:
            dict: Informations sur le PDF
        """
        try:
            with pdfplumber.open(pdf_path) as pdf:
                return {
                    "pages": len(pdf.pages),
                    "metadata": pdf.metadata,
                }
        except Exception as e:
            logger.error(f"Erreur lors de la lecture des infos PDF : {e}")
            return None
