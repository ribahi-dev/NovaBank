# =============================================================================
# Dockerfile du backend — image de production de l'API NovaBank.
#
# Bonnes pratiques appliquées :
#   - image "slim" (pas de compilateurs inutiles -> plus légère, moins de
#     surface d'attaque) ;
#   - requirements copiés AVANT le code : le cache Docker ne réinstalle les
#     dépendances que si requirements.txt change, pas à chaque édition de code ;
#   - utilisateur NON-root : un conteneur compromis n'est pas root ;
#   - pas de --reload ni d'outils de dev dans l'image.
# =============================================================================
FROM python:3.14-slim

# Sortie Python non bufferisée : les logs (entrypoint, uvicorn) apparaissent
# en temps réel dans `docker logs`, indispensable pour diagnostiquer.
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY scripts ./scripts

# Entraîne le modèle ML PENDANT la construction de l'image (version PFE).
# L'artefact (ml_artifacts/model.joblib) est ainsi baké dans l'image : le
# conteneur démarre vite et utilise directement le RandomForest. Le script
# se replie sur les données simulées si la base (feedback) est inaccessible
# au build — ce qui est le cas ici, et c'est voulu.
RUN python -m scripts.train_model

RUN useradd --create-home appuser
USER appuser

EXPOSE 8000
# L'entrypoint attend la base, crée les tables, injecte les données de démo
# (si base vide) puis lance uvicorn — un seul `docker compose up` suffit.
CMD ["python", "-m", "scripts.docker_entrypoint"]
