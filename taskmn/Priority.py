from enum import Enum


class Priority(Enum):
    """
    An Enum class that represents the priority of an object. It supports comparison with itself.
    """
    LOW = 0
    NORMAL = 1
    HIGH = 2

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented

    def __gt__(self, other):
        if self.__class__ is other.__class__:
            return self.value > other.value
        return NotImplemented

    def __eq__(self, other):
        if self.__class__ is other.__class__:
            return self.value == other.value
        return NotImplemented

    def __le__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value or self.value == other.value
        return NotImplemented

    def __ge__(self, other):
        if self.__class__ is other.__class__:
            return self.value > other.value or self.value == other.value
        return NotImplemented
