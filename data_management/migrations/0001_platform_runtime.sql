CREATE TABLE IF NOT EXISTS platform_accounts (
    id VARCHAR(100) PRIMARY KEY,
    email VARCHAR(255) UNIQUE,
    display_name VARCHAR(150) NOT NULL,
    auth_provider VARCHAR(50) NOT NULL,
    password_hash TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS platform_profiles (
    account_id VARCHAR(100) PRIMARY KEY REFERENCES platform_accounts(id) ON DELETE CASCADE,
    handle VARCHAR(50) NOT NULL UNIQUE,
    account_type VARCHAR(30) NOT NULL,
    display_name VARCHAR(150) NOT NULL,
    bio TEXT,
    avatar_url VARCHAR(500),
    banner_url VARCHAR(500),
    website_url VARCHAR(500),
    location VARCHAR(200),
    pronouns VARCHAR(50),
    is_private BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_platform_profiles_handle ON platform_profiles(handle);

CREATE TABLE IF NOT EXISTS platform_posts (
    id VARCHAR(100) PRIMARY KEY,
    account_id VARCHAR(100) NOT NULL REFERENCES platform_accounts(id) ON DELETE CASCADE,
    caption TEXT,
    video_url VARCHAR(1000),
    media_items_json TEXT,
    visibility VARCHAR(30) NOT NULL DEFAULT 'public',
    views INTEGER NOT NULL DEFAULT 0,
    completions INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_platform_posts_account_id ON platform_posts(account_id);
CREATE INDEX IF NOT EXISTS ix_platform_posts_created_at ON platform_posts(created_at);

CREATE TABLE IF NOT EXISTS platform_follows (
    id SERIAL PRIMARY KEY,
    follower_id VARCHAR(100) NOT NULL REFERENCES platform_accounts(id) ON DELETE CASCADE,
    followee_id VARCHAR(100) NOT NULL REFERENCES platform_accounts(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL,
    created_at TIMESTAMP NOT NULL,
    CONSTRAINT uq_platform_follow UNIQUE (follower_id, followee_id)
);

CREATE TABLE IF NOT EXISTS platform_engagements (
    id SERIAL PRIMARY KEY,
    account_id VARCHAR(100) NOT NULL REFERENCES platform_accounts(id) ON DELETE CASCADE,
    post_id VARCHAR(100) NOT NULL REFERENCES platform_posts(id) ON DELETE CASCADE,
    kind VARCHAR(20) NOT NULL,
    created_at TIMESTAMP NOT NULL,
    CONSTRAINT uq_platform_engagement UNIQUE (account_id, post_id, kind)
);

CREATE TABLE IF NOT EXISTS platform_comments (
    id SERIAL PRIMARY KEY,
    account_id VARCHAR(100) NOT NULL REFERENCES platform_accounts(id) ON DELETE CASCADE,
    post_id VARCHAR(100) NOT NULL REFERENCES platform_posts(id) ON DELETE CASCADE,
    parent_id INTEGER REFERENCES platform_comments(id) ON DELETE SET NULL,
    body TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_platform_comments_post_id ON platform_comments(post_id);

CREATE TABLE IF NOT EXISTS platform_moderation_reports (
    id VARCHAR(100) PRIMARY KEY,
    reporter_id VARCHAR(100) NOT NULL REFERENCES platform_accounts(id) ON DELETE CASCADE,
    target_type VARCHAR(30) NOT NULL,
    target_id VARCHAR(100) NOT NULL,
    reason TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'open',
    moderator_id VARCHAR(100) REFERENCES platform_accounts(id) ON DELETE SET NULL,
    notes TEXT,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_platform_moderation_reports_status ON platform_moderation_reports(status);