"""Schemas Pydantic de l'entité Client — le trio Create / Update / Response.

Pourquoi TROIS schemas pour UNE entité ?
    Parce que les données n'ont pas la même forme selon le sens du voyage :

      ClientCreate    (entrée POST)   : tout ce qu'il faut pour créer —
                                        mais PAS id, ni created_at, ni
                                        is_active (générés par le système).
      ClientUpdate    (entrée PATCH)  : tous les champs OPTIONNELS —
                                        on ne modifie que ce qu'on envoie.
      ClientResponse  (sortie)        : ce que l'API renvoie — avec id et
                                        created_at, générés par la base.

    ┌──────────┐  ClientCreate   ┌─────────┐   modèle Client   ┌──────────┐
    │ Frontend │ ──────────────► │ FastAPI │ ────────────────► │ Postgres │
    │  React   │ ◄────────────── │         │ ◄──────────────── │          │
    └──────────┘  ClientResponse └─────────┘   modèle Client   └──────────┘
        (JSON à la frontière)        (objets Python à l'intérieur)

Fonctionnement interne de Pydantic (v2) :
    À l'import, Pydantic compile chaque classe en un validateur écrit en
    Rust (pydantic-core) : à l'exécution, `ClientCreate(**données)` parse,
    convertit ("12000.50" -> Decimal) et valide en une passe. Données
    invalides -> ValidationError, que FastAPI transforme en réponse
    HTTP 422 listant chaque champ fautif.
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ClientBase(BaseModel):
    """Champs communs à la création et à la lecture (principe DRY :
    définis UNE fois, hérités partout — une règle de validation ne doit
    jamais exister en deux exemplaires qui pourraient diverger)."""

    # min_length=1 : refuse la chaîne vide "" — qui est pourtant un str
    # valide pour Python. max_length=100 : ALIGNÉ sur String(100) du
    # modèle SQLAlchemy, pour échouer proprement en 422 plutôt qu'en
    # erreur PostgreSQL au moment de l'INSERT.
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)

    # CIN marocain : 1-2 lettres puis 1 à 8 chiffres (ex. A123456, BE98765).
    # La regex documente ET applique le format — validation à la frontière.
    cin: str = Field(min_length=2, max_length=30, pattern=r"^[A-Za-z]{1,2}\d{1,8}$")

    # `| None = None` : champ optionnel — l'absence est une valeur légitime.
    phone: str | None = Field(default=None, max_length=30)
    address: str | None = Field(default=None, max_length=255)
    profession: str | None = Field(default=None, max_length=100)

    # ge=0 ("greater or equal") : un revenu négatif est un non-sens métier ;
    # la contrainte vit ici, PAS dans le routeur — déclarative et testable.
    # Decimal (jamais float) : cohérent avec Numeric(12,2) côté base.
    monthly_income: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)


class ClientCreate(ClientBase):
    """Corps du POST /clients — exactement ClientBase, rien de plus.

    Volontairement SANS id, created_at, is_active : ces champs sont
    décidés par le système, jamais par l'appelant. Si un client HTTP
    les envoie quand même, Pydantic les IGNORE (comportement par défaut) :
    impossible de forcer un id ou de s'auto-réactiver.
    """


class ClientUpdate(BaseModel):
    """Corps du PATCH /clients/{id} — mise à jour PARTIELLE.

    Tous les champs sont optionnels : le conseiller corrige UN téléphone
    sans renvoyer toute la fiche. Le CRUD (Phase B2) utilisera
    `model_dump(exclude_unset=True)` pour distinguer "champ absent"
    (on ne touche pas) de "champ envoyé à None" (on efface la valeur).
    N'hérite PAS de ClientBase : les contraintes y rendent les champs
    obligatoires, ici tout doit rester facultatif.
    """

    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    phone: str | None = Field(default=None, max_length=30)
    address: str | None = Field(default=None, max_length=255)
    profession: str | None = Field(default=None, max_length=100)
    monthly_income: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)

    # Choix métier assumé : PAS de cin ici. L'identifiant national d'une
    # personne ne "se corrige" pas par un simple PATCH — en banque, cela
    # exigerait une procédure KYC dédiée et auditée.


class ClientResponse(ClientBase):
    """Ce que l'API RENVOIE — la fiche complète, y compris les champs
    générés par le système (id, created_at) et l'état (is_active).

    Remarquer ce qui n'y est PAS : rien de sensible chez Client, mais le
    même pattern sur User exclura password_hash — c'est le schema de
    sortie qui garantit qu'un secret ne peut PAS fuiter, même par accident.
    """

    id: int
    is_active: bool
    created_at: datetime

    # from_attributes=True : autorise ClientResponse.model_validate(objet_orm)
    # — Pydantic lit alors les ATTRIBUTS (client.id, client.cin...) au lieu
    # d'exiger un dictionnaire. C'est LE pont officiel SQLAlchemy -> Pydantic,
    # utilisé par FastAPI quand un endpoint déclare response_model=ClientResponse.
    model_config = ConfigDict(from_attributes=True)
