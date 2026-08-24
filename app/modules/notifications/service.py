from datetime import datetime, timezone


class NotificationService:
    def __init__(self) -> None:
        self.notifications: list[dict] = []

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')

    def send_notification(self, recipient_profile_id: str, notification_type: str, payload: dict) -> dict:
        notification = {
            'id': f'notification-{len(self.notifications) + 1}',
            'recipient_profile_id': recipient_profile_id,
            'type': notification_type,
            'payload': payload,
            'created_at': self._now_iso(),
            'read_at': None,
        }
        self.notifications.append(notification)
        return notification

    def list_for_recipient(self, recipient_id: str) -> list[dict]:
        return sorted(
            [n for n in self.notifications if n['recipient_profile_id'] == recipient_id],
            key=lambda n: n['created_at'],
            reverse=True,
        )

    def count_unread(self, recipient_id: str) -> int:
        return sum(
            1 for n in self.notifications
            if n['recipient_profile_id'] == recipient_id and n.get('read_at') is None
        )

    def mark_read(self, notification_id: str, recipient_id: str) -> None:
        for notification in self.notifications:
            if notification['id'] == notification_id and notification['recipient_profile_id'] == recipient_id:
                notification['read_at'] = self._now_iso()
                return
        raise ValueError('Notification not found')
