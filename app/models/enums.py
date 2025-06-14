from enum import Enum


class RoleEnum(int, Enum):
    SUPERADMIN = 0
    ADMIN = 1
    BARBER = 2
    CLIENT = 3
