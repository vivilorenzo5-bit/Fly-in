from enum import Enum
from typing import Optional


class ZoneType(str, Enum):
    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"

    @property
    def cost(self) -> int:
        if self == ZoneType.RESTRICTED:
            return 2
        return 1


class Zone:
    def __init__(
            self,
            name: str,
            x: int,
            y: int,
            zone_type: ZoneType = ZoneType.NORMAL,
            max_drones: Optional[int] = 1,
            color: Optional[str] = None,
            is_start: bool = False,
            is_end: bool = False
    ) -> None:
        self.name: str = name
        self.x: int = x
        self.y: int = y
        self.zone_type: ZoneType = zone_type
        self.color: Optional[str] = color
        self.is_start: bool = is_start
        self.is_end: bool = is_end

        if self.is_start or self.is_end:
            self.max_drones: Optional[int] = None
        else:
            self.max_drones = max_drones

        self.current_drones: int = 0

    @property
    def is_accessible(self) -> bool:
        return self.zone_type != ZoneType.BLOCKED

    @property
    def has_capacity(self) -> bool:
        if self.max_drones is None:
            return True
        return self.current_drones < self.max_drones

    def occupy(self) -> None:
        self.current_drones += 1

    def release(self) -> None:
        if self.current_drones > 0:
            self.current_drones -= 1

    def capacity_info(self) -> str:
        max_str = "∞" if self.max_drones is None else str(self.max_drones)
        return f"Zone {self.name}: {self.current_drones}/{max_str} drones"

    def __repr__(self) -> str:
        return (f"Zone(name='{self.name}', type={self.zone_type.value}, "
                f"max={self.max_drones})")
