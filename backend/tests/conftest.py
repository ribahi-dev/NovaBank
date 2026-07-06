"""conftest.py — configuration partagée de tous les tests pytest.

Pourquoi ce fichier existe :
    pytest le charge AUTOMATIQUEMENT avant tout test du dossier. C'est ici
    qu'on prépare l'environnement de test et qu'on définira les fixtures
    partagées (client HTTP de test, session de base de données de test...).

Le point délicat réglé ici :
    app/core/config.py exige DATABASE_URL au démarrage (c'est voulu : l'API
    refuse de démarrer sans configuration). Mais en CI GitHub Actions, il
    n'y a pas de fichier .env. On fournit donc une valeur AVANT que le
    premier `import app...` ne déclenche la validation de Settings.
    `setdefault` ne remplace pas une vraie variable déjà présente — en
    local, ton .env garde la priorité.
"""

import os

# Doit s'exécuter avant tout import de `app` (les imports des fichiers de
# test passent par ce conftest en premier — garantie pytest).
os.environ.setdefault(
    "DATABASE_URL", "postgresql+psycopg://postgres:password@localhost:5433/novabank_test"
)
