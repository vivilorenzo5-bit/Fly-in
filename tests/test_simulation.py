"""Testes de integração e unidade para validação do SimulationEngine."""

from src.core.zone import Zone, ZoneType
from src.core.network import DroneNetwork
from src.routing.reservation import ReservationTable
from src.routing.router import Router
from src.simulation.engine import SimulationEngine


def test_simulation_simple_linear_output_format() -> None:
    """Valida o formato exato das linhas de saída num mapa linear com 2 drones."""
    net = DroneNetwork(nb_drones=2)
    start = Zone("start", 0, 0, is_start=True)
    mid = Zone("mid", 1, 1, max_drones=1)
    goal = Zone("goal", 2, 2, is_end=True)

    net.add_zone(start)
    net.add_zone(mid)
    net.add_zone(goal)
    net.add_connection("start", "mid")
    net.add_connection("mid", "goal")

    table = ReservationTable()
    router = Router(net, table)
    engine = SimulationEngine(net, router)

    results = engine.run()

    # O pipeline com 2 drones num trajeto de 2 passos demora 3 turnos
    assert len(results) == 3

    # Turno 1: D1 move-se para mid (D2 aguarda em start e não aparece)
    assert results[0].output_line == "D1-mid"

    # Turno 2: D1 avança para goal, D2 entra em mid
    assert results[1].output_line == "D1-goal D2-mid"

    # Turno 3: D1 já foi entregue (não aparece), D2 chega a goal
    assert results[2].output_line == "D2-goal"


def test_simulation_restricted_zone_transit_format() -> None:
    """Valida a emissão de D<ID>-<connection> durante o trânsito para zona restrita."""
    net = DroneNetwork(nb_drones=1)
    start = Zone("start", 0, 0, is_start=True)
    restr = Zone("restr", 1, 1, zone_type=ZoneType.RESTRICTED, max_drones=1)
    goal = Zone("goal", 2, 2, is_end=True)

    net.add_zone(start)
    net.add_zone(restr)
    net.add_zone(goal)
    net.add_connection("start", "restr")
    net.add_connection("restr", "goal")

    table = ReservationTable()
    router = Router(net, table)
    engine = SimulationEngine(net, router)

    results = engine.run()

    # Turno 1: Voo na conexão (D1-start-restr)
    assert results[0].output_line == "D1-start-restr"

    # Turno 2: Aterragem na zona restrita (D1-restr)
    assert results[1].output_line == "D1-restr"

    # Turno 3: Chegada à meta (D1-goal)
    assert results[2].output_line == "D1-goal"


def test_simulation_capacity_snapshot() -> None:
    """Valida a recolha de informação de capacidade para suportar o Live Coding."""
    net = DroneNetwork(nb_drones=1)
    start = Zone("start", 0, 0, is_start=True)
    mid = Zone("mid", 1, 1, max_drones=1)
    goal = Zone("goal", 2, 2, is_end=True)

    net.add_zone(start)
    net.add_zone(mid)
    net.add_zone(goal)
    net.add_connection("start", "mid")
    net.add_connection("mid", "goal")

    table = ReservationTable()
    router = Router(net, table)
    engine = SimulationEngine(net, router)

    results = engine.run()

    # No Turno 1, o D1 está na zona mid
    snap_t1 = results[0].capacity_snapshot
    assert any("Zone mid: 1/1 drones" in item for item in snap_t1)
