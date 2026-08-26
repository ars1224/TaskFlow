"""create TaskFlow schema

Revision ID: cc73f30e669c
Revises:
Create Date: 2026-08-20 18:21:22.906651

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "cc73f30e669c"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    existing_tables = set(
        inspector.get_table_names()
    )

    # -------------------------------------------------
    # USERS
    # -------------------------------------------------

    if "users" not in existing_tables:
        op.create_table(
            "users",

            sa.Column(
                "id",
                sa.Integer(),
                nullable=False,
            ),

            sa.Column(
                "full_name",
                sa.String(length=120),
                nullable=False,
            ),

            sa.Column(
                "email",
                sa.String(length=255),
                nullable=False,
            ),

            sa.Column(
                "password_hash",
                sa.String(length=255),
                nullable=False,
            ),

            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
            ),

            sa.PrimaryKeyConstraint(
                "id",
            ),

            sa.UniqueConstraint(
                "email",
            ),
        )

        op.create_index(
            "ix_users_email",
            "users",
            ["email"],
            unique=True,
        )


    # Refresh the inspector after possibly
    # creating the users table.
    inspector = sa.inspect(bind)

    existing_tables = set(
        inspector.get_table_names()
    )


    # -------------------------------------------------
    # TASKS
    # -------------------------------------------------

    if "tasks" not in existing_tables:
        op.create_table(
            "tasks",

            sa.Column(
                "id",
                sa.Integer(),
                nullable=False,
            ),

            sa.Column(
                "title",
                sa.String(length=150),
                nullable=False,
            ),

            sa.Column(
                "description",
                sa.Text(),
                nullable=True,
            ),

            sa.Column(
                "scheduled_date",
                sa.Date(),
                nullable=False,
            ),

            sa.Column(
                "due_date",
                sa.Date(),
                nullable=False,
            ),

            sa.Column(
                "status",
                sa.String(length=20),
                nullable=False,
            ),

            sa.Column(
                "priority",
                sa.String(length=10),
                nullable=False,
            ),

            sa.Column(
                "remarks",
                sa.Text(),
                nullable=True,
            ),

            sa.Column(
                "reflection",
                sa.Text(),
                nullable=True,
            ),

            sa.Column(
                "image_filename",
                sa.String(length=255),
                nullable=True,
            ),

            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
            ),

            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
            ),

            sa.Column(
                "completed_at",
                sa.DateTime(timezone=True),
                nullable=True,
            ),

            sa.Column(
                "user_id",
                sa.Integer(),
                nullable=False,
            ),

            sa.CheckConstraint(
                """
                status IN (
                    'yet-to-do',
                    'on-going',
                    'completed',
                    'dropped'
                )
                """,
                name="ck_tasks_status",
            ),

            sa.CheckConstraint(
                """
                priority IN (
                    'low',
                    'medium',
                    'high'
                )
                """,
                name="ck_tasks_priority",
            ),

            sa.ForeignKeyConstraint(
                ["user_id"],
                ["users.id"],
                ondelete="CASCADE",
            ),

            sa.PrimaryKeyConstraint(
                "id",
            ),
        )


        # Task indexes

        op.create_index(
            "ix_tasks_scheduled_date",
            "tasks",
            ["scheduled_date"],
            unique=False,
        )

        op.create_index(
            "ix_tasks_due_date",
            "tasks",
            ["due_date"],
            unique=False,
        )

        op.create_index(
            "ix_tasks_status",
            "tasks",
            ["status"],
            unique=False,
        )

        op.create_index(
            "ix_tasks_priority",
            "tasks",
            ["priority"],
            unique=False,
        )

        op.create_index(
            "ix_tasks_user_id",
            "tasks",
            ["user_id"],
            unique=False,
        )

        return


    # -------------------------------------------------
    # LEGACY DATABASE SUPPORT
    #
    # If someone has an older TaskFlow database where
    # tasks already exists but scheduled_date does not,
    # preserve the original migration behaviour.
    # -------------------------------------------------

    inspector = sa.inspect(bind)

    task_columns = {
        column["name"]
        for column in inspector.get_columns(
            "tasks"
        )
    }

    if "scheduled_date" not in task_columns:

        with op.batch_alter_table(
            "tasks",
            schema=None,
        ) as batch_op:

            batch_op.add_column(
                sa.Column(
                    "scheduled_date",
                    sa.Date(),
                    nullable=True,
                )
            )


        # Existing tasks use due_date as their
        # initial scheduled date.
        op.execute(
            """
            UPDATE tasks
            SET scheduled_date = due_date
            WHERE scheduled_date IS NULL
            """
        )


        with op.batch_alter_table(
            "tasks",
            schema=None,
        ) as batch_op:

            batch_op.alter_column(
                "scheduled_date",
                existing_type=sa.Date(),
                nullable=False,
            )

            batch_op.create_index(
                "ix_tasks_scheduled_date",
                ["scheduled_date"],
                unique=False,
            )


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    existing_tables = set(
        inspector.get_table_names()
    )

    if "tasks" in existing_tables:
        op.drop_table(
            "tasks"
        )

    if "users" in existing_tables:
        op.drop_table(
            "users"
        )