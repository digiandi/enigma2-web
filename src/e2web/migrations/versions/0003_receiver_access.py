from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade():
    # SQLite accepts an inline nullable FK on ADD COLUMN. Rebuilding users with
    # batch_alter_table would trigger cascading deletion of grants and sessions.
    op.execute(
        "ALTER TABLE users ADD COLUMN default_receiver_id INTEGER "
        "REFERENCES receivers(id) ON DELETE SET NULL"
    )
    op.execute("ALTER TABLE users ADD COLUMN all_receivers_write BOOLEAN NOT NULL DEFAULT 1")
    op.execute(
        "ALTER TABLE user_receiver_permissions ADD COLUMN can_write BOOLEAN NOT NULL DEFAULT 1"
    )


def downgrade():
    op.execute("ALTER TABLE user_receiver_permissions DROP COLUMN can_write")
    op.execute("ALTER TABLE users DROP COLUMN all_receivers_write")
    op.execute("ALTER TABLE users DROP COLUMN default_receiver_id")
