"""Tests du module IA : features, repli sur règles, chargement d'artefact.

Ces tests ne dépendent PAS d'un modèle entraîné sur disque (conftest pointe
ML_MODEL_PATH vers un fichier absent) : ils vérifient le contrat du scoring
et l'entraînement d'un artefact jetable dans un dossier temporaire.
"""


import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier

from app.ml import model as ml_model
from app.ml.features import FEATURE_NAMES, TransactionFeatures, explain_features


def test_feature_vector_order_is_canonical():
    f = TransactionFeatures(
        amount_over_income=1.5, amount_over_avg=2.0, is_night=1, city_changed=0, tx_last_24h=3
    )
    assert f.as_vector() == [1.5, 2.0, 1.0, 0.0, 3.0]
    assert len(FEATURE_NAMES) == 5


def test_explain_features_is_human_readable():
    f = TransactionFeatures(
        amount_over_income=3.2, amount_over_avg=0, is_night=1, city_changed=1, tx_last_24h=1
    )
    reasons = explain_features(f)
    joined = " ".join(reasons).lower()
    assert "montant" in joined
    assert "nocturne" in joined
    assert "ville" in joined


def test_scoring_falls_back_to_rules_without_artifact(client, auth_headers):
    """Sans modèle entraîné, l'API reste fonctionnelle : moteur de règles."""
    headers = auth_headers("advisor")
    cid = client.post(
        "/clients", headers=headers,
        json={"first_name": "A", "last_name": "B", "cin": "AB111111", "monthly_income": "5000"},
    ).json()["id"]
    aid = client.post("/accounts", headers=headers, json={"client_id": cid, "initial_balance": "0"}).json()["id"]

    resp = client.post(
        "/transactions", headers=headers,
        json={"transaction_type": "deposit", "amount": "100", "account_id": aid, "city": "Rabat"},
    )
    assert resp.status_code == 201
    assert resp.json()["risk_score"]["model_version"] == "mvp-rules-v1"


def test_model_loads_valid_artifact_and_rejects_bad_features(tmp_path, monkeypatch):
    """Le loader accepte un artefact conforme et REFUSE un ordre de
    features divergent (protection contre le training/serving skew)."""
    # Petit modèle jouet entraîné sur des vecteurs à 5 features.
    X = np.array([[0, 0, 0, 0, 0], [5, 5, 1, 1, 8]] * 5)
    y = np.array([0, 1] * 5)
    rf = RandomForestClassifier(n_estimators=5, random_state=0).fit(X, y)

    good = tmp_path / "good.joblib"
    joblib.dump({"model": rf, "feature_names": FEATURE_NAMES, "version": "ml-test"}, good)
    monkeypatch.setenv("ML_MODEL_PATH", str(good))
    from app.core.config import settings

    monkeypatch.setattr(settings, "ml_model_path", str(good))
    ml_model.reload()
    assert ml_model.is_available()
    assert ml_model.version() == "ml-test"
    high = ml_model.predict_score(
        TransactionFeatures(amount_over_income=6, amount_over_avg=6, is_night=1, city_changed=1, tx_last_24h=9)
    )
    assert 0 <= high <= 100

    # Artefact incompatible : mauvais ordre de features -> refus explicite.
    bad = tmp_path / "bad.joblib"
    joblib.dump({"model": rf, "feature_names": ["x", "y"], "version": "bad"}, bad)
    monkeypatch.setattr(settings, "ml_model_path", str(bad))
    ml_model.reload()
    import pytest

    with pytest.raises(RuntimeError, match="incompatible"):
        ml_model.is_available()
    ml_model.reload()


def test_shap_contributions_when_model_present(tmp_path, monkeypatch):
    """SHAP renvoie une contribution par variable quand un modèle existe."""
    X = np.array([[0, 0, 0, 0, 0], [6, 6, 1, 1, 9]] * 8)
    y = np.array([0, 1] * 8)
    rf = RandomForestClassifier(n_estimators=10, random_state=0).fit(X, y)
    artifact = tmp_path / "m.joblib"
    joblib.dump({"model": rf, "feature_names": FEATURE_NAMES, "version": "ml-test"}, artifact)

    from app.core.config import settings

    monkeypatch.setattr(settings, "ml_model_path", str(artifact))
    ml_model.reload()

    contrib = ml_model.explain_shap(
        TransactionFeatures(amount_over_income=6, amount_over_avg=6, is_night=1, city_changed=1, tx_last_24h=9)
    )
    ml_model.reload()

    assert contrib is not None
    assert set(contrib.keys()) == set(FEATURE_NAMES)  # une contribution par feature
    assert all(isinstance(v, float) for v in contrib.values())


def test_shap_is_none_without_model():
    """Sans modèle chargé, SHAP renvoie None (pas d'erreur)."""
    ml_model.reload()
    assert ml_model.explain_shap(
        TransactionFeatures(amount_over_income=1, amount_over_avg=1, is_night=0, city_changed=0, tx_last_24h=1)
    ) is None
