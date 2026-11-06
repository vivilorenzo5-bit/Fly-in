"""Testes unitários para o visualizador de terminal."""

from src.core.zone import Zone
from src.core.network import DroneNetwork
from src.simulation.engine import TurnResult
from src.visualiser.terminal_view import TerminalVisualiser


def test_colorize_known_and_unknown_colors() -> None:
    """Valida a aplicação de cores conhecidas e fallback limpo para cores desconhecidas."""
    red_text = TerminalVisualiser.colorize("alerta", "red")
    assert "\033[31m" in red_text
    assert "\033[0m" in red_text

    # Cor inexistente deve devolver o texto simples sem corromper
    plain_text = TerminalVisualiser.colorize("normal", "ultraviolet")
    assert plain_text == "normal"


def test_render_turn_with_zone_colors() -> None:
    """Garante que as cores das zonas no mapa são aplicadas aos nomes na saída."""
    net = DroneNetwork(nb_drones=1)
    green_zone = Zone("roof", 1, 1, color="green")
    net.add_zone(green_zone)

    turn = TurnResult(turn_number=1, movements=["D1-roof"], capacity_snapshot=[])
    rendered = TerminalVisualiser.render_turn(turn, net)

    # D1 deve ter ciano e roof deve ter verde
    assert "\033[36m" in rendered  # Cyan do drone
    assert "\033[32m" in rendered  # Green da zona
    assert "D1" in rendered
    assert "roof" in rendered
