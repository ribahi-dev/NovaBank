"""Peuple la base avec un jeu de démonstration réaliste (CdC §3.1).

Crée : 3 utilisateurs (admin/directeur/conseiller), 30 clients marocains
simulés, leurs comptes, ~400 transactions étalées sur 30 jours dont
quelques scénarios suspects qui génèrent des alertes.

Usage (depuis backend/, venv activé, PostgreSQL démarré, tables créées) :
    python -m scripts.seed

Idempotent : refuse de tourner si des clients existent déjà
(relancer après un reset : docker compose down -v && up, create_tables).
"""

import random
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import func, select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import Account, Alert, Client, RiskScore, Transaction, User

random.seed(42)  # démo REPRODUCTIBLE : mêmes données à chaque reconstruction

FIRST_NAMES = [
    "Amina", "Karim", "Fatima", "Omar", "Salma", "Youssef", "Khadija", "Mehdi",
    "Nadia", "Hamza", "Layla", "Rachid", "Sofia", "Adil", "Meriem", "Tarik",
]
LAST_NAMES = [
    "Benali", "Alaoui", "Tazi", "Idrissi", "Bennani", "El Fassi", "Chraibi",
    "Berrada", "Lahlou", "Sqalli", "Bennis", "Kettani",
]
CITIES = ["Casablanca", "Rabat", "Marrakech", "Fès", "Tanger", "Agadir"]
PROFESSIONS = [
    ("Enseignant", 7000), ("Médecin", 25000), ("Commerçant", 12000),
    ("Ingénieur", 18000), ("Fonctionnaire", 9000), ("Artisan", 5500),
    ("Pharmacien", 20000), ("Chauffeur", 4500),
]

USERS = [
    ("Hassan", "El Amrani", "admin@novabank.ma", "Admin@2026!", "admin"),
    ("Bouchra", "Raiss", "directeur@novabank.ma", "Directeur@2026!", "director"),
    ("El Mehdi", "Ribahi", "conseiller@novabank.ma", "Conseiller@2026!", "advisor"),
]


def seed():
    db = SessionLocal()
    try:
        if db.scalar(select(func.count()).select_from(Client)):
            print("La base contient déjà des clients — seed annulé.")
            return

        users = {}
        for first, last, email, password, role in USERS:
            user = User(
                first_name=first, last_name=last, email=email,
                password_hash=hash_password(password), role=role,
            )
            db.add(user)
            users[role] = user
        db.flush()
        advisor = users["advisor"]

        now = datetime.now(timezone.utc)
        accounts: list[tuple[Account, str, Decimal]] = []  # (compte, ville habituelle, revenu)

        for i in range(30):
            profession, income = random.choice(PROFESSIONS)
            income_dec = Decimal(income)
            home_city = random.choice(CITIES)
            client = Client(
                first_name=random.choice(FIRST_NAMES),
                last_name=random.choice(LAST_NAMES),
                cin=f"{random.choice('ABCDEJK')}{random.choice('BEHJZ')}{100000 + i}",
                phone=f"06{random.randint(10000000, 99999999)}",
                address=f"{random.randint(1, 200)} rue {random.choice(LAST_NAMES)}, {home_city}",
                profession=profession,
                monthly_income=income_dec,
            )
            db.add(client)
            db.flush()
            for _ in range(random.choice([1, 1, 2])):
                account = Account(
                    account_number="NB" + "".join(str(random.randint(0, 9)) for _ in range(12)),
                    account_type=random.choice(["current", "current", "savings"]),
                    balance=Decimal(random.randint(2000, 80000)),
                    client_id=client.id,
                )
                db.add(account)
                accounts.append((account, home_city, income_dec))
        db.flush()

        # ~400 transactions "normales" sur 30 jours : montants cohérents avec
        # le revenu, ville habituelle, heures de bureau.
        for _ in range(400):
            account, home_city, income = random.choice(accounts)
            amount = Decimal(random.randint(100, max(200, int(income) // 3)))
            moment = now - timedelta(
                days=random.randint(0, 29), hours=random.randint(8, 18),
                minutes=random.randint(0, 59),
            )
            tx = Transaction(
                transaction_type=random.choice(["deposit", "deposit", "withdrawal"]),
                amount=amount,
                city=home_city,
                account_id=account.id,
                created_by_id=advisor.id,
                created_at=moment,  # historique daté (écrase le server_default)
            )
            db.add(tx)
            db.flush()
            db.add(RiskScore(
                transaction_id=tx.id, score=random.randint(0, 25),
                confidence_level="faible",
                explanation="Transaction sans signal de risque particulier.",
                model_version="mvp-rules-v1",
            ))

        # 5 scénarios SUSPECTS : gros montant, nuit, ville inhabituelle.
        for i in range(5):
            account, home_city, income = random.choice(accounts)
            away = random.choice([c for c in CITIES if c != home_city])
            amount = (income * Decimal(random.randint(3, 8))).quantize(Decimal("0.01"))
            moment = now - timedelta(days=random.randint(0, 10))
            moment = moment.replace(hour=random.randint(1, 4), minute=random.randint(0, 59))
            tx = Transaction(
                transaction_type="withdrawal", amount=amount, city=away,
                description="Opération inhabituelle détectée en démo",
                account_id=account.id, created_by_id=advisor.id, created_at=moment,
            )
            db.add(tx)
            db.flush()
            score = random.randint(78, 95)
            explanation = (
                f"Signaux détectés : montant {float(amount / income):.1f}x supérieur au revenu "
                f"mensuel du client ; opération à {moment.strftime('%Hh%M')}, hors des horaires "
                f"habituels ; ville inhabituelle ({away}, précédente : {home_city})."
            )
            db.add(RiskScore(
                transaction_id=tx.id, score=score, confidence_level="élevé",
                explanation=explanation, model_version="mvp-rules-v1",
            ))
            db.add(Alert(
                alert_type="transaction_risk",
                level="critical" if score >= 85 else "high",
                message=(
                    f"Score de risque {score}/100 sur withdrawal de {amount} MAD "
                    f"(compte {account.account_number}). {explanation}"
                ),
                transaction_id=tx.id,
                created_at=moment,
            ))

        db.commit()
        print("Seed terminé :")
        print("  admin@novabank.ma / Admin@2026!")
        print("  directeur@novabank.ma / Directeur@2026!")
        print("  conseiller@novabank.ma / Conseiller@2026!")
        print(f"  {len(accounts)} comptes, ~405 transactions, 5 alertes ouvertes.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
