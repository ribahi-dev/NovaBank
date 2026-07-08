"""Chargement du modèle ML entraîné et prédiction du score de risque.

Décision d'architecture : le scoring a DEUX moteurs derrière la même
interface —
    1. le modèle ML (RandomForest) si un artefact entraîné existe ;
    2. sinon, repli transparent sur le moteur de règles (mvp-rules-v1).
L'API ne tombe JAMAIS en panne de scoring : sans artefact, elle reste
100 % fonctionnelle. Chaque RiskScore garde la trace du moteur utilisé
via model_version — exigence d'auditabilité (MLOps minimal).

L'artefact (ml_artifacts/model.joblib) est un dict :
    {"model": RandomForestClassifier, "feature_names": [...],
     "version": "ml-rf-v2.0", "trained_at": "...", "metrics": {...}}
Le chemin vient de settings (ML_MODEL_PATH) pour que les tests puissent
pointer ailleurs et rester déterministes.
"""

from pathlib import Path
from typing import Any

from app.core.config import settings
from app.ml.features import FEATURE_NAMES, TransactionFeatures

_cache: dict[str, Any] = {"artifact": None, "path": None, "explainer": None}


def _load() -> dict | None:
    """Charge l'artefact une seule fois (import joblib différé : ne pas
    payer scikit-learn au démarrage si on ne s'en sert pas)."""
    path = Path(settings.ml_model_path)
    if _cache["path"] == str(path) and _cache["artifact"] is not None:
        return _cache["artifact"]
    if not path.exists():
        return None
    import joblib

    artifact = joblib.load(path)
    # Garde-fou : si l'ordre des features de l'artefact ne correspond pas
    # au code actuel, on REFUSE le modèle (prédire avec des colonnes
    # permutées = scores silencieusement absurdes).
    if artifact.get("feature_names") != FEATURE_NAMES:
        raise RuntimeError(
            "Artefact ML incompatible : features attendues "
            f"{artifact.get('feature_names')} != {FEATURE_NAMES}. Réentraîner le modèle."
        )
    _cache["artifact"] = artifact
    _cache["path"] = str(path)
    return artifact


def reload() -> None:
    """Vide le cache (tests, ou rechargement après réentraînement)."""
    _cache["artifact"] = None
    _cache["path"] = None
    _cache["explainer"] = None


def is_available() -> bool:
    return _load() is not None


def version() -> str | None:
    artifact = _load()
    return artifact["version"] if artifact else None


def predict_score(features: TransactionFeatures) -> int:
    """Probabilité de fraude du modèle -> score 0-100 (format CdC §9.2)."""
    artifact = _load()
    if artifact is None:
        raise RuntimeError("Aucun modèle ML disponible — utiliser le moteur de règles.")
    proba = artifact["model"].predict_proba([features.as_vector()])[0][1]
    return round(float(proba) * 100)


def explain_shap(features: TransactionFeatures) -> dict[str, float] | None:
    """Contribution SHAP de chaque feature à la prédiction de fraude (XAI).

    SHAP (SHapley Additive exPlanations) répartit, de façon mathématiquement
    fondée (théorie des jeux), le score entre les variables : une valeur
    positive pousse vers la fraude, négative vers le normal. C'est la méthode
    de référence de l'état de l'art pour expliquer un modèle d'arbres.

    Retourne {feature: contribution} ou None si SHAP n'est pas installé /
    si aucun modèle n'est disponible (l'app reste fonctionnelle sans).
    """
    artifact = _load()
    if artifact is None:
        return None
    try:
        import shap  # import différé : lourd, optionnel
    except ImportError:
        return None

    import numpy as np

    if _cache["explainer"] is None:
        _cache["explainer"] = shap.TreeExplainer(artifact["model"])

    # shap_values attend un tableau numpy ; pour un arbre binaire la sortie
    # a la forme (1, n_features, 2 classes) -> on prend la classe 1 (fraude).
    values = _cache["explainer"].shap_values(np.array([features.as_vector()]))
    arr = np.array(values)
    contrib = arr[0, :, 1] if arr.ndim == 3 else np.array(values[1])[0] if isinstance(values, list) else arr[0]
    return {name: round(float(c), 4) for name, c in zip(FEATURE_NAMES, contrib)}
