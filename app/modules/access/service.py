class ContentAccessService:
    VALID_VISIBILITIES = {"public", "followers", "subscribers", "private"}

    def __init__(self, profile_service, social_service, subscription_service) -> None:
        self.profile_service = profile_service
        self.social_service = social_service
        self.subscription_service = subscription_service

    def can_view_creator(self, viewer_id: str | None, creator_id: str) -> bool:
        if viewer_id == creator_id:
            return True

        profile = self.profile_service.get_profile(creator_id)
        if profile is None or not profile.get("isPrivate", False):
            return True

        return bool(viewer_id and self.social_service.is_approved_follower(viewer_id, creator_id))

    def can_view_post(self, viewer_id: str | None, post: dict) -> bool:
        creator_id = post["creatorId"]
        if viewer_id == creator_id:
            return True
        if not self.can_view_creator(viewer_id, creator_id):
            return False

        visibility = post.get("visibility", "public")
        if visibility == "public":
            return True
        if visibility == "followers":
            return bool(viewer_id and self.social_service.is_approved_follower(viewer_id, creator_id))
        if visibility == "subscribers":
            if not viewer_id:
                return False
            subscription = self.subscription_service.get_subscription(viewer_id, creator_id)
            return bool(subscription and subscription.get("status") == "active")
        return False
