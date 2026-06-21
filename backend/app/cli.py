"""Tiny management CLI: create users, init db, run discovery once.

Usage:
  python -m app.cli init-db
  python -m app.cli create-user --email a@b.com --password secret --admin
  python -m app.cli discover
"""

from __future__ import annotations

import argparse

from app.db.base import Base
from app.db.session import engine, session
from app.core.security import hash_password
from app.db.models import Profile, Role, User


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    print("DB tables created.")


def create_user(email: str, password: str, full_name: str, admin: bool) -> None:
    db = session()
    try:
        if db.query(User).filter(User.email == email).first():
            print("User already exists.")
            return
        first = db.query(User).count() == 0
        user = User(
            email=email,
            hashed_password=hash_password(password),
            full_name=full_name,
            role=Role.admin if (admin or first) else Role.user,
        )
        db.add(user)
        db.flush()
        db.add(Profile(user_id=user.id))
        db.commit()
        print(f"Created {'admin' if user.role == Role.admin else 'user'}: {email}")
    finally:
        db.close()


def discover() -> None:
    from app.agents.discovery import DiscoveryAgent

    with DiscoveryAgent() as agent:
        print(agent.run())


def main() -> None:
    parser = argparse.ArgumentParser(prog="jobhunter")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init-db")
    cu = sub.add_parser("create-user")
    cu.add_argument("--email", required=True)
    cu.add_argument("--password", required=True)
    cu.add_argument("--full-name", default="")
    cu.add_argument("--admin", action="store_true")
    sub.add_parser("discover")

    args = parser.parse_args()
    if args.cmd == "init-db":
        init_db()
    elif args.cmd == "create-user":
        create_user(args.email, args.password, args.full_name, args.admin)
    elif args.cmd == "discover":
        discover()


if __name__ == "__main__":
    main()
