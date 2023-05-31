from __future__ import annotations

__all__ = ["FreeAuthSecurity", "PermNeed"]


class PermNeed(object):
    def __init__(self, code: str):
        self.code = code

    def __str__(self) -> str:
        return self.code

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.code})"

    def __eq__(self, perm_need: object) -> bool:
        if isinstance(perm_need, PermNeed):
            return self.code == perm_need.code
        return False


class FreeAuthSecurity(object):
    def __init__(self):
        self.permissions = []

    def add_perm(self, *perms: str | PermNeed) -> None:
        for perm in perms:
            if isinstance(perm, str):
                perm = PermNeed(perm)
            if perm not in self.permissions:
                self.permissions.append(perm)
