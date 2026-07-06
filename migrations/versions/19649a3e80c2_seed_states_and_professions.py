"""seed states and professions

Revision ID: 19649a3e80c2
Revises: abab7dbad43c
Create Date: 2026-07-05 23:57:27.565782

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '19649a3e80c2'
down_revision = 'abab7dbad43c'
branch_labels = None
depends_on = None

states_table = sa.table(
    'states',
    sa.column('state_name', sa.String),
)

professions_table = sa.table(
    'professions',
    sa.column('profession_name', sa.String),
)

STATES = [
    'Lagos', 'FCT Abuja', 'Oyo', 'Kano', 'Kaduna',
    'Rivers', 'Anambra', 'Delta', 'Enugu', 'Ogun',
]

PROFESSIONS = [
    'Registered Nurse', 'Medical Doctor', 'Lab Scientist', 'Pharmacist',
    'Physiotherapist', 'Radiographer', 'Midwife', 'Dentist',
]


def upgrade():
    op.bulk_insert(states_table, [{'state_name': name} for name in STATES])
    op.bulk_insert(professions_table, [{'profession_name': name} for name in PROFESSIONS])


def downgrade():
    conn = op.get_bind()
    conn.execute(professions_table.delete())
    conn.execute(states_table.delete())