class ExtractionError(Exception):
    """Error de extracción seguro para mostrar al usuario."""

    def __init__(self, message: str, *, code: str = "EXTRACTION_ERROR") -> None:
        super().__init__(message)
        self.code = code
