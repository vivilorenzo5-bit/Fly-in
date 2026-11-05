from src.core.zone import Zone, ZoneType
from src.core.network import DroneNetwork
from src.routing.reservation import ReservationTable
from src.routing.router import Router


def test_linear_path_two_drones_pipelining() -> None:
    """Valida o avanço em comboio (pipelining) de 2 drones num caminho linear."""
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
    plan = router.find_plan()

    assert 1 in plan and 2 in plan

    # Drone 1: Turno 1 -> mid, Turno 2 -> goal
    d1_steps = plan[1]
    assert len(d1_steps) == 2
    assert d1_steps[0].turn == 1 and d1_steps[0].zone.name == "mid"
    assert d1_steps[1].turn == 2 and d1_steps[1].zone.name == "goal"

    # Drone 2: Turno 1 -> espera em start, Turno 2 -> mid, Turno 3 -> goal
    d2_steps = plan[2]
    assert len(d2_steps) == 3
    assert d2_steps[0].turn == 1 and d2_steps[0].is_wait
    assert d2_steps[1].turn == 2 and d2_steps[1].zone.name == "mid"
    assert d2_steps[2].turn == 3 and d2_steps[2].zone.name == "goal"


def test_restricted_zone_two_turns_path() -> None:
    """Valida o planeamento de rota através de zona restrita com custo 2 turnos."""
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
    plan = router.find_plan()

    d1_steps = plan[1]
    # Esperado: 3 passos -> Turno 1: voo para restr, Turno 2: aterragem em restr, Turno 3: goal
    assert len(d1_steps) == 3
    assert d1_steps[0].turn == 1 and d1_steps[0].is_transit_start
    assert d1_steps[1].turn == 2 and d1_steps[1].zone.name == "restr"
    assert d1_steps[2].turn == 3 and d1_steps[2].zone.name == "goal"


def test_parallel_paths_distribution() -> None:
    """Garante que múltiplos drones se distribuem por caminhos alternativos paralelos."""
    net = DroneNetwork(nb_drones=2)
    start = Zone("start", 0, 0, is_start=True)
    top = Zone("top", 1, 2, max_drones=1)
    bot = Zone("bot", 1, 0, max_drones=1)
    goal = Zone("goal", 2, 1, is_end=True)

    net.add_zone(start)
    net.add_zone(top)
    net.add_zone(bot)
    net.add_zone(goal)
    net.add_connection("start", "top")
    net.add_connection("top", "goal")
    net.add_connection("start", "bot")
    net.add_connection("bot", "goal")

    table = ReservationTable()
    router = Router(net, table)
    plan = router.find_plan()

    # Como existem 2 caminhos de comprimento idêntico, ambos devem chegar no turno 2
    assert plan[1][-1].turn == 2
    assert plan[2][-1].turn == 2
    # Um drone deve usar 'top' e o outro 'bot'
    intermediate_zones = {plan[1][0].zone.name, plan[2][0].zone.name}
    assert intermediate_zones == {"top", "bot"}
