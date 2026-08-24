from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_group_owner_can_create_and_member_can_join() -> None:
    create = client.post(
        '/groups',
        headers={'X-User-Id': 'group-owner'},
        json={'name': 'Design Circle', 'description': 'Shared ideas'},
    )
    assert create.status_code == 201
    group_id = create.json()['group']['id']

    join = client.post(f'/groups/{group_id}/join', headers={'X-User-Id': 'group-member'})
    assert join.status_code == 200
    assert join.json()['status'] == 'member'

    detail = client.get(f'/groups/{group_id}')
    assert detail.status_code == 200
    assert {member['accountId'] for member in detail.json()['members']} == {'group-owner', 'group-member'}


def test_private_group_requires_owner_approval() -> None:
    create = client.post(
        '/groups',
        headers={'X-User-Id': 'private-owner'},
        json={'name': 'Private Circle', 'isPrivate': True},
    )
    group_id = create.json()['group']['id']

    join = client.post(f'/groups/{group_id}/join', headers={'X-User-Id': 'pending-member'})
    assert join.json()['status'] == 'pending'

    denied = client.post(f'/groups/{group_id}/members/pending-member/approve', headers={'X-User-Id': 'not-owner'})
    assert denied.status_code == 403

    approved = client.post(f'/groups/{group_id}/members/pending-member/approve', headers={'X-User-Id': 'private-owner'})
    assert approved.status_code == 200
    assert approved.json()['status'] == 'member'