from datetime import datetime, timedelta, timezone


class StoryService:
    def __init__(self) -> None:
        self.stories: list[dict] = []
        self.views: list[dict] = []
        self.post_story('user-1', {
            'mediaUrl': 'https://partnerhub.test/media/story1.jpg',
            'mediaType': 'image',
            'isSponsored': False,
        })
        self.post_story('user-2', {
            'mediaUrl': 'https://partnerhub.test/media/story2.mp4',
            'mediaType': 'video',
            'isSponsored': False,
        })

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')

    def post_story(self, creator_id: str, payload: dict) -> dict:
        if not payload.get('mediaUrl'):
            raise ValueError('mediaUrl is required')

        story = {
            'id': f'story-{len(self.stories) + 1}',
            'creatorId': creator_id,
            'mediaType': payload.get('mediaType'),
            'mediaUrl': payload.get('mediaUrl'),
            'isSponsored': payload.get('isSponsored', False),
            'created_at': self._now_iso(),
            'expiresAt': (datetime.now(timezone.utc) + timedelta(hours=24)).replace(microsecond=0).isoformat().replace('+00:00', 'Z'),
        }
        self.stories.append(story)
        return story

    def get_active_stories(self, creator_id: str) -> list[dict]:
        now = datetime.now(timezone.utc)
        return [
            story for story in self.stories
            if story['creatorId'] == creator_id and datetime.fromisoformat(story['expiresAt'].replace('Z', '+00:00')) > now
        ]

    def record_story_view(self, story_id: str, viewer_profile_id: str) -> None:
        story = self.get_story(story_id)
        if story is None:
            raise ValueError('Story not found')
        self.views.append({
            'story_id': story_id,
            'viewer_profile_id': viewer_profile_id,
            'viewed_at': self._now_iso(),
        })

    def get_story_viewers(self, story_id: str) -> list[dict]:
        if self.get_story(story_id) is None:
            raise ValueError('Story not found')
        return [
            {'viewerProfileId': view['viewer_profile_id'], 'viewed_at': view['viewed_at']}
            for view in self.views
            if view['story_id'] == story_id
        ]

    def get_story(self, story_id: str) -> dict | None:
        return next((story for story in self.stories if story['id'] == story_id), None)
