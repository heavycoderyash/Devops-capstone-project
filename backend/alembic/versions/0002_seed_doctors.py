"""seed starter doctors so a fresh environment is demo-ready

Revision ID: 0002_seed_doctors
Revises: 0001_doctors_appointments
"""
import sqlalchemy as sa
from alembic import op

revision = "0002_seed_doctors"
down_revision = "0001_doctors_appointments"
branch_labels = None
depends_on = None

SEED_EMAILS = [
    "ananya.mehta@medislot.clinic",
    "rohan.kapoor@medislot.clinic",
    "sara.iyer@medislot.clinic",
    "vikram.desai@medislot.clinic",
]


doctors = sa.table(
    "doctors",
    sa.column("name", sa.String),
    sa.column("specialty", sa.String),
    sa.column("email", sa.String),
    sa.column("room", sa.String),
)


def upgrade():
    op.bulk_insert(
        doctors,
        [
            {"name": "Dr. Ananya Mehta", "specialty": "General Medicine", "email": SEED_EMAILS[0], "room": "101"},
            {"name": "Dr. Rohan Kapoor", "specialty": "Cardiology", "email": SEED_EMAILS[1], "room": "204"},
            {"name": "Dr. Sara Iyer", "specialty": "Dermatology", "email": SEED_EMAILS[2], "room": "112"},
            {"name": "Dr. Vikram Desai", "specialty": "Pediatrics", "email": SEED_EMAILS[3], "room": "108"},
        ],
    )


def downgrade():
    op.execute(doctors.delete().where(doctors.c.email.in_(SEED_EMAILS)))
