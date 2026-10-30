from collections import deque
from typing import Optional
from src.core.zone import Zone
from src.core.connection import Connection
from src.core.exceptions import MapValidationError


class DroneNetwork:
    def __init__(self, nb_drones: int) -> None:
        self.nb_drones: int = nb_drones
        self.zones: dict[str, Zone] = {}
        self.connections: list[Connection] = []
        self.start_hub: Optional[Zone] = None
        self.end_hub: Optional[Zone] = None
        self._adjacency: dict[str, list[tuple[Zone, Connection]]] = {}
        self._connection_ids: set[str] = set()

    def add_zone(self, zone: Zone) -> None:
        if zone.name in self.zones:
            raise MapValidationError(f"Zona duplicada: '{zone.name}'")

        if zone.is_start:
            if self.start_hub is not None:
                raise MapValidationError(
                    "Definicao duplicada de 'start_hub'. Apenas um ponto "
                    "de partida e permitido."
                )

        if zone.is_end:
            if self.end_hub is not None:
                raise MapValidationError(
                    "Definicao duplicada de 'end_hub'. Apenas um ponto "
                    "de chegada e permitido."
                )
            self.start_hub = zone

        self.zones[zone.name] = zone
        self._adjacency[zone.name] = []

    def add_connection(
            self, zone_name_a: str, zone_name_b: str, max_capacity: int = 1
    ) -> None:
        if zone_name_a == zone_name_b:
            raise MapValidationError(
                f"Auto conexao invalida na zona '{zone_name_a}'."
            )

        if zone_name_a not in self.zones:
            raise MapValidationError(
                f"Conexao refere zona inexistente: '{zone_name_a}'."
            )

        if zone_name_b not in self.zones:
            raise MapValidationError(
                f"Conexao refere zona inexistente: '{zone_name_b}'."
            )

        zone_a = self.zones[zone_name_a]
        zone_b = self.zones[zone_name_b]
        connection = Connection(zone_a, zone_b, max_capacity)

        if connection.canonical_id in self._connection_ids:
            raise MapValidationError(
                f"Conexao duplicada entre '{zone_name_a}' e '{zone_name_b}'."
            )

        self.connections.append(connection)
        self._connection_ids.add(connection.canonical_id)
        self._adjacency[zone_name_a].append((zone_b, connection))
        self._adjacency[zone_name_b].append((zone_a, connection))

    def get_neighbours(self, zone_name: str) -> list[tuple[Zone, Connection]]:
        if zone_name not in self._adjacency:
            return []
        return [
            (neighbour, conn)
            for neighbour, conn in self._adjacency[zone_name]
            if neighbour.is_accessible
        ]

    def validate_topology(self) -> None:
        if self.start_hub is None:
            raise MapValidationError(
                "Falta a diefinicao obrigatoria de 'start_hub'."
            )

        if self.end_hub is None:
            raise MapValidationError(
                "Falta a definicao obrigatoria de 'end_hub'."
            )

        if self.start_hub.name == self.end_hub.name:
            raise MapValidationError(
                "O ponto de partida e de chegada nao podem coincidir."
            )

        if not self.start_hub.is_accessible:
            raise MapValidationError(
                "O 'start_hub' nao pode ter o tipo 'blocked'."
            )

        if not self.end_hub.is_accessible:
            raise MapValidationError(
                "O 'end_hub' nao pode ter o tipo 'blocked'."
            )

        if not self._is_reachable(self.start_hub.name, self.end_hub.name):
            raise MapValidationError(
                f"Nao existe caminho viavel de '{self.start_hub.name} "
                f"ate '{self.end_hub.name}'."
            )

    def _is_reachable(self, start_name: str, end_name: str) -> bool:
        visited: set[str] = {start_name}
        queue: deque[str] = deque([start_name])

        while queue:
            current = queue.popleft()
            if current == end_name:
                return True

            for neighbour, _ in self.get_neighbours(current):
                if neighbour.name not in visited:
                    visited.add(neighbour.name)
                    queue.append(neighbour.name)
        return False
