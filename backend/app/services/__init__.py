"""Services — la logique métier du projet.

Règle de la couche : un service reçoit une Session et des objets du
domaine, applique les règles métier, et NE CONNAÎT PAS HTTP (aucun
import FastAPI ici, à l'exception des exceptions métier traduites en
HTTPException dans les routers). C'est ce qui rend la logique testable
et réutilisable (CLI, tâches planifiées, tests).
"""
