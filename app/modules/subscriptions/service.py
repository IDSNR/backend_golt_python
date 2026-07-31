from datetime import datetime


class SubscriptionService:
    def __init__(self) -> None:
        self.plans: dict[str, dict] = {}
        self.subscriptions: list[dict] = []

    def _now_iso(self) -> str:
        return datetime.utcnow().isoformat() + 'Z'

    def set_subscription_price(self, creator_profile_id: str, payload: dict) -> dict:
        if payload.get('priceCents') is None or payload.get('priceCents') < 0:
            raise ValueError('priceCents must be a non-negative integer')

        plan = {
            'creatorProfileId': creator_profile_id,
            'price_cents': payload['priceCents'],
            'enabled': payload.get('enabled', True),
            'updated_at': self._now_iso(),
        }
        self.plans[creator_profile_id] = plan
        return plan

    def get_plan(self, creator_profile_id: str) -> dict | None:
        return self.plans.get(creator_profile_id)

    def subscribe(self, subscriber_profile_id: str, creator_profile_id: str) -> dict:
        if creator_profile_id not in self.plans:
            self.plans[creator_profile_id] = {
                'creatorProfileId': creator_profile_id,
                'price_cents': 0,
                'enabled': True,
                'updated_at': self._now_iso(),
            }

        if not self.plans[creator_profile_id]['enabled']:
            raise ValueError('Subscriptions are not enabled for this creator')

        if any(
            sub for sub in self.subscriptions
            if sub['subscriberProfileId'] == subscriber_profile_id and sub['creatorProfileId'] == creator_profile_id and sub['status'] == 'active'
        ):
            raise ValueError('Already subscribed')

        subscription = {
            'id': f'subscription-{len(self.subscriptions) + 1}',
            'subscriberProfileId': subscriber_profile_id,
            'creatorProfileId': creator_profile_id,
            'status': 'active',
            'current_period_end': self._now_iso(),
            'created_at': self._now_iso(),
        }
        self.subscriptions.append(subscription)
        return subscription

    def cancel_subscription(self, subscriber_profile_id: str, creator_profile_id: str) -> dict:
        for sub in self.subscriptions:
            if sub['subscriberProfileId'] == subscriber_profile_id and sub['creatorProfileId'] == creator_profile_id and sub['status'] == 'active':
                sub['status'] = 'canceled'
                return sub
        raise ValueError('Subscription not found')

    def get_subscription(self, subscriber_profile_id: str, creator_profile_id: str) -> dict | None:
        return next(
            (
                sub for sub in self.subscriptions
                if sub['subscriberProfileId'] == subscriber_profile_id and sub['creatorProfileId'] == creator_profile_id
            ),
            None,
        )
