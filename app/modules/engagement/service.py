from datetime import datetime, timezone


class EngagementService:
    def __init__(self) -> None:
        self.likes: set[tuple[str, str]] = set()
        self.bookmarks: set[tuple[str, str]] = set()
        self.shares: list[dict] = []
        self.comments: dict[str, list[dict]] = {}
        self.next_comment_id = 1

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')

    def _comment_count(self, content_id: str) -> int:
        return len(self.comments.get(content_id, []))

    def get_summary(self, content_id: str, account_id: str | None = None) -> dict:
        return {
            'contentId': content_id,
            'likes': sum(1 for _, target_id in self.likes if target_id == content_id),
            'comments': self._comment_count(content_id),
            'shares': sum(1 for share in self.shares if share['contentId'] == content_id),
            'bookmarks': sum(1 for _, target_id in self.bookmarks if target_id == content_id),
            'likedByViewer': bool(account_id and (account_id, content_id) in self.likes),
            'bookmarkedByViewer': bool(account_id and (account_id, content_id) in self.bookmarks),
        }

    def like(self, account_id: str, content_id: str) -> dict:
        self.likes.add((account_id, content_id))
        return self.get_summary(content_id, account_id)

    def unlike(self, account_id: str, content_id: str) -> dict:
        self.likes.discard((account_id, content_id))
        return self.get_summary(content_id, account_id)

    def bookmark(self, account_id: str, content_id: str) -> dict:
        self.bookmarks.add((account_id, content_id))
        return self.get_summary(content_id, account_id)

    def unbookmark(self, account_id: str, content_id: str) -> dict:
        self.bookmarks.discard((account_id, content_id))
        return self.get_summary(content_id, account_id)

    def share(self, account_id: str, content_id: str) -> dict:
        share = {
            'id': f'share-{len(self.shares) + 1}',
            'accountId': account_id,
            'contentId': content_id,
            'created_at': self._now_iso(),
        }
        self.shares.append(share)
        return share

    def add_comment(self, account_id: str, content_id: str, body: str, parent_comment_id: str | None = None) -> dict:
        cleaned = body.strip()
        if not cleaned:
            raise ValueError('comment body is required')
        comment = {
            'id': f'comment-{self.next_comment_id}',
            'contentId': content_id,
            'accountId': account_id,
            'body': cleaned,
            'parentCommentId': parent_comment_id,
            'created_at': self._now_iso(),
        }
        self.next_comment_id += 1
        self.comments.setdefault(content_id, []).append(comment)
        return comment

    def list_comments(self, content_id: str) -> list[dict]:
        return list(reversed(self.comments.get(content_id, [])))
