import os

from data_management.repositories import repository


def is_admin(account_id: str) -> bool:
    configured = {
        value.strip()
        for value in os.getenv('ADMIN_USER_IDS', '').split(',')
        if value.strip()
    }
    return account_id in configured


def require_admin(account_id: str) -> None:
    if not is_admin(account_id):
        raise PermissionError('admin access required')


def list_queue(status: str = 'open', limit: int = 100) -> list[dict]:
    return repository.list_moderation_reports(status=status, limit=limit)


def update_report(report_id: str, status: str, moderator_id: str, notes: str | None = None) -> dict:
    return repository.update_moderation_report(report_id, status, moderator_id, notes)
