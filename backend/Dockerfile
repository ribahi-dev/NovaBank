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

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY scripts ./scripts

RUN useradd --create-home appuser
USER appuser

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
