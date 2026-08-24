from datetime import datetime, timezone


class SocialService:
    def __init__(self) -> None:
        self.follow_requests: list[dict] = []
        self.followers: dict[str, set[str]] = {}

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')

    def follow(self, follower_id: str, followee_id: str, followee_is_private: bool = True) -> dict:
        if follower_id == followee_id:
            raise ValueError('Users cannot follow themselves')

        request = {
            'id': f'follow-{len(self.follow_requests) + 1}',
            'followerId': follower_id,
            'followeeId': followee_id,
            'status': 'pending',
            'created_at': self._now_iso(),
        }
        self.follow_requests.append(request)

        if not followee_is_private:
            request['status'] = 'approved'
            self.followers.setdefault(followee_id, set()).add(follower_id)

        return request

    def list_follow_requests(self, followee_id: str) -> list[dict]:
        return [
            request for request in self.follow_requests
            if request['followeeId'] == followee_id and request['status'] == 'pending'
        ]

    def approve(self, request_id: str, acting_followee_id: str | None = None) -> dict:
        for request in self.follow_requests:
            if request['id'] == request_id:
                if acting_followee_id is not None and request['followeeId'] != acting_followee_id:
                    raise ValueError('Follow request not found')
                request['status'] = 'approved'
                self.followers.setdefault(request['followeeId'], set()).add(request['followerId'])
                return request
        raise ValueError('Follow request not found')

    def deny(self, request_id: str, acting_followee_id: str | None = None) -> dict:
        for request in self.follow_requests:
            if request['id'] == request_id:
                if acting_followee_id is not None and request['followeeId'] != acting_followee_id:
                    raise ValueError('Follow request not found')
                request['status'] = 'denied'
                return request
        raise ValueError('Follow request not found')

    def get_request_for(self, followee_id: str, follower_id: str) -> dict | None:
        return next(
            (
                request for request in self.follow_requests
                if request['followeeId'] == followee_id and request['followerId'] == follower_id and request['status'] == 'pending'
            ),
            None,
        )

    def approve_by_follower(self, followee_id: str, follower_id: str) -> dict:
        request = self.get_request_for(followee_id, follower_id)
        if request is None:
            raise ValueError('Follow request not found')
        request['status'] = 'approved'
        self.followers.setdefault(followee_id, set()).add(follower_id)
        return request

    def deny_by_follower(self, followee_id: str, follower_id: str) -> dict:
        request = self.get_request_for(followee_id, follower_id)
        if request is None:
            raise ValueError('Follow request not found')
        request['status'] = 'denied'
        return request

    def unfollow(self, follower_id: str, followee_id: str) -> None:
        followers = self.followers.get(followee_id)
        if followers and follower_id in followers:
            followers.remove(follower_id)

    def is_approved_follower(self, viewer_id: str, creator_id: str) -> bool:
        return viewer_id in self.followers.get(creator_id, set())

    def follower_count(self, followee_id: str) -> int:
        return len(self.followers.get(followee_id, set()))

    def following_count(self, follower_id: str) -> int:
        return sum(1 for followers in self.followers.values() if follower_id in followers)

    def relationship_status(self, viewer_id: str | None, profile_id: str) -> str:
        if viewer_id is None:
            return 'none'
        if self.is_approved_follower(viewer_id, profile_id):
            return 'following'
        request = self.get_request_for(profile_id, viewer_id)
        return 'requested' if request else 'none'
