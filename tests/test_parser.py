import pytest
from src.core.exceptions import ParsingError
from src.core.zone import ZoneType
from src.parser.map_parser import MapParser


def test_valid_map_parsing() -> None:
    raw_data = [
        "#Comentario inicial",
        "nb_drones: 4",
        "start_hub: start 0 0 [color=green]",
        "end_hub: goal 10 10 [color=yellow]",
        "hub: junction 2 2 [zone priority color=blue max_drones=2]",
        "hub: buffer 4 4 [zone restricted color=red max_drones=3]",
        "connection: start-junction [max_link_capacity=2]",
        "connection: junction-buffer",
        "connection: buffer-goal # comentario inline"
    ]
    network = MapParser.parse_lines(raw_data)

    assert network.nb_drones == 4
    assert network.start_hub is not None
    assert network.start_hub.name == "start"
    assert network.start_hub.max_drones is None

    assert network.end_hub is not None
    assert network.end_hub.name == "goal"
    assert network.end_hub.max_drones is None

    assert "junction" in network.zones
    junction = network.zones["junction"]
    assert junction.zone_type == ZoneType.PRIORITY
    assert junction.max_drones == 2
    assert junction.color == "blue"

    assert "buffer" in network.zones
    buffer_zone = network.zones["buffer"]
    assert buffer_zone.zone_type == ZoneType.RESTRICTED
    assert buffer_zone.max_drones == 3
    assert buffer_zone.cost == 2

    assert len(network.connections) == 3
    assert network.connections[0].max_capacity == 2
    assert network.connections[1].max_capacity == 1


def test_missing_nb_drones() -> None:
    raw_data = [
        "#Apenas comentario",
        "start_hub: start 0 0",
        "end_hub: goal 1 1"
    ]
    with pytest.raises(ParsingError) as exc_info:
        MapParser.parse_lines(raw_data)
    assert (
        "A primeira diretiva do mapa tem de ser 'nb_drones:'"
        in str(exc_info.value)
    )


def test_invalid_nb_drones_values() -> None:
    invalid_cases = ["nb_drones: 0", "nb_drones: -5", "nb_drones: abc"]
    for case in invalid_cases:
        with pytest.raises(ParsingError):
            MapParser.parse_lines([case])


