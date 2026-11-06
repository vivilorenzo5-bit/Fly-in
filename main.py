import argparse
import sys
from src.core.exceptions import FlyinError
from src.parser.map_parser import MapParser
from src.routing.reservation import ReservationTable
from src.routing.router import Router
from src.simulation.engine import SimulationEngine
from src.visualiser.terminal_view import TerminalVisualiser


def parse_arguments() -> argparse.Namespace:
    """Configura e valida os argumentos passados."""
    parser = argparse.ArgumentParser(
        description="Fly-in: Simulador e otimizador de tráfego aéreo para "
        "frota de drones."
    )
    parser.add_argument(
        "map_file",
        type=str,
        help="Caminho para o ficheiro de configuração do mapa."
    )
    parser.add_argument(
        "--visual",
        "-v",
        action="store_true",
        help="Ativa a visualização interativa colorida e o painel de "
        "controlo da simulação."
    )
    parser.add_argument(
        "--capacity-info",
        action="store_true",
        help="Exibe informação de uso de capacidade das zonas e conexões "
        "turno a turno."
    )
    return parser.parse_args()


def main() -> None:
    """Orquestra a leitura do mapa, o planeamento de rotas
    e a execução da simulação."""
    args = parse_arguments()

    try:
        # 1. Parsing e validação da topologia da rede
        network = MapParser.parse_file(args.map_file)

        # 2. Inicialização da tabela de reservas e cálculo do plano ótimo
        # (Space-Time A*)
        reservation_table = ReservationTable()
        router = Router(network, reservation_table)

        # 3. Execução do motor de simulação discreta
        engine = SimulationEngine(network, router)
        turn_results = engine.run()

        # 4. Saída conforme os modos selecionados
        if args.visual:
            TerminalVisualiser.render_dashboard(
                network,
                turn_results,
                show_capacity=args.capacity_info
            )
        else:
            # Modo padrão exigido pelo subject: turnos em linhas de texto puro
            for turn in turn_results:
                if turn.movements:
                    print(turn.output_line)
                # if args.capacity_info and turn.capacity_snapshot:
                    # Formato exato estipulado na avaliação para live coding
                    # cap_details = ", ".join(turn.capacity_snapshot)
                    # print(f"Turn {turn.turn_number} Capacity: {cap_details}")

    except FlyinError as err:
        # cena do subject: terminação sem traceback não controlado
        sys.stderr.write(f"Error: {err}\n")
        sys.exit(1)
    except Exception as unexpected_err:
        sys.stderr.write(f"Unexpected Error: {unexpected_err}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
    sys.exit(0)
