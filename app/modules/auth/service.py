import random
import string
from datetime import datetime


class ProfileService:
    def __init__(self) -> None:
        self.profiles: dict[str, dict] = {}
        self.profiles_by_handle: dict[str, str] = {}
        self.link_tokens: dict[str, str] = {}

    def _normalize_handle(self, handle: str) -> str:
        return handle.strip().lower()

    def _generate_referral_code(self) -> str:
        return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(8))

    def _now_iso(self) -> str:
        return datetime.utcnow().isoformat() + 'Z'

    def create_profile(self, profile_id: str, payload: dict) -> dict:
        if payload.get('accountType') not in {'standard', 'creator'}:
            raise ValueError("accountType must be 'standard' or 'creator'")

        handle = self._normalize_handle(payload.get('handle', ''))
        if not handle:
            raise ValueError('handle is required')
        if handle in self.profiles_by_handle:
            raise ValueError('handle is already taken')

        profile = {
            'id': profile_id,
            'identityId': payload.get('identityLinkToken') or f'identity-{profile_id}',
            'accountType': payload.get('accountType'),
            'handle': handle,
            'displayName': payload.get('displayName'),
            'bio': payload.get('bio'),
            'avatarUrl': payload.get('avatarUrl'),
            'isVerifiedMinor': False,
            'isPrivate': payload.get('isPrivate', False),
            'creatorModeEnabled': payload.get('accountType') == 'creator',
            'referralCode': self._generate_referral_code(),
            'createdAt': self._now_iso(),
        }
        self.profiles[profile_id] = profile
        self.profiles_by_handle[handle] = profile_id
        return profile

    def get_profile(self, profile_id: str) -> dict | None:
        return self.profiles.get(profile_id)

    def get_profile_by_handle(self, handle: str) -> dict | None:
        profile_id = self.profiles_by_handle.get(self._normalize_handle(handle))
        return self.get_profile(profile_id) if profile_id else None

    def ensure_profile(self, profile_id: str) -> dict:
        profile = self.get_profile(profile_id)
        if profile is not None:
            return profile

        handle = self._normalize_handle(profile_id)
        if not handle:
            handle = f'user-{len(self.profiles) + 1}'
        elif handle in self.profiles_by_handle:
            handle = f'{handle}-{len(self.profiles) + 1}'

        profile = {
            'id': profile_id,
            'identityId': f'identity-{profile_id}',
            'accountType': 'standard',
            'handle': handle,
            'displayName': profile_id,
            'bio': None,
            'avatarUrl': None,
            'isVerifiedMinor': False,
            'isPrivate': True,
            'creatorModeEnabled': False,
            'referralCode': self._generate_referral_code(),
            'createdAt': self._now_iso(),
        }
        self.profiles[profile_id] = profile
        self.profiles_by_handle[handle] = profile_id
        return profile

    def create_link_token(self, profile_id: str) -> dict:
        token = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(24))
        self.link_tokens[token] = profile_id
        return {
            'token': token,
            'expiresAt': self._now_iso(),
        }

    def redeem_link_token(self, token: str, profile_id: str, payload: dict) -> dict:
        owner_id = self.link_tokens.get(token)
        if owner_id is None:
            raise ValueError('Invalid or expired link token')

        if payload.get('identityLinkToken') != token:
            raise ValueError('Invalid identityLinkToken')

        profile = self.create_profile(profile_id, payload)
        return profile
