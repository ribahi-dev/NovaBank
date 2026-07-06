"""Point d'entrée de l'API NovaBank.

Pourquoi ce fichier existe :
    C'est ici que l'application FastAPI est créée et assemblée. Au fil du
    projet, ce fichier ne fera QUE brancher des éléments définis ailleurs
    (routers, middlewares, gestionnaires d'erreurs) — jamais de logique
    métier ici. Un main.py qui grossit est le symptôme d'une architecture
    qui se dégrade.

Lancement en développement :
    uvicorn app.main:app --reload
    (--reload : redémarre à chaque modification de fichier — dev uniquement)

FastAPI génère automatiquement la documentation interactive de l'API :
    http://localhost:8000/docs   (Swagger UI — pour tester à la main)
    http://localhost:8000/redoc  (version lisible pour le rapport/jury)
"""

from fastapi import FastAPI

from app.core.config import settings

app = FastAPI(title=settings.app_name)


@app.get("/health")
def health_check():
    """Endpoint de supervision ("suis-je vivant ?").

    Convention universelle en entreprise : les orchestrateurs (Docker
    healthcheck, Kubernetes, load balancers) interrogent cette route pour
    savoir si le service doit recevoir du trafic. Elle ne touche pas la
    base : elle répond juste "le processus tourne".
    """
    return {"status": "ok", "app": settings.app_name}
