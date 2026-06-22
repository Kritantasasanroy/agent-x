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


def autopilot() -> None:
    """Run the full loop once, synchronously (no Redis/Celery needed).

    Ideal entrypoint for a free scheduler (e.g. GitHub Actions cron): discover ->
    score -> tailor -> apply for every active, non-paused user -> send due follow-ups.
    """
    from app.agents.discovery import DiscoveryAgent
    from app.agents.outreach import OutreachAgent
    from app.agents.pipeline import process_user_applications
    from app.db.models import User

    db = session()
    try:
        with DiscoveryAgent(db) as disc:
            disc_result = disc.run()
        print(f"discovery: {disc_result}")

        users = db.query(User).filter(User.is_active.is_(True)).all()
        for user in users:
            result = process_user_applications(db, user)
            print(f"applications[{user.email}]: {result}")

        sent = OutreachAgent(db).process_followups()
        print(f"outreach_followups_sent: {sent}")
    finally:
        db.close()


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
    sub.add_parser("autopilot")

    args = parser.parse_args()
    if args.cmd == "init-db":
        init_db()
    elif args.cmd == "create-user":
        create_user(args.email, args.password, args.full_name, args.admin)
    elif args.cmd == "discover":
        discover()
    elif args.cmd == "autopilot":
        autopilot()


if __name__ == "__main__":
    main()
