import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "ownership",
        sa.Column("marker", sa.String(80), primary_key=True),
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column(
            "receiver_id",
            sa.Integer(),
            sa.ForeignKey("receivers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("connection", sa.String(64), nullable=False),
        sa.Column("service", sa.String(2048), nullable=False),
        sa.Column("created_at", sa.Integer(), nullable=False),
    )
    op.execute("ALTER TABLE timer_actions ADD COLUMN encrypted_token TEXT")


def downgrade():
    op.execute("ALTER TABLE timer_actions DROP COLUMN encrypted_token")
    op.drop_table("ownership")
