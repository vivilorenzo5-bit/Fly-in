import heapq
from dataclasses import dataclass
from typing import Optional
from src.core.exceptions import SimulationError
from src.core.zone import Zone, ZoneType
from src.core.connection import Connection
from src.core.network import DroneNetwork
from src.routing.reservation import ReservationTable


@dataclass(frozen=True)
class PathStep:
    """Representa uma acao discreta planeada para um drone
        num turno especifico"""
    turn: int
    zone: Zone
    connection: Optional[Connection] = None
    is_wait: bool = False
    is_transit_start: bool = False


QueueItem = tuple[int, int, int, int, int, str, list[PathStep]]


class Router:
    """Orquestrador de pesquisa de rotas livres de colisoes"""
    def __init__(
            self, network: DroneNetwork, reservation_table: ReservationTable
    ) -> None:
        self.network: DroneNetwork = network
        self.reservation_table: ReservationTable = reservation_table
        self._heuristics: dict[str, int] = self._compute_heuristics()

    def _compute_heuristics(self) -> dict[str, int]:
        """Calcula o custo minimo em turnos ate ao end_hub via rev Dijkstra"""
        if self.network.end_hub is None:
            return {}

        end_name = self.network.end_hub.name
        # min heap com tuples (custo_acumulado, nome_da_zona)
        heap: list[tuple[int, str]] = [(0, end_name)]
        min_costs: dict[str, int,] = {end_name: 0}

        while heap:
            cost, current_name = heapq.heappop(heap)
            if cost > min_costs[current_name]:
                continue
            for neighbour, _ in self.network.get_neighbours(current_name):
                if not neighbour.is_accessible:
                    continue
                current_zone = self.network.zones[current_name]
                step_cost = current_zone.cost
                new_cost = cost + step_cost

                if (
                    neighbour.name not in min_costs or
                    new_cost < min_costs[neighbour.name]
                ):
                    min_costs[neighbour.name] = new_cost
                    heapq.heappush(heap, (new_cost, neighbour.name))
        return min_costs

    def find_plan(self) -> dict[int, list[PathStep]]:
        """Gera o plano de voo individual e coordenado para toda a frota"""
        fleet_plan: dict[int, list[PathStep]] = {}

        for drone_id in range(1, self.network.nb_drones + 1):
            path = self._find_path_for_drone(drone_id)
            if not path:
                raise SimulationError(
                    f"Impossivel encontrar rota viavel para o drone "
                    f"D{drone_id}. A rede encontra-se saturada ou bloqueada."
                )
            self._commit_path_reservations(path)
            fleet_plan[drone_id] = path
        return fleet_plan

    def _commit_path_reservations(self, path: list[PathStep]) -> None:
        """Regista as reservas de zonas e ligacoes planeadas na ResTable"""
        for step in path:
            if step.is_wait:
                if not step.zone.is_start:
                    self.reservation_table.reserve_zone(step.zone, step.turn)
            elif step.is_transit_start:
                if step.connection is not None:
                    self.reservation_table.reserve_link(
                        step.connection, step.turn)
            else:
                if (
                    step.connection is not None and
                    not step.zone.zone_type == ZoneType.RESTRICTED
                ):
                    self.reservation_table.reserve_link(
                        step.connection, step.turn)
                self.reservation_table.reserve_zone(step.zone, step.turn)

    def _find_path_for_drone(self, drone_id: int) -> Optional[list[PathStep]]:
        start_zone = self.network.start_hub
        end_zone = self.network.end_hub
        if start_zone is None or end_zone is None:
            return None

        max_horizon = max(
            100, len(self.network.zones) * 10 + self.network.nb_drones * 5)
        counter = 0
        h_start = self._heuristics.get(start_zone.name, 0)
        start_state: QueueItem = (
            h_start, 0, 0, 0, counter, start_zone.name, []
        )
        heap: list[
            tuple[
                int, int, int, int, int, str, list[PathStep]]] = [start_state]
        visited: set[tuple[str, int]] = set()

        while heap:
            (f_score, neg_prio, g_score, turn, _,
             curr_name, steps) = heapq.heappop(heap)
            state_key = (curr_name, turn)

            if state_key in visited:
                continue
            visited.add(state_key)

            curr_zone = self.network.zones[curr_name]

            if curr_zone.is_end:
                return steps
            if turn >= max_horizon:
                continue

            # Expansao 1: mover para zonas vizinhas acessiveis
            for neighbour, conn in self.network.get_neighbours(curr_name):
                if not neighbour.is_accessible:
                    continue

                prio_inc = 1 if neighbour.zone_type == ZoneType.PRIORITY else 0

                if neighbour.zone_type == ZoneType.RESTRICTED:
                    # Zona restrita: custo de 2 turnos
                    t_flight = turn + 1
                    t_land = turn + 2

                    if (
                        self.reservation_table.is_link_available(
                            conn, t_flight)
                        and self.reservation_table.is_zone_available(
                            neighbour, t_land)
                    ):
                        step_flight = PathStep(
                            turn=t_flight,
                            zone=neighbour,
                            connection=conn,
                            is_transit_start=True,
                        )
                        step_land = PathStep(
                            turn=t_land,
                            zone=neighbour,
                            connection=conn,
                        )
                        new_g = g_score + 2
                        new_h = self._heuristics.get(neighbour.name, 0)
                        counter += 1
                        heapq.heappush(
                            heap,
                            (
                                new_g + new_h,
                                neg_prio - prio_inc,
                                new_g,
                                t_land,
                                counter,
                                neighbour.name,
                                steps + [step_flight, step_land],
                            ),
                        )
                else:
                    # Zona normal ou prioritaria: custo de 1 turno
                    t_land = turn + 1
                    if (
                        self.reservation_table.is_link_available(conn, t_land)
                        and self.reservation_table.is_zone_available(
                            neighbour, t_land)
                    ):
                        step = PathStep(
                            turn=t_land,
                            zone=neighbour,
                            connection=conn,
                        )
                        new_g = g_score + 1
                        new_h = self._heuristics.get(neighbour.name, 0)
                        counter += 1
                        heapq.heappush(
                            heap,
                            (
                                new_g + new_h,
                                neg_prio - prio_inc,
                                new_g,
                                t_land,
                                counter,
                                neighbour.name,
                                steps + [step],
                            ),
                        )

            # Expansao 2: aguardar na zona atual (fora do loop for de vizinhos)
            t_wait = turn + 1
            if (
                curr_zone.is_start
                or self.reservation_table.is_zone_available(curr_zone, t_wait)
            ):
                wait_step = PathStep(
                    turn=t_wait,
                    zone=curr_zone,
                    is_wait=True,
                )
                new_g = g_score + 1
                new_h = self._heuristics.get(curr_zone.name, 0)
                counter += 1
                heapq.heappush(
                    heap,
                    (
                        new_g + new_h,
                        neg_prio,
                        new_g,
                        t_wait,
                        counter,
                        curr_zone.name,
                        steps + [wait_step],
                    ),
                )
        return None
