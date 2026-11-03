import pytest
from src.core.zone import Zone, ZoneType
from src.core.connection import Connection
from src.core.drone import Drone, DroneState


def test_drone_lifecycle_single_hop() -> None:
    """Valida o movimento de 1 turno entre start_hub e end_hub."""
    start = Zone("start", 0, 0, is_start=True)
    goal = Zone("goal", 1, 1, is_end=True)
    conn = Connection(start, goal)

    drone = Drone(1, start)
    assert drone.tag == "D1"
    assert drone.state == DroneState.AT_REST
    assert not drone.is_delivered

    # Movimento para o destino
    output = drone.start_move(goal, conn)
    assert output == "D1-goal"
    assert drone.is_delivered
    assert drone.current_zone == goal
    assert start.current_drones == 0


def test_drone_restricted_zone_two_turns() -> None:
    """Valida a mecânica de 2 turnos com retenção de conexão-zona restrita."""
    start = Zone("start", 0, 0, is_start=True)
    restricted = Zone(
        "restr", 1, 1, zone_type=ZoneType.RESTRICTED, max_drones=1
        )
    conn = Connection(start, restricted)

    drone = Drone(2, start)

    # Turno 1: Descola para a conexão
    step1 = drone.start_move(restricted, conn)
    assert step1 == f"D2-{conn.display_name}"
    assert drone.is_in_flight
    assert conn.current_transit == 1
    assert restricted.current_drones == 0  # Ainda não aterrou

    # Turno 2: Conclui a travessia
    step2 = drone.advance_transit()
    assert step2 == "D2-restr"
    assert not drone.is_in_flight
    assert conn.current_transit == 0  # Ligação libertada
    assert restricted.current_drones == 1  # Zona ocupada


def test_invalid_drone_id() -> None:
    """Garante que IDs menores ou iguais a zero são rejeitados."""
    start = Zone("start", 0, 0, is_start=True)
    with pytest.raises(ValueError):
        Drone(0, start)
    with pytest.raises(ValueError):
        Drone(-3, start)
