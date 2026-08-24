from datetime import datetime, timezone
from typing import Any


class DirectMessageService:
    def __init__(self) -> None:
        self.threads: dict[str, dict] = {}
        self.messages: dict[str, list[dict]] = {}
        self.next_thread_id = 1
        self.next_message_id = 1

        # Seed a sample conversation for demo purposes.
        self.create_thread('demo-1', 'demo-2', 'Hi there! This is a demo direct message.')

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')

    def _next_thread_id(self) -> str:
        value = f'thread-{self.next_thread_id}'
        self.next_thread_id += 1
        return value

    def _next_message_id(self) -> str:
        value = f'message-{self.next_message_id}'
        self.next_message_id += 1
        return value

    def _create_message(self, thread_id: str, sender_id: str, content: str) -> dict:
        return {
            'id': self._next_message_id(),
            'threadId': thread_id,
            'senderId': sender_id,
            'content': content,
            'created_at': self._now_iso(),
        }

    def create_thread(self, sender_id: str, recipient_id: str, initial_message: str) -> dict:
        if sender_id == recipient_id:
            raise ValueError('Cannot create a thread with yourself')

        thread_id = self._next_thread_id()
        thread = {
            'id': thread_id,
            'participantIds': [sender_id, recipient_id],
            'created_at': self._now_iso(),
            'updated_at': self._now_iso(),
        }
        self.threads[thread_id] = thread
        message = self._create_message(thread_id, sender_id, initial_message)
        self.messages[thread_id] = [message]
        return thread

    def list_threads(self, user_id: str) -> list[dict]:
        result = []
        for thread in self.threads.values():
            if user_id in thread['participantIds']:
                thread_messages = self.messages.get(thread['id'], [])
                last_message = thread_messages[-1] if thread_messages else None
                result.append({
                    'id': thread['id'],
                    'participantIds': thread['participantIds'],
                    'lastMessage': last_message['content'] if last_message else '',
                    'updatedAt': thread['updated_at'],
                })
        return sorted(result, key=lambda item: item['updatedAt'], reverse=True)

    def get_thread(self, thread_id: str, user_id: str) -> dict:
        thread = self.threads.get(thread_id)
        if thread is None:
            raise ValueError('Thread not found')
        if user_id not in thread['participantIds']:
            raise ValueError('Access denied')
        return {
            'id': thread['id'],
            'participantIds': thread['participantIds'],
            'messages': self.messages.get(thread['id'], []),
            'updatedAt': thread['updated_at'],
        }

    def send_message(self, thread_id: str, sender_id: str, content: str) -> dict:
        thread = self.threads.get(thread_id)
        if thread is None:
            raise ValueError('Thread not found')
        if sender_id not in thread['participantIds']:
            raise ValueError('Access denied')
        message = self._create_message(thread_id, sender_id, content)
        self.messages.setdefault(thread_id, []).append(message)
        thread['updated_at'] = self._now_iso()
        return message
