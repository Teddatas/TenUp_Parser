"""
Petit serveur local pour la carte interactive.

    python -m src.serve            # http://localhost:8000

Sert data/output/ et expose POST /api/regenerate {"adresse": "..."} qui
relance le pipeline (nouvelle adresse de départ) puis régénère la carte.
"""

from __future__ import annotations

import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

from src.config import OUTPUT_DIR
from src.logger import setup_logger

logger = setup_logger(__name__)
PORT = 8000


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(OUTPUT_DIR), **kw)

    def do_GET(self):  # noqa: N802
        if self.path in ("/", ""):
            self.path = "/carte_tournois.html"
        return super().do_GET()

    def do_POST(self):  # noqa: N802
        if self.path.rstrip("/") != "/api/regenerate":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", 0))
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
            adresse = (body.get("adresse") or "").strip()
            if not adresse:
                raise ValueError("adresse vide")
            from main_carte import generate

            logger.info(f"Régénération pour : {adresse}")
            n = generate(address=adresse)
            self._json(200, {"ok": True, "tournois": n})
        except Exception as e:  # noqa: BLE001
            logger.error(f"Régénération échouée : {e}")
            self._json(500, {"ok": False, "erreur": str(e)})

    def _json(self, code: int, payload: dict):
        data = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *a):  # silencieux
        pass


def main():
    logger.info(f"Carte : http://localhost:{PORT}/  (Ctrl+C pour arrêter)")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
