class InsufficientSpotsError(Exception):
    def __init__(self, available: int):
        self.available = available
        super().__init__(f"Недостаточно мест. Доступно: {available}.")