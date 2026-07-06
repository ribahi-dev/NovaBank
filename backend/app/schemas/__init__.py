"""Schemas Pydantic — le CONTRAT public de l'API.

Pourquoi ce package existe (la question centrale de la Phase B1) :
    Les modèles SQLAlchemy décrivent la BASE DE DONNÉES ; les schemas
    Pydantic décrivent ce que l'API ACCEPTE et RENVOIE. Ce sont deux
    contrats différents qui évoluent pour des raisons différentes —
    les confondre est l'erreur d'architecture n°1 des projets FastAPI.

Trois raisons de ne JAMAIS exposer un modèle SQLAlchemy directement :

1. SÉCURITÉ — le modèle contient TOUT, y compris ce qui ne doit jamais
   sortir (users.password_hash) ni jamais entrer (clients.is_active :
   un client "s'auto-réactivant" via un POST forgé = faille de type
   "Broken Object Property Level Authorization", OWASP API Top 10 n°3,
   cité dans le cahier des charges §5.1).

2. DÉCOUPLAGE — si l'API expose la base, renommer une colonne casse
   tous les clients HTTP. Le schema est une couche d'isolation : la
   base peut évoluer sans casser le contrat public.

3. VALIDATION — Pydantic rejette les données invalides À LA FRONTIÈRE
   de l'application, avec une erreur 422 détaillée, avant qu'elles ne
   touchent la logique métier ou la base.
"""

from app.schemas.client import ClientCreate, ClientResponse, ClientUpdate

__all__ = ["ClientCreate", "ClientResponse", "ClientUpdate"]
