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


def test_forbidden_dash_in_zone_name() -> None:
    raw_data = [
        "nb_drones: 2",
        "start_hub: start 0 0",
        "end_hub: goal 10 10",
        "hub: zone-invalid 5 5"
    ]
    with pytest.raises(ParsingError) as exc_info:
        MapParser.parse_lines(raw_data)
    assert "hifens sao proibidos." in str(exc_info.value)


def test_invalid_zone_type() -> None:
    raw_data = [
        "nb_drones: 1",
        "start_hub: start 0 0",
        "end_hub: goal 10 10",
        "hub: mid 2 2 [zone=hyperloop]"
        ]
    with pytest.raises(ParsingError) as exc_info:
        MapParser.parse_lines(raw_data)
    assert "Tipo de zona invalida" in str(exc_info.value)


def test_invalid_capacity_values() -> None:
    raw_data_zone = [
        "nb_drones: 1",
        "start_hub: start 0 0",
        "end_hub: goal 10 10",
        "hub: mid 2 2 [max_drones=0]"
        ]
    with pytest.raises(ParsingError) as exc_info:
        MapParser.parse_lines(raw_data_zone)
    assert "'max_drones' invalido" in str(exc_info.value)

    raw_data_link = [
        "nb_drones: 1",
        "start_hub: start 0 0",
        "end_hub: goal 10 10",
        "hub: mid 2 2",
        "connection: start-mid [max_link_capacity=-2]"
    ]
    with pytest.raises(ParsingError) as exc_info:
        MapParser.parse_lines(raw_data_link)
    assert "'max_link_capacity' invalido" in str(exc_info.value)


def test_missing_start_or_end_hub() -> None:
    missing_end = [
        "nb_drones: 1",
        "start_hub: start 0 0",
        "hub: mid 1 1",
        "connection: start-mid"
    ]
    with pytest.raises(ParsingError) as exc_info:
        MapParser.parse_lines(missing_end)
    assert (
        "falta a definicao obrigatoria de 'end_hub:'"
        in str(exc_info.value)
    )


def test_duplicate_zone_names() -> None:
    raw_data = [
        "nb_drones: 1",
        "start_hub: start 0 0",
        "end_hub: goal 10 10",
        "hub: duplicate 2 2",
        "hub: duplicate 3 3"
        ]
    with pytest.raises(ParsingError) as exc_info:
        MapParser.parse_lines(raw_data)
    assert (
        "Zona duplicada encontrada: 'duplicate'"
        in str(exc_info.value)
    )


def test_duplicate_connection() -> None:
    raw_data = [
        "nb_drones: 1",
        "start_hub: start 0 0",
        "end_hub: goal 10 10",
        "connection: start-goal",
        "connection: goal-start"
        ]
    with pytest.raises(ParsingError) as exc_info:
        MapParser.parse_lines(raw_data)
    assert (
        "Conexao duplicada entre 'goal' e 'start'"
        in str(exc_info.value)
    )


def test_disconnected_graph() -> None:
    raw_data = [
        "nb_drones: 2",
        "start_hub: start 0 0",
        "end_hub: goal 10 10",
        "hub: island 5 5"
        "connection: start-island"
        ]
    with pytest.raises(ParsingError) as exc_info:
        MapParser.parse_lines(raw_data)
    assert "Grafo desconexo" in str(exc_info.value)


def test_start_and_end_capacity_metadata_ignores() -> None:
    raw_data = [
        "nb_drones: 10",
        "start_hub: start 0 0 [max_drones=1]",
        "end_hub: goal 10 10[max_drones=2]",
        "connection: start-goal"
        ]
    network = MapParser.parse_lines(raw_data)
    assert network.start_hub is not None
    assert network.start_hub.max_drones is None
    assert network.end_hub is not None
    assert network.end_hub.max_drones is None
