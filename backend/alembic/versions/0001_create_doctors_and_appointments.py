"""create doctors and appointments tables

Revision ID: 0001_doctors_appointments
Revises:
"""
import sqlalchemy as sa
from alembic import op

revision = "0001_doctors_appointments"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "doctors",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("specialty", sa.String(length=80), nullable=False),
        sa.Column("email", sa.String(length=160), nullable=False, unique=True),
        sa.Column("room", sa.String(length=20), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "appointments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("patient_name", sa.String(length=120), nullable=False),
        sa.Column("patient_phone", sa.String(length=20), nullable=False),
        sa.Column("doctor_id", sa.Integer(), sa.ForeignKey("doctors.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("reason", sa.Text(), nullable=False, server_default=""),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="SCHEDULED"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_appointments_doctor_id", "appointments", ["doctor_id"])
    op.create_index("ix_appointments_scheduled_at", "appointments", ["scheduled_at"])
    op.create_index("ix_appointments_status", "appointments", ["status"])


def downgrade():
    op.drop_index("ix_appointments_status", table_name="appointments")
    op.drop_index("ix_appointments_scheduled_at", table_name="appointments")
    op.drop_index("ix_appointments_doctor_id", table_name="appointments")
    op.drop_table("appointments")
    op.drop_table("doctors")
