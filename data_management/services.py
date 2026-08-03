from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import SessionLocal
from .models import (
    Account,
    AccountBalance,
    AccountLedgerEntry,
    AccountMetadata,
    AuthIdentity,
    Circle,
    CircleMember,
    Comment,
    DirectMessage,
    DirectMessageThread,
    DirectMessageThreadParticipant,
    Follow,
    Notification,
    Post,
    Story,
    UserProfile,
)


def create_account_and_profile(
    *,
    username: str,
    email: Optional[str] = None,
    display_name: Optional[str] = None,
    auth_provider: str = "email",
    password_hash: Optional[str] = None,
    provider_user_id: Optional[str] = None,
    biography: Optional[str] = None,
    website_url: Optional[str] = None,
    location: Optional[str] = None,
    pronouns: Optional[str] = None,
    avatar_url: Optional[str] = None,
    banner_url: Optional[str] = None,
    session: Optional[Session] = None,
) -> Account:
    db = session or SessionLocal()
    try:
        account = Account(
            username=username,
            email=email,
            display_name=display_name or username,
            auth_provider=auth_provider,
        )
        db.add(account)
        db.flush()

        profile = UserProfile(
            account_id=account.id,
            biography=biography,
            website_url=website_url,
            location=location,
            pronouns=pronouns,
            avatar_url=avatar_url,
            banner_url=banner_url,
        )
        db.add(profile)

        balance = AccountBalance(account_id=account.id, available_balance=0, pending_balance=0, reserved_balance=0)
        db.add(balance)

        identity = AuthIdentity(
            account_id=account.id,
            provider=auth_provider,
            provider_user_id=provider_user_id,
            email=email,
            password_hash=password_hash,
            is_primary=True,
        )
        db.add(identity)

        db.commit()
        db.refresh(account)
        return account
    finally:
        if session is None:
            db.close()


def get_account_by_id(account_id: int, session: Optional[Session] = None) -> Optional[Account]:
    db = session or SessionLocal()
    try:
        return db.get(Account, account_id)
    finally:
        if session is None:
            db.close()


def get_account_by_username(username: str, session: Optional[Session] = None) -> Optional[Account]:
    db = session or SessionLocal()
    try:
        return db.execute(select(Account).where(Account.username == username)).scalar_one_or_none()
    finally:
        if session is None:
            db.close()


def get_account_by_email(email: str, session: Optional[Session] = None) -> Optional[Account]:
    db = session or SessionLocal()
    try:
        return db.execute(select(Account).where(Account.email == email)).scalar_one_or_none()
    finally:
        if session is None:
            db.close()


def update_user_profile(
    *,
    account_id: int,
    biography: Optional[str] = None,
    website_url: Optional[str] = None,
    location: Optional[str] = None,
    pronouns: Optional[str] = None,
    avatar_url: Optional[str] = None,
    banner_url: Optional[str] = None,
    session: Optional[Session] = None,
) -> Optional[UserProfile]:
    db = session or SessionLocal()
    try:
        profile = db.execute(select(UserProfile).where(UserProfile.account_id == account_id)).scalar_one_or_none()
        if not profile:
            profile = UserProfile(account_id=account_id)
            db.add(profile)
        if biography is not None:
            profile.biography = biography
        if website_url is not None:
            profile.website_url = website_url
        if location is not None:
            profile.location = location
        if pronouns is not None:
            profile.pronouns = pronouns
        if avatar_url is not None:
            profile.avatar_url = avatar_url
        if banner_url is not None:
            profile.banner_url = banner_url
        db.commit()
        db.refresh(profile)
        return profile
    finally:
        if session is None:
            db.close()


def get_user_profile(account_id: int, session: Optional[Session] = None) -> Optional[UserProfile]:
    db = session or SessionLocal()
    try:
        return db.execute(select(UserProfile).where(UserProfile.account_id == account_id)).scalar_one_or_none()
    finally:
        if session is None:
            db.close()


def set_user_metadata(account_id: int, key: str, value: Any, value_type: str = "string", session: Optional[Session] = None) -> AccountMetadata:
    db = session or SessionLocal()
    try:
        metadata = db.execute(select(AccountMetadata).where(AccountMetadata.account_id == account_id, AccountMetadata.key == key)).scalar_one_or_none()
        if metadata is None:
            metadata = AccountMetadata(account_id=account_id, key=key, value=str(value), value_type=value_type)
            db.add(metadata)
        else:
            metadata.value = str(value)
            metadata.value_type = value_type
        db.commit()
        db.refresh(metadata)
        return metadata
    finally:
        if session is None:
            db.close()


def retrieve_user_metadata(account_id: int, key: Optional[str] = None, session: Optional[Session] = None) -> list[AccountMetadata] | AccountMetadata | None:
    db = session or SessionLocal()
    try:
        query = select(AccountMetadata).where(AccountMetadata.account_id == account_id)
        if key is not None:
            query = query.where(AccountMetadata.key == key)
        items = db.execute(query).scalars().all()
        if key is not None:
            return items[0] if items else None
        return items
    finally:
        if session is None:
            db.close()


def create_post(
    *,
    account_id: int,
    content_text: Optional[str] = None,
    parent_post_id: Optional[int] = None,
    visibility: str = "public",
    session: Optional[Session] = None,
) -> Post:
    db = session or SessionLocal()
    try:
        post = Post(account_id=account_id, content_text=content_text, parent_post_id=parent_post_id, visibility=visibility)
        db.add(post)
        db.commit()
        db.refresh(post)
        return post
    finally:
        if session is None:
            db.close()


def create_story(
    *,
    account_id: int,
    media_url: Optional[str] = None,
    media_type: str = "image",
    caption: Optional[str] = None,
    expires_in_seconds: int = 86400,
    session: Optional[Session] = None,
) -> Story:
    db = session or SessionLocal()
    try:
        story = Story(
            account_id=account_id,
            media_url=media_url,
            media_type=media_type,
            caption=caption,
            expires_at=datetime.utcnow() + timedelta(seconds=expires_in_seconds),
        )
        db.add(story)
        db.commit()
        db.refresh(story)
        return story
    finally:
        if session is None:
            db.close()


def follow_account(follower_account_id: int, followed_account_id: int, session: Optional[Session] = None) -> Follow:
    db = session or SessionLocal()
    try:
        follow = Follow(follower_account_id=follower_account_id, followed_account_id=followed_account_id)
        db.add(follow)
        db.commit()
        db.refresh(follow)
        return follow
    finally:
        if session is None:
            db.close()


def create_circle(*, owner_account_id: int, name: str, slug: str, description: Optional[str] = None, is_private: bool = False, session: Optional[Session] = None) -> Circle:
    db = session or SessionLocal()
    try:
        circle = Circle(owner_account_id=owner_account_id, name=name, slug=slug, description=description, is_private=is_private)
        db.add(circle)
        db.commit()
        db.refresh(circle)
        return circle
    finally:
        if session is None:
            db.close()


def add_circle_member(circle_id: int, account_id: int, role: str = "member", session: Optional[Session] = None) -> CircleMember:
    db = session or SessionLocal()
    try:
        member = CircleMember(circle_id=circle_id, account_id=account_id, role=role)
        db.add(member)
        db.commit()
        db.refresh(member)
        return member
    finally:
        if session is None:
            db.close()


def send_direct_message(*, thread_id: Optional[int], sender_account_id: int, content: str, session: Optional[Session] = None) -> DirectMessage:
    db = session or SessionLocal()
    try:
        if thread_id is None:
            thread = DirectMessageThread(created_by_account_id=sender_account_id)
            db.add(thread)
            db.flush()
            thread_id = thread.id
            for account_id in [sender_account_id]:
                db.add(DirectMessageThreadParticipant(thread_id=thread.id, account_id=account_id))
        message = DirectMessage(thread_id=thread_id, sender_account_id=sender_account_id, content=content)
        db.add(message)
        db.commit()
        db.refresh(message)
        return message
    finally:
        if session is None:
            db.close()


def get_user_balance(account_id: int, session: Optional[Session] = None) -> Optional[AccountBalance]:
    db = session or SessionLocal()
    try:
        return db.get(AccountBalance, account_id)
    finally:
        if session is None:
            db.close()


def record_balance_entry(
    *,
    account_id: int,
    entry_type: str,
    amount: float,
    reason: str,
    reference_type: Optional[str] = None,
    reference_id: Optional[str] = None,
    status: str = "posted",
    session: Optional[Session] = None,
) -> AccountLedgerEntry:
    db = session or SessionLocal()
    try:
        balance = db.get(AccountBalance, account_id)
        if balance is None:
            balance = AccountBalance(account_id=account_id)
            db.add(balance)
            db.flush()

        if entry_type == "credit":
            balance.available_balance = balance.available_balance + amount
        elif entry_type == "debit":
            balance.available_balance = balance.available_balance - amount

        entry = AccountLedgerEntry(
            account_id=account_id,
            entry_type=entry_type,
            amount=amount,
            reason=reason,
            reference_type=reference_type,
            reference_id=reference_id,
            status=status,
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry
    finally:
        if session is None:
            db.close()
