"""
Gestionnaire des trajets et estimations de temps de transport
- OSRM : Voiture, marche, vélo (gratuit, pas de clé)
- Navitia : Transports en commun (gratuit, clé optionnelle)
"""

from typing import Optional, Dict
import re
import requests
import os
from src.logger import setup_logger

logger = setup_logger(__name__)


class TravelTimeCalculator:
    """Calcule les temps de trajet entre deux adresses (100% gratuit)"""
    
    # URLs des APIs publiques
    OSRM_API_URL = "https://router.project-osrm.org/route/v1"
    NAVITIA_API_URL = "https://api.navitia.io/v1"
    NOMINATIM_API_URL = "https://nominatim.openstreetmap.org/search"
    
    def __init__(self, departure_address: str = None, navitia_api_key: str = None):
        """
        Initialise le calculateur
        
        Args:
            departure_address: Adresse de départ (ex: "Paris, France")
            navitia_api_key: Clé API Navitia (optionnel, gratuit sur https://www.navitia.io/)
        """
        self.departure_address = departure_address
        self.departure_coords = None
        self.navitia_api_key = navitia_api_key or os.getenv("NAVITIA_API_KEY")
        self.travel_times = {}  # Cache pour éviter les requêtes répétées
        
        if departure_address:
            self.set_departure_address(departure_address)
    
    def set_departure_address(self, address: str) -> None:
        """
        Définit l'adresse de départ et récupère ses coordonnées
        
        Args:
            address: Adresse de départ
        """
        self.departure_address = address
        self.departure_coords = self._geocode_address(address)
        
        if self.departure_coords:
            logger.info(f"Adresse de départ définie : {address} ({self.departure_coords})")
        else:
            logger.warning(f"Impossible de géolocaliser : {address}")
    
    def _geocode_address(self, address: str) -> Optional[tuple]:
        """
        Convertit une adresse en coordonnées (latitude, longitude)
        Utilise Nominatim (OpenStreetMap) - gratuit
        
        Args:
            address: Adresse à géolocaliser
        
        Returns:
            Tuple (latitude, longitude) ou None
        """
        try:
            params = {
                "q": address,
                "format": "json",
                "limit": 1,
            }
            
            response = requests.get(self.NOMINATIM_API_URL, params=params, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            if data:
                lat = float(data[0]["lat"])
                lon = float(data[0]["lon"])
                logger.debug(f"Géocodé : {address} -> ({lat}, {lon})")
                return (lat, lon)
            
            logger.warning(f"Adresse non trouvée : {address}")
            return None
        
        except Exception as e:
            logger.error(f"Erreur géocodage : {e}")
            return None
    
    def calculate_travel_time(self, destination_address: str, mode: str = "driving") -> Optional[Dict]:
        """
        Calcule le temps de trajet entre l'adresse de départ et la destination
        
        Args:
            destination_address: Adresse de destination
            mode: Mode de transport ("driving", "walking", "cycling", "transit")
        
        Returns:
            Dict avec clés: duration_seconds, duration_text, distance_m, distance_text, or None
        """
        if not self.departure_address or not self.departure_coords:
            logger.warning("Adresse de départ non définie ou non géocodée")
            return None
        
        if not destination_address or destination_address.strip() == "":
            logger.debug("Destination vide, skipping")
            return None
        
        # Cache key
        cache_key = f"{self.departure_address}|{destination_address}|{mode}"
        if cache_key in self.travel_times:
            return self.travel_times[cache_key]
        
        try:
            # Géocoder la destination
            dest_coords = self._geocode_address(destination_address)
            if not dest_coords:
                logger.warning(f"Impossible de géolocaliser : {destination_address}")
                return None
            
            # Utiliser Navitia pour transit si disponible
            if mode == "transit" and self.navitia_api_key:
                result = self._calculate_with_navitia(
                    self.departure_coords, 
                    dest_coords, 
                    destination_address
                )
                if result:
                    self.travel_times[cache_key] = result
                    return result
                logger.debug("Navitia a échoué, fallback sur OSRM")
            
            # Calculer le trajet avec OSRM pour voiture/marche/vélo
            result = self._calculate_with_osrm(self.departure_coords, dest_coords, mode)
            if result:
                self.travel_times[cache_key] = result
                return result
            
            logger.warning(f"Impossible de calculer le trajet pour {destination_address}")
            return None
        
        except Exception as e:
            logger.error(f"Erreur lors du calcul de trajet : {e}")
            return None
    
    def _calculate_with_navitia(self, origin_coords: tuple, dest_coords: tuple, dest_address: str) -> Optional[Dict]:
        """
        Utilise Navitia API pour les trajets en transports en commun (métro, bus, RER, tram)
        API officielle IDFM Île-de-France - gratuit après inscription sur https://www.navitia.io/
        
        Pour Île-de-France : https://prim.iledefrance-mobilites.fr/fr/apis/
        
        Args:
            origin_coords: Tuple (lat, lon) de départ
            dest_coords: Tuple (lat, lon) de destination
            dest_address: Adresse de destination (pour affichage)
        
        Returns:
            Dict avec les informations de trajet ou None
        """
        try:
            if not self.navitia_api_key:
                logger.debug("Navitia API key non configurée - mode transit indisponible")
                return None
            
            # Format Navitia : lon;lat (attention: OSRM utilise lat,lon)
            from_coord = f"{origin_coords[1]};{origin_coords[0]}"
            to_coord = f"{dest_coords[1]};{dest_coords[0]}"
            
            # URL pour IDFM (Île-de-France)
            url = f"{self.NAVITIA_API_URL}/journeys"
            
            # Paramètres : voir https://doc.navitia.io/api/public-transport-journeys
            params = {
                "from": from_coord,
                "to": to_coord,
                # datetime au format yyyyMMddTHHmmss (optionnel, utilise maintenant par défaut)
                "count": 3,  # Retourner 3 trajets pour avoir des alternatives
                "min_nb_transfers": 0,  # Autoriser 0 changement minimum
                "max_nb_transfers": 3,  # Maximum 3 changements
            }
            
            headers = {
                "Authorization": self.navitia_api_key,
            }
            
            logger.debug(f"Navitia request: {url} from={from_coord} to={to_coord}")
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("journeys") and len(data["journeys"]) > 0:
                # Prendre le premier (le plus rapide généralement)
                journey = data["journeys"][0]
                duration_seconds = journey["duration"]
                
                # Extracte les infos de chaque section du trajet
                sections = journey.get("sections", [])
                distance_m = 0
                transports_used = []
                nb_changes = 0
                
                for section in sections:
                    # Accumuler les distances si disponibles
                    if section.get("type") == "public_transport":
                        if "length" in section:
                            distance_m += section["length"]
                        
                        # Récupérer le mode et la ligne
                        display_info = section.get("display_informations", {})
                        mode = display_info.get("commercial_mode", "?")
                        line = display_info.get("label", "")
                        
                        # Éviter les doublons, garder les transports uniques
                        transport_key = f"{mode}"
                        if transport_key not in transports_used:
                            transports_used.append(transport_key)
                        
                        nb_changes += 1
                    
                    elif section.get("type") == "street_network":
                        # Section à pied (marche entre deux transports)
                        if "length" in section:
                            distance_m += section["length"]
                
                # Formatter le texte de durée
                hours = int(duration_seconds // 3600)
                minutes = int((duration_seconds % 3600) // 60)
                
                duration_text = ""
                if hours > 0:
                    duration_text += f"{hours}h "
                duration_text += f"{minutes}min"
                
                # Formatter la distance
                if distance_m >= 1000:
                    distance_text = f"{distance_m / 1000:.1f} km"
                elif distance_m > 0:
                    distance_text = f"{distance_m:.0f} m"
                else:
                    distance_text = "distance inconnue"
                
                # Créer l'info sur les transports utilisés
                transport_modes = ", ".join(set(transports_used)) if transports_used else "marche"
                
                # Ajouter le nombre de changements s'il y en a
                transfer_info = ""
                if nb_changes > 1:
                    nb_transfer_segments = nb_changes - 1
                    transfer_info = f" ({nb_transfer_segments} changement{'s' if nb_transfer_segments > 1 else ''})"
                
                return {
                    "duration_seconds": int(duration_seconds),
                    "duration_text": f"{duration_text} ({transport_modes}){transfer_info}",
                    "distance_m": int(distance_m),
                    "distance_text": distance_text,
                    "source": "Navitia/IDFM",
                    "transport_modes": transports_used,
                    "num_transfers": nb_changes - 1 if nb_changes > 0 else 0,
                }
            else:
                # Pas de trajet trouvé - peut arriver si l'adresse est mal géocodée
                logger.warning(f"Navitia: Pas de trajet trouvé pour {dest_address}")
                return None
        
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                logger.error("Navitia: Clé API invalide ou expirée - vérifiez NAVITIA_API_KEY")
            elif e.response.status_code == 404:
                logger.warning(f"Navitia: Trajet non trouvé")
            else:
                logger.error(f"Erreur HTTP Navitia ({e.response.status_code}): {e}")
            return None
        
        except Exception as e:
            logger.error(f"Erreur Navitia : {e}")
            return None
    
    def _calculate_with_osrm(self, origin_coords: tuple, dest_coords: tuple, mode: str) -> Optional[Dict]:
        """
        Utilise OSRM (Open Source Routing Machine) - totalement gratuit
        
        Args:
            origin_coords: Tuple (lat, lon) de départ
            dest_coords: Tuple (lat, lon) de destination
            mode: Mode de transport (driving, walking, cycling)
        
        Returns:
            Dict avec les informations de trajet ou None
        """
        try:
            # Mapper les modes OSRM
            osrm_profile = {
                "driving": "car",
                "walking": "foot",
                "cycling": "bike",
            }.get(mode, "car")
            
            # Format : /route/v1/{profile}/{coordinates}
            coords = f"{origin_coords[1]},{origin_coords[0]};{dest_coords[1]},{dest_coords[0]}"
            url = f"{self.OSRM_API_URL}/{osrm_profile}/{coords}"
            
            params = {
                "overview": "false",
                "steps": "false",
                "geometries": "geojson",
            }
            
            logger.debug(f"OSRM request: {url}")
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("code") == "Ok" and data.get("routes"):
                route = data["routes"][0]
                duration_seconds = route["duration"]
                distance_m = route["distance"]
                
                # Formatter le texte de durée
                hours = int(duration_seconds // 3600)
                minutes = int((duration_seconds % 3600) // 60)
                
                duration_text = ""
                if hours > 0:
                    duration_text += f"{hours}h "
                duration_text += f"{minutes}min"
                
                # Formatter la distance
                if distance_m >= 1000:
                    distance_text = f"{distance_m / 1000:.1f} km"
                else:
                    distance_text = f"{distance_m:.0f} m"
                
                mode_label = {
                    "car": "voiture",
                    "foot": "à pied",
                    "bike": "vélo"
                }.get(osrm_profile, osrm_profile)
                
                return {
                    "duration_seconds": int(duration_seconds),
                    "duration_text": f"{duration_text} ({mode_label})",
                    "distance_m": int(distance_m),
                    "distance_text": distance_text,
                    "source": "OSRM",
                }
            else:
                logger.warning(f"OSRM error: {data.get('message', 'Unknown')}")
                return None
        
        except Exception as e:
            logger.error(f"Erreur OSRM : {e}")
            return None
    
    def format_travel_info(self, travel_data: Dict) -> str:
        """
        Formate les informations de trajet en texte lisible
        
        Args:
            travel_data: Dict retourné par calculate_travel_time()
        
        Returns:
            str: Texte formaté
        """
        if not travel_data:
            return ""
        
        duration = travel_data.get("duration_text", "N/A")
        distance = travel_data.get("distance_text", "N/A")
        
        return f"{duration} ({distance})"
    
    def extract_address_from_installations(self, installations_str: str) -> str:
        """
        Extrait une adresse exploitable depuis le champ INSTALLATIONS
        
        Args:
            installations_str: Chaîne INSTALLATIONS (ex: "93260_PARIS & T.C.JOINVILLE & Route")
        
        Returns:
            str: Adresse nettoyée
        """
        if not installations_str:
            return ""
        
        # Prendre la première partie (code postal + ville)
        parts = installations_str.split(" & ")
        
        # Nettoyer et combiner les parties utiles
        address_parts = []
        
        for part in parts[:3]:  # Prendre les 3 premières parties
            part = part.strip()
            if part and not part.startswith(("http", "mailto", "01", "02", "03", "04", "05", "06", "07", "08", "09")):
                # Ignorer les URLs, emails et numéros de téléphone
                address_parts.append(part)
        
        address = " ".join(address_parts)
        
        # Ajouter France si pas présent
        if "france" not in address.lower():
            address += ", France"
        
        return address
