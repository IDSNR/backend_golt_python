from fastapi.testclient import TestClient

from app.main import app
from conftest import auth_headers

client = TestClient(app)


def test_group_owner_can_create_and_member_can_join() -> None:
    create = client.post(
        '/groups',
        headers=auth_headers('group-owner'),
        json={'name': 'Design Circle', 'description': 'Shared ideas'},
    )
    assert create.status_code == 201
    group_id = create.json()['group']['id']

    join = client.post(f'/groups/{group_id}/join', headers=auth_headers('group-member'))
    assert join.status_code == 200
    assert join.json()['status'] == 'member'

    detail = client.get(f'/groups/{group_id}')
    assert detail.status_code == 200
    assert {member['accountId'] for member in detail.json()['members']} == {'group-owner', 'group-member'}


def test_private_group_requires_owner_approval() -> None:
    create = client.post(
        '/groups',
        headers=auth_headers('private-owner'),
        json={'name': 'Private Circle', 'isPrivate': True},
    )
    group_id = create.json()['group']['id']

    join = client.post(f'/groups/{group_id}/join', headers=auth_headers('pending-member'))
    assert join.json()['status'] == 'pending'

    denied = client.post(f'/groups/{group_id}/members/pending-member/approve', headers=auth_headers('not-owner'))
    assert denied.status_code == 403

    approved = client.post(f'/groups/{group_id}/members/pending-member/approve', headers=auth_headers('private-owner'))
    assert approved.status_code == 200
    assert approved.json()['status'] == 'member'