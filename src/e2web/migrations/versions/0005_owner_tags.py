import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "owner_tags",
        sa.Column("marker", sa.String(80), primary_key=True),
        sa.Column(
            "owner_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            unique=True,
        ),
        sa.Column("created_at", sa.Integer(), nullable=False),
    )
    # Register every existing account, even if it has never created a timer.
    # Old opaque proofs remain intact for existing timers and recording files.
    op.execute(
        "INSERT INTO owner_tags (marker, owner_id, created_at) "
        "SELECT 'e2web-owner-' || username, id, CAST(strftime('%s', 'now') AS INTEGER) FROM users"
    )


def downgrade():
    op.drop_table("owner_tags")
