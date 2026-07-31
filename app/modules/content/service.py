from datetime import datetime


class ContentService:
    def __init__(self) -> None:
        self.posts: list[dict] = []

    def _now_iso(self) -> str:
        return datetime.utcnow().isoformat() + 'Z'

    def create_post(self, author_id: str, payload: dict) -> dict:
        if not payload.get('videoUrl') and not payload.get('mediaItems'):
            raise ValueError('videoUrl or mediaItems is required')

        post = {
            'id': f'content-{len(self.posts) + 1}',
            'creatorId': author_id,
            'caption': payload.get('caption'),
            'videoUrl': payload.get('videoUrl'),
            'visibility': payload.get('visibility', 'public'),
            'mediaItems': payload.get('mediaItems'),
            'created_at': self._now_iso(),
            'views': 0,
            'completions': 0,
        }
        self.posts.append(post)
        return post

    def list_posts(self) -> list[dict]:
        return sorted(self.posts, key=lambda post: post['created_at'], reverse=True)

    def list_posts_by_creator(self, creator_id: str) -> list[dict]:
        return sorted(
            [post for post in self.posts if post['creatorId'] == creator_id],
            key=lambda post: post['created_at'],
            reverse=True,
        )

    def get_post(self, content_id: str) -> dict | None:
        return next((post for post in self.posts if post['id'] == content_id), None)

    def list_public_posts(self) -> list[dict]:
        return [post for post in self.posts if post.get('visibility') == 'public']
