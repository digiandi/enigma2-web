import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "timer_actions",
        sa.Column("token_hash", sa.String(64), primary_key=True),
        sa.Column(
            "session_hash",
            sa.String(64),
            sa.ForeignKey("sessions.token_hash", ondelete="SET NULL"),
        ),
        sa.Column(
            "receiver_id",
            sa.Integer,
            sa.ForeignKey("receivers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("payload", sa.Text, nullable=False),
        sa.Column("created_at", sa.Integer, nullable=False),
        sa.Column("used_at", sa.Integer),
        sa.Column("locked_receiver_id", sa.Integer, unique=True),
        sa.Column("lock_until", sa.Integer),
        sa.CheckConstraint("kind IN ('add', 'edit', 'delete')", name="ck_timer_action_kind"),
    )
    op.create_index("ix_timer_actions_session_hash", "timer_actions", ["session_hash"])


def downgrade():
    op.drop_table("timer_actions")
