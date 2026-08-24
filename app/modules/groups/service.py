from datetime import datetime, timezone


class GroupService:
    def __init__(self) -> None:
        self.groups: dict[str, dict] = {}
        self.members: dict[str, dict[str, str]] = {}
        self.next_id = 1

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')

    def create_group(self, owner_id: str, name: str, description: str | None, is_private: bool) -> dict:
        cleaned_name = name.strip()
        if not cleaned_name:
            raise ValueError('name is required')
        group_id = f'group-{self.next_id}'
        self.next_id += 1
        group = {
            'id': group_id,
            'ownerId': owner_id,
            'name': cleaned_name,
            'description': description.strip() if description else None,
            'isPrivate': is_private,
            'created_at': self._now_iso(),
        }
        self.groups[group_id] = group
        self.members[group_id] = {owner_id: 'owner'}
        return group

    def list_groups(self) -> list[dict]:
        return list(reversed(list(self.groups.values())))

    def get_group(self, group_id: str) -> dict | None:
        return self.groups.get(group_id)

    def join_group(self, group_id: str, account_id: str) -> str:
        group = self.get_group(group_id)
        if group is None:
            raise ValueError('Group not found')
        if account_id in self.members[group_id]:
            return self.members[group_id][account_id]
        role = 'pending' if group['isPrivate'] else 'member'
        self.members[group_id][account_id] = role
        return role

    def leave_group(self, group_id: str, account_id: str) -> None:
        group = self.get_group(group_id)
        if group is None:
            raise ValueError('Group not found')
        if group['ownerId'] == account_id:
            raise ValueError('Group owner cannot leave the group')
        self.members[group_id].pop(account_id, None)

    def list_members(self, group_id: str) -> list[dict]:
        if self.get_group(group_id) is None:
            raise ValueError('Group not found')
        return [{'accountId': account_id, 'role': role} for account_id, role in self.members[group_id].items()]

    def approve_member(self, group_id: str, account_id: str, acting_owner_id: str) -> str:
        group = self.get_group(group_id)
        if group is None:
            raise ValueError('Group not found')
        if group['ownerId'] != acting_owner_id:
            raise ValueError('Only the group owner can approve members')
        if self.members[group_id].get(account_id) != 'pending':
            raise ValueError('Membership request not found')
        self.members[group_id][account_id] = 'member'
        return 'member'
