import os
import uuid

import pytest

from data_management.database import init_db
from data_management.repositories import repository


pytestmark = pytest.mark.skipif(
    os.getenv('RUN_POSTGRES_TESTS', '').lower() != 'true',
    reason='set RUN_POSTGRES_TESTS=true to run PostgreSQL end-to-end tests',
)


def test_postgres_persists_core_social_and_moderation_workflows() -> None:
    init_db()
    suffix = uuid.uuid4().hex
    account_id = f'e2e-account-{suffix}'
    other_id = f'e2e-other-{suffix}'
    post_id = f'e2e-post-{suffix}'
    report_id = f'e2e-report-{suffix}'

    repository.create_account(account_id, f'{suffix}@example.com', 'E2E Account', None, 'test')
    repository.create_account(other_id, f'{suffix}-other@example.com', 'E2E Other', None, 'test')
    repository.create_post({'id': post_id, 'creatorId': other_id, 'caption': 'database test', 'visibility': 'public'})
    repository.follow(account_id, other_id, 'approved')
    repository.engagement_toggle(account_id, post_id, 'like', True)
    report = repository.create_moderation_report({
        'id': report_id, 'reporterId': account_id, 'targetType': 'post',
        'targetId': post_id, 'reason': 'database test',
    })

    assert repository.get_account(account_id)['id'] == account_id
    assert repository.get_post(post_id)['id'] == post_id
    assert repository.relationship_status(account_id, other_id) == 'following'
    assert repository.engagement_summary(account_id, post_id)['likedByViewer'] is True
    assert report['status'] == 'open'
    assert repository.list_moderation_reports('open', 10)[-1]['id'] == report_id

    updated = repository.update_moderation_report(report_id, 'resolved', account_id, 'reviewed')
    assert updated['status'] == 'resolved'
    assert updated['moderatorId'] == account_id
