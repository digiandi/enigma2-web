from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config as AlembicConfig
from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, create_engine, event
from sqlalchemy.engine import URL
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from e2web.config import Config


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(32), unique=True)
    display_name: Mapped[str] = mapped_column(String(128))
    password_hash: Mapped[str] = mapped_column(String(512))
    role: Mapped[str] = mapped_column(String(16), default="user")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=True)
    all_receivers: Mapped[bool] = mapped_column(Boolean, default=True)
    all_receivers_write: Mapped[bool] = mapped_column(Boolean, default=True)
    default_receiver_id: Mapped[int | None] = mapped_column(
        ForeignKey("receivers.id", ondelete="SET NULL"), nullable=True
    )

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"


class Receiver(Base):
    __tablename__ = "receivers"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    hostname: Mapped[str] = mapped_column(String(253))
    port: Mapped[int] = mapped_column(Integer, default=80)
    https: Mapped[bool] = mapped_column(Boolean, default=False)
    verify_tls: Mapped[bool] = mapped_column(Boolean, default=True)
    username: Mapped[str] = mapped_column(String(128), default="")
    encrypted_password: Mapped[str] = mapped_column(Text, default="")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    # Legacy column kept for compatibility with revision 0001; lists use the receiver name.
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    @property
    def base_url(self) -> str:
        host = f"[{self.hostname}]" if ":" in self.hostname else self.hostname
        return f"{'https' if self.https else 'http'}://{host}:{self.port}"


class Grant(Base):
    __tablename__ = "user_receiver_permissions"
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    receiver_id: Mapped[int] = mapped_column(
        ForeignKey("receivers.id", ondelete="CASCADE"), primary_key=True
    )
    can_write: Mapped[bool] = mapped_column(Boolean, default=True)


class WebSession(Base):
    __tablename__ = "sessions"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    expires_at: Mapped[int] = mapped_column(Integer, index=True)
    receiver_id: Mapped[int | None] = mapped_column(
        ForeignKey("receivers.id", ondelete="SET NULL"), nullable=True
    )


class LoginAttempt(Base):
    __tablename__ = "login_attempts"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(32), index=True)
    ip_address: Mapped[str] = mapped_column(String(64), index=True)
    attempted_at: Mapped[int] = mapped_column(Integer, index=True)


class AuditLog(Base):
    __tablename__ = "audit_log"
    id: Mapped[int] = mapped_column(primary_key=True)
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    action: Mapped[str] = mapped_column(String(64))
    target_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[int] = mapped_column(Integer)


class TimerAction(Base):
    __tablename__ = "timer_actions"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    session_hash: Mapped[str | None] = mapped_column(
        ForeignKey("sessions.token_hash", ondelete="SET NULL"), index=True, nullable=True
    )
    receiver_id: Mapped[int] = mapped_column(ForeignKey("receivers.id", ondelete="CASCADE"))
    kind: Mapped[str] = mapped_column(String(16))
    payload: Mapped[str] = mapped_column(Text)
    created_at: Mapped[int] = mapped_column(Integer)
    used_at: Mapped[int | None] = mapped_column(Integer, nullable=True)
    encrypted_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    # A short lease serializes receiver writes across workers without a long SQLite lock.
    locked_receiver_id: Mapped[int | None] = mapped_column(Integer, unique=True, nullable=True)
    lock_until: Mapped[int | None] = mapped_column(Integer, nullable=True)


class Ownership(Base):
    __tablename__ = "ownership"
    marker: Mapped[str] = mapped_column(String(80), primary_key=True)
    owner_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    receiver_id: Mapped[int] = mapped_column(ForeignKey("receivers.id", ondelete="CASCADE"))
    connection: Mapped[str] = mapped_column(String(64))
    service: Mapped[str] = mapped_column(String(2048))
    created_at: Mapped[int] = mapped_column(Integer)


class OwnerTag(Base):
    __tablename__ = "owner_tags"
    marker: Mapped[str] = mapped_column(String(80), primary_key=True)
    owner_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, unique=True
    )
    created_at: Mapped[int] = mapped_column(Integer)


def make_engine(config: Config):
    engine = create_engine(
        URL.create("sqlite", database=str(config.database_path)),
        connect_args={"check_same_thread": False, "timeout": 15},
    )

    @event.listens_for(engine, "connect")
    def pragmas(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA busy_timeout=15000")

    return engine


def migrate(config: Config) -> None:
    alembic = AlembicConfig()
    alembic.set_main_option("script_location", str(Path(__file__).parent / "migrations"))
    engine = make_engine(config)
    try:
        with engine.begin() as connection:
            alembic.attributes["connection"] = connection
            command.upgrade(alembic, "head")
    finally:
        engine.dispose()
