from datetime import datetime


class StoryService:
    def __init__(self) -> None:
        self.stories: list[dict] = []
        self.views: list[dict] = []

    def _now_iso(self) -> str:
        return datetime.utcnow().isoformat() + 'Z'

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
        }
        self.stories.append(story)
        return story

    def get_active_stories(self, creator_id: str) -> list[dict]:
        return [story for story in self.stories if story['creatorId'] == creator_id]

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
