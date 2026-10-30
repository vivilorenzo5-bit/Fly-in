from src.core.zone import Zone


class Connection:
    def __init__(
            self, zone_a: Zone, zone_b: Zone, max_capacity: int = 1
            ) -> None:
        self.zone_a: Zone = zone_a
        self.zone_b: Zone = zone_b
        self.max_capacity: int = max_capacity
        self.current_transit: int = 0

    @property
    def canonical_id(self) -> str:
        names = sorted([self.zone_a.name, self.zone_b.name])
        return f"{names[0]}-{names[1]}"

    @property
    def display_name(self) -> str:
        return f"{self.zone_a.name}-{self.zone_b.name}"

    @property
    def has_capacity(self) -> bool:
        return self.current_transit < self.max_capacity

    def connects(self, name_a: str, name_b: str) -> bool:
        return {self.zone_a.name, self.zone_b.name} == {name_a, name_b}

    def get_opposite(self, zone: Zone) -> Zone:
        if zone == self.zone_a:
            return self.zone_b
        if zone == self.zone_b:
            return self.zone_a
        raise ValueError(
            f"A zona '{zone.name}' nao pertence "
            f"a esta ligacao ({self.canonical_id})."
            )

    def occupy(self) -> None:
        self.current_transit += 1

    def release(self) -> None:
        if self.current_transit > 0:
            self.current_transit -= 1

    def capacity_info(self) -> str:
        return (
                f"Connection {self.display_name}: "
                f"{self.current_transit}/{self.max_capacity} capacity used"
        )

    def __repr__(self) -> str:
        return (
            f"Connection({self.zone_a.name} <-> {self.zone_b.name}, "
            f"capacity={self.current_transit}/{self.max_capacity})"
        )
