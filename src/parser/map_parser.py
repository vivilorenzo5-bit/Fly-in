from pathlib import Path
from typing import Optional
from src.core.exceptions import ParsingError, MapValidationError
from src.core.zone import Zone, ZoneType
from src.core.network import DroneNetwork


class MapParser:
    @classmethod
    def parse_file(cls, file_path: str | Path) -> DroneNetwork:
        path = Path(file_path)
        if not path.is_file():
            raise ParsingError(
                0, str(file_path), f"O ficheiro '{file_path}' nao existe "
                "ou nao e acessivel"
            )

        with open(path, "r", encoding="utf-8") as file:
            lines = file.readlines()

        return cls.parse_lines(lines)

    @classmethod
    def parse_lines(cls, lines: list[str]) -> DroneNetwork:
        network: Optional[DroneNetwork] = None

        for line_idx, raw_line in enumerate(lines, start=1):
            clean_line = raw_line.split("#")[0].strip()
            if not clean_line:
                continue

            if network is None:
                network = cls._parse_nb_drones(clean_line, line_idx, raw_line)
                continue

            if clean_line.startswith("start_hub:"):
                zone = cls._parse_zone_line(
                    clean_line[10:], line_idx, raw_line, is_start=True)
                cls._safe_add_zone(network, zone, line_idx, raw_line)
            elif clean_line.startswith("end_hub:"):
                zone = cls._parse_zone_line(
                    clean_line[8:], line_idx, raw_line, is_end=True)
                cls._safe_add_zone(network, zone, line_idx, raw_line)
            elif clean_line.startswith("hub:"):
                zone = cls._parse_zone_line(
                    clean_line[4:], line_idx, raw_line)
                cls._safe_add_zone(network, zone, line_idx, raw_line)
            elif clean_line.startswith("connection:"):
                cls._parse_connection_line(
                    network, clean_line[11:], line_idx, raw_line)
            else:
                raise ParsingError(
                    line_idx,
                    raw_line,
                    "Diretiva desconhecida. Esperado: 'start_hub:', "
                    "end_hub:', 'hub:, ou 'connection:'."
                )

        if network is None:
            raise ParsingError(
                0,
                "",
                "O ficheiro de mapa esta vazio ou nao "
                "contem a linha 'nb_drones:'."
            )

        try:
            network.validate_topology()
        except MapValidationError as err:
            raise ParsingError(0, "", str(err)) from err
        return network

    @classmethod
    def _parse_nb_drones(
            cls, line: str, line_num: int, raw_line: str
            ) -> DroneNetwork:
        if not line.startswith("nb_drones:"):
            raise ParsingError(
                line_num,
                raw_line,
                "A primeira diretiva do mapa tem de "
                "ser 'nb_drones: <numero positivo>'."
            )

        value_part = line[10:].strip()
        try:
            nb_drones = int(value_part)
            if nb_drones <= 0:
                raise ValueError()
        except ValueError:
            raise ParsingError(
                line_num,
                raw_line,
                f"Numero de drones invalido ('{value_part}'). Deve "
                "ser um numero ESTRITAMENTE POSITIVO."
            )

        return DroneNetwork(nb_drones)

    @classmethod
    def _extract_metadata(
        cls, text: str, line_num: int, raw_line: str
    ) -> tuple[str, dict[str, str]]:
        start_bracket = text.find("[")
        if start_bracket == -1:
            return text.strip(), {}
        end_bracket = text.rfind("]")
        if end_bracket == -1 or end_bracket < start_bracket:
            raise ParsingError(
                line_num,
                raw_line,
                "Bloco de metadados mal formado. Falta fechar o "
                "parenteses reto correspondente."
            )

        main_part = text[:start_bracket].strip()
        metadata_content = text[start_bracket + 1:end_bracket].strip()
        metadata_dict: dict[str, str] = {}
        tokens = metadata_content.split()
        idx = 0
        while idx < len(tokens):
            token = tokens[idx]
            if "=" in token:
                key, val = token.split("=", 1)
                metadata_dict[key.strip()] = val.strip()
                idx += 1
            else:
                if idx + 1 < len(tokens) and "=" not in tokens[idx + 1]:
                    metadata_dict[token.strip()] = tokens[idx + 1].strip()
                    idx += 2
                else:
                    raise ParsingError(
                        line_num,
                        raw_line,
                        f"Metadado invalido/incompleto proximo de '{token}'."
                    )
        return main_part, metadata_dict

    @classmethod
    def _parse_zone_line(
        cls,
        content: str,
        line_num: int,
        raw_line: str,
        is_start: bool = False,
        is_end: bool = False
    ) -> Zone:
        main_part, metadata = cls._extract_metadata(
            content, line_num, raw_line)
        parts = main_part.split()

        if len(parts) != 3:
            raise ParsingError(
                line_num,
                raw_line,
                f"Definicao de zona invalida. Esperado: '<nome> <x> <y>', "
                f"obtido: '{main_part}'."
            )

        name, x_str, y_str = parts[0], parts[1], parts[2]

        if "-" in name:
            raise ParsingError(
                line_num,
                raw_line,
                f"O nome da zona '{name}' e invalido. "
                "Hifens sao estritamente proibidos em nomes de zonas."
            )

        try:
            x = int(x_str)
            y = int(y_str)
        except ValueError:
            raise ParsingError(
                line_num,
                raw_line,
                f"Coordenadas invalidas para a zona '{name}': "
                f"({x_str}, {y_str}). Devem ser numeros inteiros."
            )

        zone_type = ZoneType.NORMAL
        if "zone" in metadata:
            raw_type = metadata["zone"]
            try:
                zone_type = ZoneType(raw_type)
            except ValueError:
                raise ParsingError(
                    line_num,
                    raw_line,
                    f"Tipo de zona invalido: '{raw_type}'. "
                    "Permitidos: normal, blocked, restricted, priority."
                )

        max_drones: Optional[int] = 1
        if "max_drones" in metadata:
            try:
                parsed_max = int(metadata["max_drones"])
                if parsed_max <= 0:
                    raise ValueError()
                max_drones = parsed_max
            except ValueError:
                raise ParsingError(
                    line_num,
                    raw_line,
                    f"Valor de 'max_drones' invalido: "
                    f"'{metadata['max_drones']}'. Deve ser inteiro positivo."
                )

        color: Optional[str] = metadata.get("color")

        return Zone(
            name=name,
            x=x,
            y=y,
            zone_type=zone_type,
            max_drones=max_drones,
            color=color,
            is_start=is_start,
            is_end=is_end
        )

    @classmethod
    def _parse_connection_line(
        cls,
        network: DroneNetwork,
        content: str,
        line_num: int,
        raw_line: str
    ) -> None:
        main_part, metadata = cls._extract_metadata(
            content, line_num, raw_line)
        link_parts = main_part.split("-")

        if len(link_parts) != 2 or not link_parts[0] or not link_parts[1]:
            raise ParsingError(
                line_num,
                raw_line,
                f"Formato de ligacao invalido. Esperado: "
                f"'<zona1>-<zona2>', obtido: '{main_part}'"
            )

        name_a, name_b = link_parts[0].strip(), link_parts[1].strip()

        max_capacity = 1
        if "max_link_capacity" in metadata:
            try:
                parsed_cap = int(metadata["max_link_capacity"])
                if parsed_cap <= 0:
                    raise ValueError()
                max_capacity = parsed_cap
            except ValueError:
                raise ParsingError(
                    line_num,
                    raw_line,
                    f"'max_link_capacity' invalido: "
                    f"'{metadata['max_link_capacity']}'"
                )

        try:
            network.add_connection(name_a, name_b, max_capacity)
        except MapValidationError as err:
            raise ParsingError(line_num, raw_line, str(err)) from err

    @classmethod
    def _safe_add_zone(
        cls,
        network: DroneNetwork,
        zone: Zone,
        line_num: int,
        raw_line: str
    ) -> None:
        try:
            network.add_zone(zone)
        except MapValidationError as err:
            raise ParsingError(line_num, raw_line, str(err)) from err
