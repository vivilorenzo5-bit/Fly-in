from enum import Enum
from typing import Optional
from src.core.zone import Zone
from src.core.connection import Connection


class DroneState(str, Enum):
    AT_REST = "at_rest"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"


class Drone:
    def __init__(self, drone_id: int, start_zone: Zone) -> None:
        if drone_id <= 0:
            raise ValueError(
                "O identificador do drone deve ser um inteiro positivo."
            )

        self.id: int = drone_id
        self.current_zone: Optional[Zone] = start_zone
        self.transit_connection: Optional[Connection] = None
        self.target_zone: Optional[Zone] = None
        self.turns_remaining: int = 0
        self.state: DroneState = DroneState.AT_REST

        start_zone.occupy()

    @property
    def tag(self) -> str:
        return f"D{self.id}"

    @property
    def is_delivered(self) -> bool:
        return self.state == DroneState.DELIVERED

    @property
    def is_in_flight(self) -> bool:
        return self.state == DroneState.IN_TRANSIT

    def start_move(self, destination: Zone, connection: Connection) -> str:
        if self.current_zone is None:
            raise RuntimeError(
                f"{self.tag} nao esta posicionado numa zona "
                "para iniciar movimento"
            )
        cost = destination.cost
        self.current_zone.release()
        self.current_zone = None

        if cost == 1:
            destination.occupy()
            self.current_zone = destination
            if destination.is_end:
                self.state = DroneState.DELIVERED
            else:
                self.state = DroneState.AT_REST
            return f"{self.tag}-{destination.name}"

        self.transit_connection = connection
        self.target_zone = destination
        self.transit_connection.occupy()
        self.turns_remaining = cost - 1
        self.state = DroneState.IN_TRANSIT
        return f"{self.tag}-{connection.display_name}"

    def advance_transit(self) -> Optional[str]:
        if self.state != DroneState.IN_TRANSIT:
            return None

        self.turns_remaining -= 1
        if self.turns_remaining == 0:
            if self.transit_connection is None or self.target_zone is None:
                raise RuntimeError(
                    f"Estado de transito corrompido para o drone {self.tag}"
                )

            self.transit_connection.release()
            self.transit_connection = None
            dest = self.target_zone
            dest.occupy()
            self.current_zone = dest
            self.target_zone = None

            if dest.is_end:
                self.state = DroneState.DELIVERED
            else:
                self.state = DroneState.AT_REST

            return f"{self.tag}-{dest.name}"
        return None

    def __repr__(self) -> str:
        loc = self.current_zone.name if self.current_zone else "em transito"
        return f"Drone({self.tag}, state={self.state.value}, location='{loc}')"
