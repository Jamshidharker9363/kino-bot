from app.config import get_admin_ids, get_bot_owner_id
from app.data.admin_repository import AdminRepository


class AdminService:
    def __init__(self, repository: AdminRepository):
        self.repository = repository
        self.owner_id = get_bot_owner_id()
        self.bootstrap_admins = get_admin_ids()
        for admin_id in self.bootstrap_admins:
            if self.owner_id and int(admin_id) == int(self.owner_id):
                continue
            self.repository.add(admin_id)

    def is_admin(self, user_id: int | None) -> bool:
        if not user_id:
            return False
        return int(user_id) == int(self.owner_id) or int(user_id) in self.repository.all_ids()

    def is_super_admin(self, user_id: int | None) -> bool:
        return bool(user_id) and self.owner_id is not None and int(user_id) == int(self.owner_id)

    def all_admin_ids(self) -> set[int]:
        return self.repository.all_ids()

    def manageable_admin_ids(self) -> list[int]:
        admin_ids = sorted(self.repository.all_ids())
        if self.owner_id is None:
            return admin_ids
        return [admin_id for admin_id in admin_ids if int(admin_id) != int(self.owner_id)]

    def add_admin(self, user_id: int, added_by: int | None = None) -> None:
        if self.owner_id and int(user_id) == int(self.owner_id):
            return
        self.repository.add(user_id, added_by)

    def remove_admin(self, user_id: int) -> bool:
        if self.owner_id and int(user_id) == int(self.owner_id):
            return False
        return self.repository.remove(user_id)
