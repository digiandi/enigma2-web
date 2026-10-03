import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("username", sa.String(32), unique=True, nullable=False),
        sa.Column("display_name", sa.String(128), nullable=False),
        sa.Column("password_hash", sa.String(512), nullable=False),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("active", sa.Boolean, nullable=False),
        sa.Column("must_change_password", sa.Boolean, nullable=False),
        sa.Column("all_receivers", sa.Boolean, nullable=False),
        sa.CheckConstraint("role IN ('admin', 'user')", name="ck_users_role"),
    )
    op.create_table(
        "receivers",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("hostname", sa.String(253), nullable=False),
        sa.Column("port", sa.Integer, nullable=False),
        sa.Column("https", sa.Boolean, nullable=False),
        sa.Column("verify_tls", sa.Boolean, nullable=False),
        sa.Column("username", sa.String(128), nullable=False),
        sa.Column("encrypted_password", sa.Text, nullable=False),
        sa.Column("enabled", sa.Boolean, nullable=False),
        sa.Column("sort_order", sa.Integer, nullable=False),
        sa.CheckConstraint("port BETWEEN 1 AND 65535", name="ck_receiver_port"),
    )
    op.create_table(
        "user_receiver_permissions",
        sa.Column(
            "user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
        ),
        sa.Column(
            "receiver_id",
            sa.Integer,
            sa.ForeignKey("receivers.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )
    op.create_table(
        "sessions",
        sa.Column("token_hash", sa.String(64), primary_key=True),
        sa.Column(
            "user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("expires_at", sa.Integer, nullable=False),
        sa.Column("receiver_id", sa.Integer, sa.ForeignKey("receivers.id", ondelete="SET NULL")),
    )
    op.create_index("ix_sessions_user_id", "sessions", ["user_id"])
    op.create_index("ix_sessions_expires_at", "sessions", ["expires_at"])
    op.create_table(
        "login_attempts",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("username", sa.String(32), nullable=False),
        sa.Column("ip_address", sa.String(64), nullable=False),
        sa.Column("attempted_at", sa.Integer, nullable=False),
    )
    for name in ["username", "ip_address", "attempted_at"]:
        op.create_index(f"ix_login_attempts_{name}", "login_attempts", [name])
    op.create_table(
        "audit_log",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("actor_id", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("target_id", sa.Integer),
        sa.Column("created_at", sa.Integer, nullable=False),
    )


def downgrade():
    for table in [
        "audit_log",
        "login_attempts",
        "sessions",
        "user_receiver_permissions",
        "receivers",
        "users",
    ]:
        op.drop_table(table)
