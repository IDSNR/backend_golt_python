from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, MetaData, String, Table, Text, UniqueConstraint

metadata = MetaData()

accounts = Table(
    'platform_accounts', metadata,
    Column('id', String(100), primary_key=True),
    Column('email', String(255), unique=True),
    Column('display_name', String(150), nullable=False),
    Column('auth_provider', String(50), nullable=False),
    Column('password_hash', Text),
    Column('is_active', Boolean, nullable=False, default=True),
    Column('created_at', DateTime, nullable=False),
)

profiles = Table(
    'platform_profiles', metadata,
    Column('account_id', String(100), ForeignKey('platform_accounts.id', ondelete='CASCADE'), primary_key=True),
    Column('handle', String(50), nullable=False, unique=True, index=True),
    Column('account_type', String(30), nullable=False),
    Column('display_name', String(150), nullable=False),
    Column('bio', Text),
    Column('avatar_url', String(500)),
    Column('banner_url', String(500)),
    Column('website_url', String(500)),
    Column('location', String(200)),
    Column('pronouns', String(50)),
    Column('is_private', Boolean, nullable=False, default=False),
    Column('created_at', DateTime, nullable=False),
    Column('updated_at', DateTime, nullable=False),
)

posts = Table(
    'platform_posts', metadata,
    Column('id', String(100), primary_key=True),
    Column('account_id', String(100), ForeignKey('platform_accounts.id', ondelete='CASCADE'), nullable=False, index=True),
    Column('caption', Text),
    Column('video_url', String(1000)),
    Column('media_items_json', Text),
    Column('visibility', String(30), nullable=False, default='public'),
    Column('views', Integer, nullable=False, default=0),
    Column('completions', Integer, nullable=False, default=0),
    Column('created_at', DateTime, nullable=False, index=True),
)

follows = Table(
    'platform_follows', metadata,
    Column('id', Integer, primary_key=True),
    Column('follower_id', String(100), ForeignKey('platform_accounts.id', ondelete='CASCADE'), nullable=False),
    Column('followee_id', String(100), ForeignKey('platform_accounts.id', ondelete='CASCADE'), nullable=False),
    Column('status', String(20), nullable=False),
    Column('created_at', DateTime, nullable=False),
    UniqueConstraint('follower_id', 'followee_id', name='uq_platform_follow'),
)

engagements = Table(
    'platform_engagements', metadata,
    Column('id', Integer, primary_key=True),
    Column('account_id', String(100), ForeignKey('platform_accounts.id', ondelete='CASCADE'), nullable=False),
    Column('post_id', String(100), ForeignKey('platform_posts.id', ondelete='CASCADE'), nullable=False),
    Column('kind', String(20), nullable=False),
    Column('created_at', DateTime, nullable=False),
    UniqueConstraint('account_id', 'post_id', 'kind', name='uq_platform_engagement'),
)

comments = Table(
    'platform_comments', metadata,
    Column('id', Integer, primary_key=True),
    Column('account_id', String(100), ForeignKey('platform_accounts.id', ondelete='CASCADE'), nullable=False),
    Column('post_id', String(100), ForeignKey('platform_posts.id', ondelete='CASCADE'), nullable=False, index=True),
    Column('parent_id', Integer, ForeignKey('platform_comments.id', ondelete='SET NULL')),
    Column('body', Text, nullable=False),
    Column('created_at', DateTime, nullable=False),
)

moderation_reports = Table(
    'platform_moderation_reports', metadata,
    Column('id', String(100), primary_key=True),
    Column('reporter_id', String(100), ForeignKey('platform_accounts.id', ondelete='CASCADE'), nullable=False),
    Column('target_type', String(30), nullable=False),
    Column('target_id', String(100), nullable=False),
    Column('reason', Text, nullable=False),
    Column('status', String(20), nullable=False, default='open', index=True),
    Column('moderator_id', String(100), ForeignKey('platform_accounts.id', ondelete='SET NULL')),
    Column('notes', Text),
    Column('created_at', DateTime, nullable=False),
    Column('updated_at', DateTime, nullable=False),
)
