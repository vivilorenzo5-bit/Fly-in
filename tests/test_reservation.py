import pytest
from src.core.zone import Zone, ZoneType
from src.core.connection import Connection
from src.routing.reservation import ReservationTable


def test_zone_capacity_enforcement() -> None:
    """Valida o controlo estrito de capacidade numa
    zona comum (max_drones=1)."""
    table = ReservationTable()
    zone = Zone("mid", 1, 1, max_drones=1)

    assert table.is_zone_available(zone, turn=1)
    table.reserve_zone(zone, turn=1)

    # No turno 1 está cheia
    assert not table.is_zone_available(zone, turn=1)
    with pytest.raises(ValueError):
        table.reserve_zone(zone, turn=1)

    # No turno 2 continua livre
    assert table.is_zone_available(zone, turn=2)


def test_infinite_capacity_hubs() -> None:
    """Garante que start_hub e end_hub aceitam múltiplos drones
    no mesmo turno."""
    table = ReservationTable()
    start = Zone("start", 0, 0, is_start=True)

    for i in range(50):
        assert table.is_zone_available(start, turn=1)
        table.reserve_zone(start, turn=1)

    assert table.get_zone_usage("start", turn=1) == 50


def test_link_capacity_enforcement() -> None:
    """Valida a capacidade de trânsito em ligações com max_link_capacity=2."""
    table = ReservationTable()
    za = Zone("a", 0, 0)
    zb = Zone("b", 1, 1)
    conn = Connection(za, zb, max_capacity=2)

    assert table.is_link_available(conn, turn=3)
    table.reserve_link(conn, turn=3)
    assert table.is_link_available(conn, turn=3)
    table.reserve_link(conn, turn=3)

    # Capacidade máxima atingida
    assert not table.is_link_available(conn, turn=3)
    with pytest.raises(ValueError):
        table.reserve_link(conn, turn=3)


def test_cancel_reservations() -> None:
    """Verifica a libertação correta de capacidade ao cancelar reservas."""
    table = ReservationTable()
    zone = Zone("hub1", 0, 0, max_drones=1)

    table.reserve_zone(zone, turn=4)
    assert not table.is_zone_available(zone, turn=4)

    table.cancel_zone_reservation(zone, turn=4)
    assert table.is_zone_available(zone, turn=4)
    assert table.get_zone_usage("hub1", turn=4) == 0


def test_blocked_zone_is_never_available() -> None:
    """Garante que zonas bloqueadas são rejeitadas em qualquer turno."""
    table = ReservationTable()
    blocked = Zone("wall", 2, 2, zone_type=ZoneType.BLOCKED)

    assert not table.is_zone_available(blocked, turn=1)
