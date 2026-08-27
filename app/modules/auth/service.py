import hashlib
import os
import random
import secrets
import string
from datetime import datetime, timedelta, timezone


class AuthService:
    def __init__(self) -> None:
        self.users: dict[str, dict] = {}
        self.google_users: dict[str, dict] = {}
        self.sessions: dict[str, dict] = {}
        self.session_ttl = timedelta(days=7)
        self.persistence = os.getenv('PERSISTENCE_ENABLED', 'false').lower() == 'true'

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    def _hash_password(self, password: str) -> str:
        salt = os.getenv("AUTH_PASSWORD_SALT", "dev-salt").encode("utf-8")
        return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200_000).hex()

    def _issue_session(self, user_id: str) -> str:
        now = datetime.now(timezone.utc)
        for token, session in self.sessions.items():
            if session['userId'] == user_id and session['expiresAt'] > now:
                return token
        token = secrets.token_urlsafe(32)
        self.sessions[token] = {
            'userId': user_id,
            'expiresAt': now + self.session_ttl,
        }
        return token

    def validate_session(self, token: str) -> str | None:
        session = self.sessions.get(token)
        if session is None:
            return None
        if session['expiresAt'] <= datetime.now(timezone.utc):
            self.sessions.pop(token, None)
            return None
        return session['userId']

    def revoke_session(self, token: str) -> None:
        self.sessions.pop(token, None)

    def register_user(self, email: str, password: str, display_name: str, skip_validation: bool = False) -> dict:
        normalized = email.strip().lower()
        if not normalized:
            raise ValueError("email is required")
        if not skip_validation and normalized in self.users:
            raise ValueError("email already exists")
        if self.persistence and not skip_validation:
            from data_management.repositories import repository
            if repository.get_account_by_email(normalized):
                raise ValueError("email already exists")
        if not password or len(password) < 8:
            raise ValueError("password must be at least 8 characters")

        user = {
            "id": f"user-{secrets.token_hex(8)}" if self.persistence else f"user-{len(self.users) + 1}",
            "email": normalized,
            "displayName": display_name or "New user",
            "passwordHash": self._hash_password(password),
            "createdAt": self._now_iso(),
            "authProvider": "email",
        }
        self.users[normalized] = user
        if self.persistence:
            from data_management.repositories import repository
            repository.create_account(user['id'], normalized, user['displayName'], user['passwordHash'], 'email')
        return {"token": self._issue_session(user['id']), "user": user}

    def authenticate_user(self, email: str, password: str) -> dict:
        normalized = email.strip().lower()
        user = self.users.get(normalized)
        if user is None and self.persistence:
            from data_management.repositories import repository
            stored = repository.get_account_by_email(normalized)
            if stored:
                user = dict(stored)
                user['passwordHash'] = user.pop('password_hash')
                user['displayName'] = user.pop('display_name')
                user['authProvider'] = user.pop('auth_provider')
                self.users[normalized] = user
        if user is None or user["passwordHash"] != self._hash_password(password):
            raise ValueError("invalid credentials")
        return {"token": self._issue_session(user['id']), "user": user}

    def handle_google_auth(self, email: str, display_name: str, google_id: str) -> dict:
        normalized = email.strip().lower()
        existing = self.google_users.get(google_id)
        if existing is not None:
            return {"token": self._issue_session(existing['id']), "user": existing}

        user = {
            "id": f"google-{len(self.google_users) + 1}",
            "email": normalized,
            "displayName": display_name or "Google user",
            "passwordHash": None,
            "createdAt": self._now_iso(),
            "authProvider": "google",
        }
        self.google_users[google_id] = user
        return {"token": self._issue_session(user['id']), "user": user}

    def authenticate_google_token(self, id_token: str) -> dict:
        from google.auth.transport import requests
        from google.oauth2 import id_token as google_id_token

        client_id = os.getenv('GOOGLE_CLIENT_ID')
        if not client_id:
            raise ValueError('Google OAuth is not configured')
        try:
            claims = google_id_token.verify_oauth2_token(id_token, requests.Request(), audience=client_id)
        except Exception as exc:
            raise ValueError('invalid Google ID token') from exc
        if claims.get('iss') not in {'accounts.google.com', 'https://accounts.google.com'}:
            raise ValueError('invalid Google token issuer')
        if not claims.get('email') or not claims.get('email_verified') or not claims.get('sub'):
            raise ValueError('Google account email is not verified')

        email = claims['email'].strip().lower()
        google_id = claims['sub']
        display_name = claims.get('name') or email.split('@')[0]
        existing = self.google_users.get(google_id)
        if existing is None and self.persistence:
            from data_management.repositories import repository
            stored = repository.get_account_by_email(email)
            if stored:
                existing = {
                    'id': stored['id'], 'email': stored['email'], 'displayName': stored['display_name'],
                    'passwordHash': stored['password_hash'], 'createdAt': self._now_iso(), 'authProvider': stored['auth_provider'],
                }
        if existing is not None:
            self.google_users[google_id] = existing
            return {"token": self._issue_session(existing['id']), "user": existing}

        user = {
            'id': f"google-{secrets.token_hex(8)}" if self.persistence else f"google-{len(self.google_users) + 1}",
            'email': email, 'displayName': display_name, 'passwordHash': None,
            'createdAt': self._now_iso(), 'authProvider': 'google',
        }
        self.google_users[google_id] = user
        if self.persistence:
            from data_management.repositories import repository
            repository.create_account(user['id'], email, display_name, None, 'google')
        return {"token": self._issue_session(user['id']), "user": user}


auth_service = AuthService()


class ProfileService:
    def __init__(self) -> None:
        self.profiles: dict[str, dict] = {}
        self.profiles_by_handle: dict[str, str] = {}
        self.link_tokens: dict[str, str] = {}
        self.persistence = os.getenv('PERSISTENCE_ENABLED', 'false').lower() == 'true'

        self.create_profile('user-1', {
            'accountType': 'standard',
            'handle': 'demo_user',
            'displayName': 'Demo User',
            'bio': 'A test account for the PartnerHub feed.',
            'avatarUrl': 'https://partnerhub.test/media/avatar-demo.png',
            'isPrivate': False,
        })
        self.create_profile('user-2', {
            'accountType': 'creator',
            'handle': 'creator_space',
            'displayName': 'Creator Space',
            'bio': 'Creators post short media stories and clips here.',
            'avatarUrl': 'https://partnerhub.test/media/avatar-creator.png',
            'isPrivate': False,
        })

    def _normalize_handle(self, handle: str) -> str:
        return handle.strip().lower()

    def _generate_referral_code(self) -> str:
        return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(8))

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')

    def create_profile(self, profile_id: str, payload: dict) -> dict:
        if payload.get('accountType') not in {'standard', 'creator'}:
            raise ValueError("accountType must be 'standard' or 'creator'")

        handle = self._normalize_handle(payload.get('handle', ''))
        if not handle:
            raise ValueError('handle is required')
        # Check DB for existing account username to avoid duplicates when Postgres is used
        try:
            from backend.data_management.services import get_account_by_username
        except Exception:
            get_account_by_username = None

        if get_account_by_username is not None:
            try:
                existing_account = get_account_by_username(handle)
            except Exception:
                existing_account = None
            if existing_account is not None:
                raise ValueError('handle is already taken')

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
            'bannerUrl': payload.get('bannerUrl'),
            'websiteUrl': payload.get('websiteUrl'),
            'location': payload.get('location'),
            'pronouns': payload.get('pronouns'),
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
        if self.persistence:
            from data_management.repositories import repository
            return repository.get_profile(profile_id)
        return self.profiles.get(profile_id)

    def get_profile_by_handle(self, handle: str) -> dict | None:
        if self.persistence:
            from data_management.repositories import repository
            return repository.get_profile_by_handle(handle)
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
            'bannerUrl': None,
            'websiteUrl': None,
            'location': None,
            'pronouns': None,
            'isVerifiedMinor': False,
            'isPrivate': True,
            'creatorModeEnabled': False,
            'referralCode': self._generate_referral_code(),
            'createdAt': self._now_iso(),
        }
        self.profiles[profile_id] = profile
        self.profiles_by_handle[handle] = profile_id
        if self.persistence:
            from data_management.repositories import repository
            profile = repository.upsert_profile(profile)
        return profile

    def update_profile(self, profile_id: str, payload: dict) -> dict:
        profile = self.get_profile(profile_id)
        if profile is None:
            raise ValueError('Profile not found')

        if 'handle' in payload:
            new_handle = self._normalize_handle(payload.get('handle', ''))
            if not new_handle:
                raise ValueError('handle is required')
            # Check DB for existing account username to avoid duplicates when Postgres is used
            try:
                from backend.data_management.services import get_account_by_username
            except Exception:
                get_account_by_username = None

            if new_handle != profile['handle']:
                if get_account_by_username is not None:
                    try:
                        existing_account = get_account_by_username(new_handle)
                    except Exception:
                        existing_account = None
                    if existing_account is not None:
                        raise ValueError('handle is already taken')
                if new_handle in self.profiles_by_handle:
                    raise ValueError('handle is already taken')
                del self.profiles_by_handle[profile['handle']]
                profile['handle'] = new_handle
                self.profiles_by_handle[new_handle] = profile_id

        if 'displayName' in payload:
            profile['displayName'] = payload.get('displayName')
        if 'bio' in payload:
            profile['bio'] = payload.get('bio')
        if 'avatarUrl' in payload:
            profile['avatarUrl'] = payload.get('avatarUrl')
        if 'bannerUrl' in payload:
            profile['bannerUrl'] = payload.get('bannerUrl')
        if 'websiteUrl' in payload:
            profile['websiteUrl'] = payload.get('websiteUrl')
        if 'location' in payload:
            profile['location'] = payload.get('location')
        if 'pronouns' in payload:
            profile['pronouns'] = payload.get('pronouns')
        if 'isPrivate' in payload:
            profile['isPrivate'] = bool(payload.get('isPrivate'))

        profile['updatedAt'] = self._now_iso()
        if self.persistence:
            from data_management.repositories import repository
            profile = repository.upsert_profile(profile)
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
