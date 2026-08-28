from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import delete, func, insert, select, update
from sqlalchemy.exc import IntegrityError

from .database import engine
from .runtime_schema import accounts, comments, engagements, follows, moderation_reports, posts, profiles


def persistence_enabled() -> bool:
    return os.getenv('PERSISTENCE_ENABLED', 'false').lower() == 'true'


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)


def iso(value: datetime | None) -> str | None:
    return value.isoformat() + 'Z' if value else None


class PlatformRepository:
    def create_moderation_report(self, report: dict) -> dict:
        now = utc_now()
        with engine.begin() as connection:
            connection.execute(insert(moderation_reports).values(
                id=report['id'], reporter_id=report['reporterId'], target_type=report['targetType'],
                target_id=report['targetId'], reason=report['reason'], status='open',
                created_at=now, updated_at=now,
            ))
        return self.get_moderation_report(report['id']) or report

    def get_moderation_report(self, report_id: str) -> dict | None:
        with engine.connect() as connection:
            row = connection.execute(select(moderation_reports).where(moderation_reports.c.id == report_id)).mappings().first()
        return self._moderation_report_dict(dict(row)) if row else None

    def list_moderation_reports(self, status: str = 'open', limit: int = 100) -> list[dict]:
        query = select(moderation_reports).where(moderation_reports.c.status == status).order_by(moderation_reports.c.created_at.asc()).limit(limit)
        with engine.connect() as connection:
            rows = connection.execute(query).mappings().all()
        return [self._moderation_report_dict(dict(row)) for row in rows]

    def update_moderation_report(self, report_id: str, status: str, moderator_id: str, notes: str | None = None) -> dict:
        with engine.begin() as connection:
            result = connection.execute(update(moderation_reports).where(moderation_reports.c.id == report_id).values(
                status=status, moderator_id=moderator_id, notes=notes, updated_at=utc_now(),
            ))
            if result.rowcount == 0:
                raise LookupError('report not found')
        return self.get_moderation_report(report_id) or {}

    def _moderation_report_dict(self, row: dict) -> dict:
        return {
            'id': row['id'], 'reporterId': row['reporter_id'], 'targetType': row['target_type'],
            'targetId': row['target_id'], 'reason': row['reason'], 'status': row['status'],
            'moderatorId': row['moderator_id'], 'notes': row['notes'],
            'createdAt': iso(row['created_at']), 'updatedAt': iso(row['updated_at']),
        }

    def create_account(self, account_id: str, email: str, display_name: str, password_hash: str | None, provider: str) -> dict:
        now = utc_now()
        with engine.begin() as connection:
            existing = connection.execute(select(accounts.c.id).where(accounts.c.id == account_id)).first()
            if not existing:
                connection.execute(insert(accounts).values(id=account_id, email=email, display_name=display_name, password_hash=password_hash, auth_provider=provider, is_active=True, created_at=now))
        return self.get_account(account_id) or {}

    def get_account(self, account_id: str) -> dict | None:
        with engine.connect() as connection:
            row = connection.execute(select(accounts).where(accounts.c.id == account_id)).mappings().first()
        return dict(row) if row else None

    def get_account_by_email(self, email: str) -> dict | None:
        with engine.connect() as connection:
            row = connection.execute(select(accounts).where(accounts.c.email == email)).mappings().first()
        return dict(row) if row else None

    def upsert_profile(self, profile: dict) -> dict:
        now = utc_now()
        values = {
            'account_id': profile['id'], 'handle': profile['handle'], 'account_type': profile.get('accountType', 'standard'),
            'display_name': profile.get('displayName') or profile['handle'], 'bio': profile.get('bio'), 'avatar_url': profile.get('avatarUrl'),
            'banner_url': profile.get('bannerUrl'), 'website_url': profile.get('websiteUrl'), 'location': profile.get('location'),
            'pronouns': profile.get('pronouns'), 'is_private': profile.get('isPrivate', False), 'created_at': now, 'updated_at': now,
        }
        with engine.begin() as connection:
            existing = connection.execute(select(profiles).where(profiles.c.account_id == profile['id'])).first()
            if existing:
                connection.execute(update(profiles).where(profiles.c.account_id == profile['id']).values(**{key: value for key, value in values.items() if key not in {'account_id', 'created_at'}}))
            else:
                account_exists = connection.execute(select(accounts.c.id).where(accounts.c.id == profile['id'])).first()
                if not account_exists:
                    connection.execute(insert(accounts).values(id=profile['id'], email=None, display_name=values['display_name'], password_hash=None, auth_provider='profile', is_active=True, created_at=now))
                connection.execute(insert(profiles).values(**values))
        return self.get_profile(profile['id']) or profile

    def get_profile(self, account_id: str) -> dict | None:
        with engine.connect() as connection:
            row = connection.execute(select(profiles).where(profiles.c.account_id == account_id)).mappings().first()
        if not row:
            return None
        return self._profile_dict(dict(row))

    def get_profile_by_handle(self, handle: str) -> dict | None:
        with engine.connect() as connection:
            row = connection.execute(select(profiles).where(profiles.c.handle == handle.lower())).mappings().first()
        return self._profile_dict(dict(row)) if row else None

    def _profile_dict(self, row: dict) -> dict:
        return {'id': row['account_id'], 'handle': row['handle'], 'accountType': row['account_type'], 'displayName': row['display_name'], 'bio': row['bio'], 'avatarUrl': row['avatar_url'], 'bannerUrl': row['banner_url'], 'websiteUrl': row['website_url'], 'location': row['location'], 'pronouns': row['pronouns'], 'isPrivate': row['is_private'], 'createdAt': iso(row['created_at']), 'updatedAt': iso(row['updated_at'])}

    def create_post(self, post: dict) -> dict:
        with engine.begin() as connection:
            values = {'account_id': post['creatorId'], 'caption': post.get('caption'), 'video_url': post.get('videoUrl'), 'media_items_json': json.dumps(post.get('mediaItems')), 'visibility': post.get('visibility', 'public'), 'views': post.get('views', 0), 'completions': post.get('completions', 0), 'created_at': utc_now()}
            existing = connection.execute(select(posts.c.id).where(posts.c.id == post['id'])).first()
            if existing:
                connection.execute(update(posts).where(posts.c.id == post['id']).values(**{key: value for key, value in values.items() if key != 'created_at'}))
            else:
                connection.execute(insert(posts).values(id=post['id'], **values))
        return post

    def list_posts(self, account_id: str | None = None, public_only: bool = False) -> list[dict]:
        query = select(posts).order_by(posts.c.created_at.desc())
        if account_id:
            query = query.where(posts.c.account_id == account_id)
        if public_only:
            query = query.where(posts.c.visibility == 'public')
        with engine.connect() as connection:
            rows = connection.execute(query).mappings().all()
        return [self._post_dict(dict(row)) for row in rows]

    def get_post(self, post_id: str) -> dict | None:
        with engine.connect() as connection:
            row = connection.execute(select(posts).where(posts.c.id == post_id)).mappings().first()
        return self._post_dict(dict(row)) if row else None

    def _post_dict(self, row: dict) -> dict:
        return {'id': row['id'], 'creatorId': row['account_id'], 'caption': row['caption'], 'videoUrl': row['video_url'], 'mediaItems': json.loads(row['media_items_json']) if row['media_items_json'] else None, 'visibility': row['visibility'], 'views': row['views'], 'completions': row['completions'], 'created_at': iso(row['created_at'])}

    def follow(self, follower_id: str, followee_id: str, status: str) -> dict:
        now = utc_now()
        with engine.begin() as connection:
            existing = connection.execute(select(follows).where(follows.c.follower_id == follower_id, follows.c.followee_id == followee_id)).first()
            if existing:
                connection.execute(update(follows).where(follows.c.follower_id == follower_id, follows.c.followee_id == followee_id).values(status=status))
            else:
                connection.execute(insert(follows).values(follower_id=follower_id, followee_id=followee_id, status=status, created_at=now))
        return {'followerId': follower_id, 'followeeId': followee_id, 'status': status}

    def follower_count(self, followee_id: str) -> int:
        with engine.connect() as connection:
            return int(connection.execute(select(func.count()).select_from(follows).where(follows.c.followee_id == followee_id, follows.c.status == 'approved')).scalar_one())

    def following_count(self, follower_id: str) -> int:
        with engine.connect() as connection:
            return int(connection.execute(select(func.count()).select_from(follows).where(follows.c.follower_id == follower_id, follows.c.status == 'approved')).scalar_one())

    def relationship_status(self, viewer_id: str, followee_id: str) -> str:
        with engine.connect() as connection:
            row = connection.execute(select(follows.c.status).where(follows.c.follower_id == viewer_id, follows.c.followee_id == followee_id)).scalar_one_or_none()
        if row == 'approved':
            return 'following'
        if row == 'pending':
            return 'requested'
        return 'none'

    def engagement_toggle(self, account_id: str, post_id: str, kind: str, enabled: bool) -> None:
        with engine.begin() as connection:
            query = select(engagements).where(engagements.c.account_id == account_id, engagements.c.post_id == post_id, engagements.c.kind == kind)
            exists = connection.execute(query).first()
            if enabled and not exists:
                connection.execute(insert(engagements).values(account_id=account_id, post_id=post_id, kind=kind, created_at=utc_now()))
            elif not enabled and exists:
                connection.execute(delete(engagements).where(engagements.c.account_id == account_id, engagements.c.post_id == post_id, engagements.c.kind == kind))

    def add_comment(self, account_id: str, post_id: str, body: str, parent_id: int | None = None) -> dict:
        with engine.begin() as connection:
            row = connection.execute(insert(comments).values(account_id=account_id, post_id=post_id, body=body, parent_id=parent_id, created_at=utc_now()).returning(comments)).mappings().one()
        return dict(row)

    def engagement_summary(self, account_id: str | None, post_id: str) -> dict:
        with engine.connect() as connection:
            rows = connection.execute(select(engagements.c.kind, func.count()).where(engagements.c.post_id == post_id).group_by(engagements.c.kind)).all()
            viewer = connection.execute(select(engagements.c.kind).where(engagements.c.account_id == account_id, engagements.c.post_id == post_id)).scalars().all() if account_id else []
        counts = {kind: int(count) for kind, count in rows}
        return {'contentId': post_id, 'likes': counts.get('like', 0), 'bookmarks': counts.get('bookmark', 0), 'shares': counts.get('share', 0), 'comments': len(self.list_comments(post_id)), 'likedByViewer': 'like' in viewer, 'bookmarkedByViewer': 'bookmark' in viewer}

    def list_comments(self, post_id: str) -> list[dict]:
        with engine.connect() as connection:
            return [dict(row) for row in connection.execute(select(comments).where(comments.c.post_id == post_id).order_by(comments.c.created_at.desc())).mappings().all()]


repository = PlatformRepository()
