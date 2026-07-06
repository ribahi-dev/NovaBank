"""Connexion à PostgreSQL : Engine, fabrique de Sessions, dépendance get_db.

Pourquoi ce fichier existe :
    C'est l'UNIQUE point de contact entre l'application et la base.
    Tout le reste du code (repositories, services) reçoit une Session
    déjà prête — il ne sait ni où est la base, ni comment s'y connecter.
    Changer de base (autre hôte, base de test) = changer une variable
    d'environnement, zéro ligne de code.

Les trois objets, du plus bas niveau au plus haut :
    Engine       : le "moteur". Créé UNE SEULE fois au démarrage, il gère
                   un pool de connexions TCP réutilisables (ouvrir une
                   connexion PostgreSQL coûte cher ; le pool les recycle).
    SessionLocal : une "fabrique" de Sessions. Chaque requête HTTP obtient
                   SA propre Session — jamais de partage entre requêtes.
    Session      : l'espace de travail d'UNE unité de travail : elle suit
                   les objets chargés (Identity Map), accumule les
                   modifications et les envoie en bloc au commit
                   (Unit of Work).
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# pool_pre_ping=True : avant de réutiliser une connexion du pool, SQLAlchemy
# envoie un "SELECT 1". Si la connexion est morte (Postgres redémarré, réseau
# coupé), elle est remplacée silencieusement au lieu de faire planter la
# requête de l'utilisateur.
engine = create_engine(settings.database_url, pool_pre_ping=True)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,  # on valide EXPLICITEMENT (db.commit()) — jamais d'écriture accidentelle
    autoflush=False,   # pas d'envoi implicite du SQL en attente avant chaque SELECT :
                       # comportement prévisible, on contrôle le moment du flush
)


def get_db():
    """Dépendance FastAPI : fournit une Session par requête HTTP.

    Le `yield` coupe la fonction en deux :
      - avant : exécuté quand la requête ARRIVE (création de la session) ;
      - après (le finally) : exécuté quand la réponse est PARTIE
        (fermeture garantie, même si le endpoint a levé une exception).

    C'est le pattern "une session par requête" — la session retourne au
    pool quoi qu'il arrive, sinon fuite de connexions et base saturée.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
