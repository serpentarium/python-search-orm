class _NoValue:
    """
    To check when value is explicitly None or False
    """
    @staticmethod
    def __bool__():
        return False

    @staticmethod
    def __repr__():
        return "NoValue"


NoValue = _NoValue()


class Operator:
    """Constants to define join operators."""
    AND = 'AND'
    OR = 'OR'
    XOR = 'XOR'


class Condition:
    """Constants to define condition operators"""
    LT = 'lt'
    LE = 'le'
    EQ = 'eq'
    NE = 'ne'
    GT = 'gt'
    GE = 'ge'
    IN = 'in'
    RANGE = 'range'


RANGE_CONDITIONS = [
    Condition.LT,
    Condition.LE,
    Condition.GT,
    Condition.GE,
]
