"""Configuration centralisée de l'application, chargée depuis backend/.env.

Pourquoi ce fichier existe :
    Le code doit être IDENTIQUE en dev, en test et en démo ; seule la
    configuration change (principe "12-factor app"). Les secrets (clé JWT,
    mot de passe base) ne doivent JAMAIS être écrits dans le code versionné
    sur GitHub — ils vivent dans un fichier .env local, ignoré par git.

Pourquoi pydantic-settings plutôt que os.environ :
    1. Validation au démarrage : si DATABASE_URL manque ou si
       ACCESS_TOKEN_EXPIRE_MINUTES n'est pas un entier, l'application
       REFUSE de démarrer avec un message clair — au lieu de planter
       à la première requête, en pleine démo devant le jury.
    2. Typage : `settings.access_token_expire_minutes` est un vrai int,
       pas une chaîne à convertir partout.
    3. Défauts explicites : une valeur sans défaut (database_url) est
       OBLIGATOIRE ; une valeur avec défaut est optionnelle.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "NovaBank API"
    app_env: str = "development"

    # Clé de signature des JWT. Le défaut n'existe que pour le confort du
    # dev local ; en démo/production, la vraie valeur vient du .env.
    secret_key: str = "change-this-secret-key"
    access_token_expire_minutes: int = 60

    # Pas de valeur par défaut = variable OBLIGATOIRE : impossible de
    # démarrer l'API sans savoir où est la base.
    database_url: str

    # Indique à pydantic-settings de lire backend/.env (encodage UTF-8).
    # Les variables d'environnement système ont priorité sur le fichier.
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


# Instance unique, importée partout : `from app.core.config import settings`.
# Créée UNE fois à l'import du module (et donc validée une fois au démarrage).
settings = Settings()
