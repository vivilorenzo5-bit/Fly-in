from typing import Optional
from src.core.network import DroneNetwork
from src.core.zone import Zone
from src.simulation.engine import TurnResult


class TerminalVisualiser:
    """Renderiza a simulacao com cores no terminal"""
    ANSI_COLOURS: dict[str, str] = {
        "black": "\033[30m",
        "red": "\033[31m",
        "green": "\033[32m",
        "yellow": "\033[33m",
        "blue": "\033[34m",
        "magenta": "\033[35m",
        "purple": "\033[35m",
        "cyan": "\033[36m",
        "white": "\033[37m",
        "gray": "\033[90m",
        "grey": "\033[90m",
    }
    ANSI_BOLD: str = "\033[1m"
    ANSI_RESET: str = "\033[0m"

    @classmethod
    def colorize(
            cls, text: str, color_name: Optional[str], bold: bool = False
            ) -> str:
        """Aplica estilo e cor ANSI a uma string"""
        if not color_name:
            return f"{cls.ANSI_BOLD}{text}{cls.ANSI_RESET}" if bold else text

        code = cls.ANSI_COLOURS.get(color_name.lower(), "")
        if not code:
            return f"{cls.ANSI_BOLD}{text}{cls.ANSI_RESET}" if bold else text

        prefix = f"{cls.ANSI_BOLD}{code}" if bold else code
        return f"{prefix}{text}{cls.ANSI_RESET}"

    @classmethod
    def render_turn(cls, result: TurnResult, network: DroneNetwork) -> str:
        """Formata uma linha de turno com as suas cores nas zonas do mapa"""
        if not result.movements:
            return f"Turno{result.turn_number}: [sem movimentos]"

        coloured_moves: list[str] = []
        for move in result.movements:
            # Format = D<ID>-<destino>
            drone_tag, dest_name = move.split("-", 1)
            if dest_name in network.zones:
                zone: Zone = network.zones[dest_name]
                coloured_dest = cls.colorize(dest_name, zone.color, bold=True)
            else:
                coloured_dest = cls.colorize(dest_name, "magenta", bold=True)

            drone_coloured = cls.colorize(drone_tag, "cyan", bold=True)
            coloured_moves.append(f"{drone_coloured}-{coloured_dest}")
        return " ".join(coloured_moves)

    @classmethod
    def render_dashboard(
        cls,
        network: DroneNetwork,
        turns: list[TurnResult],
        show_capacity: bool = False
    ) -> None:
        """Exibe um painel visual completo com historico de turnos e sumario"""
        print(
            cls.colorize(
                "\n=== Fly-In: Simulacao de trafego aereo ===", "cyan",
                bold=True
                )
            )
        print(
            f"Drones: {network.nb_drones} | Zonas: {len(network.zones)} | "
            f"Conexoes: {network.connections}"
            )
        print(
            f"Partida: {network.start_hub.name if network.start_hub else '?'}"
            f" -> Chegada: {network.end_hub.name if network.end_hub else '?'}"
            "\n"
        )

        for turn in turns:
            turn_header = cls.colorize(
                f"[Turno {turn.turn_number:02d}]", "yellow", bold=True
                )
            moves_display = cls.render_turn(turn, network)
            print(f"{turn_header} {moves_display}")

            # if show_capacity and turn.capacity_snapshot:
            #     cap_str = ", ".join(turn.capacity_snapshot)
            #     print(cls.colorize(f"      |-> Uso: {cap_str}", "gray"))

        total_turns = len(turns)
        print(cls.colorize(
            f"Simulacao concluida com sucesso em {total_turns} turnos.",
            "green", bold=True
            ))
