class FilterStore:
    def __init__(self):
        self._filters = []

    def save(self, name: str) -> None:
        self._filters.append(name)

    def all(self) -> list[str]:
        return list(self._filters)
