class CT:
    def __init__(self, name, value) -> None:
        self._name = name
        self._value = value

    @property
    def name(self):
        """Name of CT clamp"""
        return self._name

    @property
    def power(self):
        """Power reading of CT clamp in W"""
        return self._value
