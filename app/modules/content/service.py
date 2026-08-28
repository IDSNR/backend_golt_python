from datetime import datetime, timezone
import os


class ContentService:
    def __init__(self) -> None:
        self.posts: list[dict] = []
        self.persistence = os.getenv('PERSISTENCE_ENABLED', 'false').lower() == 'true'
        self.create_post('user-1', {
            'caption': 'Golden hour in the city.',
            'mediaItems': [
                {'id': 'media-1', 'mediaType': 'image', 'url': 'https://partnerhub.test/media/sample1.jpg', 'orderIndex': 0},
            ],
        })
        self.create_post('user-2', {
            'caption': 'Quick creator reel: day in the studio.',
            'videoUrl': 'https://partnerhub.test/media/sample-video.mp4',
        })

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')

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
        if self.persistence:
            from data_management.repositories import repository
            if repository.get_account(author_id) is None:
                repository.create_account(author_id, None, author_id, None, 'profile')
            repository.create_post(post)
        return post

    def list_posts(self) -> list[dict]:
        if self.persistence:
            from data_management.repositories import repository
            return repository.list_posts()
        return sorted(self.posts, key=lambda post: post['created_at'], reverse=True)

    def list_posts_by_creator(self, creator_id: str) -> list[dict]:
        if self.persistence:
            from data_management.repositories import repository
            return repository.list_posts(creator_id)
        return sorted(
            [post for post in self.posts if post['creatorId'] == creator_id],
            key=lambda post: post['created_at'],
            reverse=True,
        )

    def get_post(self, content_id: str) -> dict | None:
        if self.persistence:
            from data_management.repositories import repository
            return repository.get_post(content_id)
        return next((post for post in self.posts if post['id'] == content_id), None)

    def list_public_posts(self) -> list[dict]:
        if self.persistence:
            from data_management.repositories import repository
            return repository.list_posts(public_only=True)
        return [post for post in self.posts if post.get('visibility') == 'public']
