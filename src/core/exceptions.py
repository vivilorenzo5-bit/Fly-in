class FlyinError (Exception):
    pass


class ParsingError(FlyinError):
    def __init__(self, line_number: int, raw_line: str, details: str) -> None:
        self.line_number: int = line_number
        self.raw_line: str = raw_line
        self.details: str = details
        message = (f"Erro de parsing na linha {line_number}: {details} "
                   f"-> '{raw_line}'")
        super().__init__(message)


class MapValidationError(FlyinError):
    pass


class SimulationError(FlyinError):
    pass
