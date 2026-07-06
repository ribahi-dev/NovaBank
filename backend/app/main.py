"""Point d'entrée de l'API NovaBank : assemblage de l'application.

Ce fichier ne fait QUE brancher (routers, CORS) — aucune logique métier.
Documentation interactive : /docs (Swagger) et /redoc.
Lancement dev : uvicorn app.main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import accounts, alerts, analytics, audit, auth, clients, transactions, users

app = FastAPI(
    title=settings.app_name,
    description="Plateforme bancaire intelligente d'aide à la décision — MVP",
    version="0.1.0",
)

# CORS : seul le frontend de dev est autorisé (liste blanche stricte,
# jamais '*' quand les requêtes portent un jeton d'authentification).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(clients.router)
app.include_router(accounts.router)
app.include_router(transactions.router)
app.include_router(alerts.router)
app.include_router(analytics.router)
app.include_router(audit.router)


@app.get("/health", tags=["Supervision"])
def health_check():
    """Sonde de vie pour Docker/monitoring — ne touche pas la base."""
    return {"status": "ok", "app": settings.app_name}
