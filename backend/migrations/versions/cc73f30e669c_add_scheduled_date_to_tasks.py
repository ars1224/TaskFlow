"""add scheduled date to tasks

Revision ID: cc73f30e669c
Revises:
Create Date: 2026-08-20 18:21:22.906651

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cc73f30e669c'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add scheduled_date temporarily allowing NULL
    with op.batch_alter_table('tasks', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                'scheduled_date',
                sa.Date(),
                nullable=True
            )
        )

    # Existing tasks use their current due date
    # as their initial scheduled date.
    op.execute(
        """
        UPDATE tasks
        SET scheduled_date = due_date
        WHERE scheduled_date IS NULL
        """
    )

    # Make scheduled_date required and add its index.
    with op.batch_alter_table('tasks', schema=None) as batch_op:
        batch_op.alter_column(
            'scheduled_date',
            existing_type=sa.Date(),
            nullable=False
        )

        batch_op.create_index(
            batch_op.f('ix_tasks_scheduled_date'),
            ['scheduled_date'],
            unique=False
        )


def downgrade():
    with op.batch_alter_table('tasks', schema=None) as batch_op:
        batch_op.drop_index(
            batch_op.f('ix_tasks_scheduled_date')
        )

        batch_op.drop_column('scheduled_date')