from dataclasses import dataclass
from typing import Optional
from src.core.drone import Drone
from src.core.network import DroneNetwork
from src.routing.router import PathStep, Router


@dataclass(frozen=True)
class TurnResult:
    """Encapsula as movimentacoes e o snapshot de capacidade de um turno"""
    turn_number: int
    movements: list[str]
    capacity_snapshot: list[str]

    @property
    def output_line(self) -> str:
        """Linha formatada de movimentos (coisa do subject)"""
        return " ".join(self.movements)


class SimulationEngine:
    """Executa a movimentacao turno a turno e gera as saidas da sim"""
    def __init__(self, network: DroneNetwork, router: Router) -> None:
        self.network: DroneNetwork = network
        self.router: Router = router
        self.drones: dict[int, Drone] = self._initialize_drones()
        self.turns_history: list[TurnResult] = []

    def _initialize_drones(self) -> dict[int, Drone]:
        """Instancia a frota completa posicionada no start_hub"""
        if self.network.start_hub is None:
            raise RuntimeError(
                "Nao e possivel instanciar drones: 'start_hub'"
                " nao definido."
            )
        drones_dict: dict[int, Drone] = {}
        for drone_id in range(1, self.network.nb_drones + 1):
            drones_dict[drone_id] = Drone(drone_id, self.network.start_hub)
        return drones_dict

    def run(self) -> list[TurnResult]:
        """Executa a simulacao completa do inicio ate todos os drones
        chegarem a meta"""
        # Calcula as trajetorias coordenadas sem colisoes
        plan = self.router.find_plan()

        # Mapeia os passos para acesso O(1):
        # steps_by_drone_turn[drone_id][turn] -> PathStep
        steps_map: dict[int, dict[int, PathStep]] = {
            drone_id: {step.turn: step for step in steps}
            for drone_id, steps in plan.items()
        }
        # Turno maximo previsto
        max_turn = max(
            (max(steps_by_turn.keys()) for steps_by_turn in
                steps_map.values() if steps_by_turn), default=0
        )

        current_turn = 1
        while current_turn <= max_turn:
            turn_moves: list[str] = []

            for drone_id in sorted(self.drones.keys()):
                drone = self.drones[drone_id]

                if drone.is_delivered:
                    continue

                drone_steps = steps_map.get(drone_id, {})
                step: Optional[PathStep] = drone_steps.get(current_turn)

                if step is None or step.is_wait:
                    continue

                if drone.is_in_flight:
                    landing_output = drone.advance_transit()
                    if landing_output:
                        turn_moves.append(landing_output)
                else:
                    if step.connection is None:
                        continue
                    move_output = drone.start_move(step.zone, step.connection)
                    turn_moves.append(move_output)

            capacity_info = self._get_turn_capacity_snapshot()

            result = TurnResult(
                turn_number=current_turn,
                movements=turn_moves,
                capacity_snapshot=capacity_info
            )
            self.turns_history.append(result)
            current_turn += 1
        return self.turns_history

    def _get_turn_capacity_snapshot(self) -> list[str]:
        """Gera o snapshot formatado do uso de capacidade de nos e ligacoes"""
        snapshot: list[str] = []

        # Informacao de zonas (exlcuindo start_hub e end_hub duuuuuhhhHhhhh)
        for zone_name in sorted(self.network.zones.keys()):
            zone = self.network.zones[zone_name]
            if not zone.is_start and not zone.is_end:
                snapshot.append(zone.capacity_info())

        # Informacao de conexoes
        for conn in self.network.connections:
            snapshot.append(conn.capacity_info())

        return snapshot
