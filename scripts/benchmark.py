import sys
from pathlib import Path

# Adiciona a raiz do projeto ao sys.path para reconhecer o pacote 'src'
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

# Agora os imports de 'src' funcionam sem qualquer erro
import time
from dataclasses import dataclass
from typing import Dict, List, Optional
from src.parser.map_parser import MapParser
from src.routing.reservation import ReservationTable
from src.routing.router import Router
from src.simulation.engine import SimulationEngine


@dataclass(frozen=True)
class BenchmarkTarget:
    """Metas oficiais de turnos definidas no Chapter VII.7 do subject."""
    category: str
    relative_path: str
    target_turns: int
    is_strict_less: bool = False  # True quando a meta for estritamente '<' em vez de '<='


# Mapeamento oficial dos benchmarks do subject da 42
TARGETS: List[BenchmarkTarget] = [
    # Mapas Fáceis
    BenchmarkTarget("Easy", "easy/01_linear_path.txt", 6),
    BenchmarkTarget("Easy", "easy/02_simple_fork.txt", 8),
    BenchmarkTarget("Easy", "easy/03_basic_capacity.txt", 6),
    # Mapas Médios
    BenchmarkTarget("Medium", "medium/01_dead_end_trap.txt", 12),
    BenchmarkTarget("Medium", "medium/02_circular_loop.txt", 15),
    BenchmarkTarget("Medium", "medium/03_priority_puzzle.txt", 12),
    # Mapas Difíceis
    BenchmarkTarget("Hard", "hard/01_maze_nightmare.txt", 30),
    BenchmarkTarget("Hard", "hard/02_capacity_hell.txt", 35),
    BenchmarkTarget("Hard", "hard/03_ultimate_challenge.txt", 45, is_strict_less=True),
    # Mapa Challenger (Bónus)
    BenchmarkTarget("Challenger", "challenger/01_the_impossible_dream.txt", 45, is_strict_less=True),
]


def run_benchmark_on_map(map_path: Path) -> tuple[int, float]:
    """Executa a simulação completa num mapa e retorna (turnos, tempo_em_segundos)."""
    start_time = time.perf_counter()

    network = MapParser.parse_file(map_path)
    reservation_table = ReservationTable()
    router = Router(network, reservation_table)
    engine = SimulationEngine(network, router)

    turn_results = engine.run()
    elapsed_time = time.perf_counter() - start_time

    return len(turn_results), elapsed_time


def main() -> None:
    """Executa a suite completa de benchmarks e imprime a tabela de resultados."""
    base_maps_dir = Path("maps")
    if not base_maps_dir.exists():
        print("Erro: A pasta 'maps/' não foi encontrada na raiz do projeto.")
        return

    print("\n" + "=" * 80)
    print(f"{'CATEGORIA':<12} | {'MAPA':<32} | {'ALVO':<6} | {'OBTIDO':<6} | {'TEMPO':<8} | {'STATUS'}")
    print("=" * 80)

    category_results: Dict[str, List[bool]] = {}

    for item in TARGETS:
        full_path = base_maps_dir / item.relative_path
        map_name = Path(item.relative_path).name

        if not full_path.exists():
            print(f"{item.category:<12} | {map_name:<32} | {'?':<6} | {'N/A':<6} | {'N/A':<8} | IGNORADO")
            continue

        try:
            turns, exec_time = run_benchmark_on_map(full_path)

            if item.is_strict_less:
                target_str = f"< {item.target_turns}"
                passed = turns < item.target_turns
            else:
                target_str = f"<= {item.target_turns}"
                passed = turns <= item.target_turns

            status = "\033[32mPASSOU\033[0m" if passed else "\033[31mFALHOU\033[0m"
            time_str = f"{exec_time * 1000:.1f}ms"

            category_results.setdefault(item.category, []).append(passed)

            print(
                f"{item.category:<12} | {map_name:<32} | {target_str:<6} | "
                f"{turns:<6} | {time_str:<8} | {status}"
            )

        except Exception as err:
            print(f"{item.category:<12} | {map_name:<32} | {'ERRO':<6} | {'-':<6} | {'-':<8} | {err}")

    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()