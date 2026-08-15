"""Seeds a demo organization with a fixed set of synthetic contracts so
the evaluation dataset (evaluation/datasets/qa_eval_v1.json) has a stable
corpus to test against, and so the app has something to explore in demo
mode without a manual upload.

Idempotent: re-running skips documents that already exist for the demo
org (matched by filename), so it's safe to run on every fresh `docker
compose up`. Pass --force to delete and re-upload everything.

Usage (from apps/api, with the venv active):
    python -m scripts.seed_demo_data
    python -m scripts.seed_demo_data --force
"""

import argparse
import asyncio
import sys
from pathlib import Path

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import AsyncSessionLocal
from app.models.document import Document
from app.models.organization import Organization
from app.models.user import User, UserRole
from app.services.document_service import create_document, process_document

DEMO_ORG_NAME = "ContractLens Demo"
DEMO_ORG_SLUG = "contractlens-demo-seed"
DEMO_USER_EMAIL = "demo@contractlens-demo.com"
DEMO_USER_PASSWORD = "demopassword123"
DEMO_USER_NAME = "Demo User"

_FILE_PARENTS = Path(__file__).resolve().parents
# Local checkout: .../apps/api/scripts/seed_demo_data.py -> parents[3] is
# the repo root. Docker image: /app/scripts/seed_demo_data.py has only 2
# parents, so fall back to the /evaluation mount configured in
# docker-compose.yml instead of indexing past the end of parents.
SEED_DIR = (
    _FILE_PARENTS[3] / "evaluation" / "seed_documents"
    if len(_FILE_PARENTS) > 3
    else Path("/evaluation/seed_documents")
)

SEED_FILES = [
    "master_services_agreement.txt",
    "non_disclosure_agreement.txt",
    "data_processing_agreement.txt",
    "software_license_agreement.txt",
]


async def _get_or_create_demo_org_and_user(db) -> tuple[Organization, User]:
    # User is authoritative: if the demo user already exists, use *its*
    # organization rather than independently resolving org-by-slug, so a
    # slug collision (or a stale user from unrelated testing reusing this
    # email) can never leave documents seeded into an org the demo user
    # doesn't actually belong to.
    user = await db.scalar(select(User).where(User.email == DEMO_USER_EMAIL))
    if user is not None:
        org = await db.get(Organization, user.organization_id)
        print(f"Using existing user '{DEMO_USER_EMAIL}' in org '{org.name}' ({org.id})")
        return org, user

    org = await db.scalar(select(Organization).where(Organization.slug == DEMO_ORG_SLUG))
    if org is None:
        org = Organization(name=DEMO_ORG_NAME, slug=DEMO_ORG_SLUG)
        db.add(org)
        await db.flush()
        print(f"Created organization '{DEMO_ORG_NAME}' ({org.id})")
    else:
        print(f"Using existing organization '{DEMO_ORG_NAME}' ({org.id})")

    user = User(
        email=DEMO_USER_EMAIL,
        hashed_password=hash_password(DEMO_USER_PASSWORD),
        full_name=DEMO_USER_NAME,
        role=UserRole.ADMIN,
        organization_id=org.id,
    )
    db.add(user)
    await db.flush()
    print(f"Created user '{DEMO_USER_EMAIL}' (password: {DEMO_USER_PASSWORD})")

    await db.commit()
    return org, user


async def _seed_documents(db, org: Organization, user: User, force: bool) -> None:
    if not SEED_DIR.exists():
        print(f"ERROR: seed documents directory not found at {SEED_DIR}", file=sys.stderr)
        sys.exit(1)

    for filename in SEED_FILES:
        path = SEED_DIR / filename
        if not path.exists():
            print(f"WARNING: seed file missing, skipping: {path}")
            continue

        existing = await db.scalar(
            select(Document).where(
                Document.organization_id == org.id,
                Document.filename == filename,
                Document.deleted_at.is_(None),
            )
        )
        if existing is not None and not force:
            print(f"Skipping {filename} (already seeded as {existing.id})")
            continue
        if existing is not None and force:
            await db.delete(existing)
            await db.commit()

        data = path.read_bytes()
        document = await create_document(
            db,
            organization_id=org.id,
            owner_id=user.id,
            filename=filename,
            content_type="text/plain",
            data=data,
        )
        print(f"Uploaded {filename} -> {document.id}, processing...")
        await process_document(document.id)
        print(f"  done: {filename}")


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force", action="store_true", help="Delete and re-upload documents that already exist."
    )
    args = parser.parse_args()

    async with AsyncSessionLocal() as db:
        org, user = await _get_or_create_demo_org_and_user(db)
        await _seed_documents(db, org, user, force=args.force)

    print("\nSeeding complete.")
    print(f"Log in with: {DEMO_USER_EMAIL} / {DEMO_USER_PASSWORD}")


if __name__ == "__main__":
    asyncio.run(main())
