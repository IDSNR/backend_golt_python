from fastapi.testclient import TestClient

from app.main import app
from conftest import auth_headers

client = TestClient(app)


def test_engagement_requires_authenticated_actor() -> None:
    response = client.post('/content/content-1/like')

    assert response.status_code == 401


def test_like_bookmark_comment_and_share_flow() -> None:
    headers = auth_headers('engagement-user')

    like = client.post('/content/content-1/like', headers=headers)
    assert like.status_code == 200
    assert like.json()['engagement']['likedByViewer'] is True
    assert like.json()['engagement']['likes'] == 1

    bookmark = client.post('/content/content-1/bookmark', headers=headers)
    assert bookmark.status_code == 200
    assert bookmark.json()['engagement']['bookmarkedByViewer'] is True

    comment = client.post(
        '/content/content-1/comments',
        headers=headers,
        json={'body': 'Useful post'},
    )
    assert comment.status_code == 201
    assert comment.json()['comment']['accountId'] == 'engagement-user'

    share = client.post('/content/content-1/share', headers=headers)
    assert share.status_code == 201
    assert share.json()['share']['contentId'] == 'content-1'

    summary = client.get('/content/content-1/engagement', headers=headers)
    assert summary.status_code == 200
    assert summary.json()['engagement']['comments'] == 1
    assert summary.json()['engagement']['shares'] == 1


def test_engagement_actions_reject_unknown_content() -> None:
    response = client.post('/content/does-not-exist/like', headers=auth_headers('user-1'))

    assert response.status_code == 404
    assert response.json()['detail'] == 'Content not found'
