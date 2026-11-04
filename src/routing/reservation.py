from src.core.zone import Zone
from src.core.connection import Connection


class ReservationTable:
    """Tabela de reservas para zonas e ligacoes"""
    def __init__(self) -> None:
        # nome da zona, turno, nbr de drones agendados
        self._zone_reservations: dict[tuple[str, int], int] = {}
        # id_da_ligacao, turno, nbr de travessias agendadas
        self._link_reservations: dict[tuple[str, int], int] = {}

    def is_zone_available(self, zone: Zone, turn: int) -> bool:
        """Verifica se uma zona tem capacidade livre num turno especifico"""
        if not zone.is_accessible:
            return False
        if zone.max_drones is None:
            return True

        current_occupancy = self.get_zone_usage(zone.name, turn)
        return current_occupancy < zone.max_drones

    def is_link_available(self, connection: Connection, turn: int) -> bool:
        """Verifica se uma ligacao suporta mais uma travessia num turno
            especifico"""
        current_usage = self.get_link_usage(connection.canonical_id, turn)
        return current_usage < connection.max_capacity

    def reserve_zone(self, zone: Zone, turn: int) -> None:
        """Reserva uma vaga numa zona para um determinado turno"""
        key = (zone.name, turn)
        current = self._zone_reservations.get(key, 0)

        if zone.max_drones is not None and current >= zone.max_drones:
            raise ValueError(
                f"Capacidade excedida na zona '{zone.name}' no turno {turn}: "
                f"{current}/{zone.max_drones}."
            )

        self._zone_reservations[key] = current + 1

    def reserve_link(self, connection: Connection, turn: int) -> None:
        """Reserva passagem numa ligacao para um determinado turno"""
        key = (connection.canonical_id, turn)
        current = self._link_reservations.get(key, 0)

        if current >= connection.max_capacity:
            raise ValueError(
                f"Capacidade excedida na ligacao '{connection.canonical_id}' "
                f"no turno {turn}: {current}/{connection.max_capacity}"
            )

        self._link_reservations[key] = current + 1

    def cancel_zone_reservation(self, zone: Zone, turn: int) -> None:
        """Cancela uma reserva previa de zona """
        key = (zone.name, turn)
        if key in self._zone_reservations:
            self._zone_reservations[key] -= 1
            if self._zone_reservations[key] <= 0:
                del self._zone_reservations[key]

    def cancel_link_reservation(
            self, connection: Connection, turn: int
            ) -> None:
        """Cancela uma reserva previa de ligacao"""
        key = (connection.canonical_id, turn)
        if key in self._link_reservations:
            self._link_reservations[key] -= 1
            if self._link_reservations[key] <= 0:
                del self._link_reservations[key]

    def get_zone_usage(self, zone_name: str, turn: int) -> int:
        """Retorna o numero de reservas ativas para uma zuna num turno"""
        return self._zone_reservations.get((zone_name, turn), 0)

    def get_link_usage(self, canonical_link_id: str, turn: int) -> int:
        """Retorna o numero de reservas ativas para uma ligacao num turno"""
        return self._link_reservations.get((canonical_link_id, turn), 0)

    def clear(self) -> None:
        """Limpa todas as reservas registadas na tabela."""
        self._zone_reservations.clear()
        self._link_reservations.clear()
