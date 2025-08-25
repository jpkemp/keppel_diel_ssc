from abc import ABC, abstractmethod
from collections.abc import Iterable
import operator as op
import pandas as pd

class Range(ABC):
    @classmethod
    def format_range(cls, val, start, end):
        return f"{start} {cls.formatters[0]} {val} {cls.formatters[1]} {end}"

class EERange(Range):
    boundaries = "()"
    left = op.gt
    right = op.lt
    formatters = ("<", "<")

class IERange(Range):
    boundaries = "[)"
    left = op.ge
    right = op.lt
    formatters = ("<=", "<")

class IIRange(Range):
    boundaries = "[]"
    left = op.ge
    right = op.le
    formatters = ("<=", "<=")

class EIRange(Range):
    boundaries = "(]"
    left = op.gt
    right = op.le
    formatters = ("<", "<=")

OPERATORS = {
    ">=": op.ge,
    ">": op.gt,
    "<=": op.le,
    "<": op.lt,
    "==": op.eq,
    "!=": op.ne,
    "!": op.not_,
    "&": op.and_,
    "|": op.or_,
    "()": EERange,
    "[]": IIRange,
    "[)": IERange,
    "(]": EIRange
}

OPERATOR_FUNCS = {v: k for k, v in OPERATORS.items()}

def get_all_keys(d, level=0):
    for key, value in d.items():
        if isinstance(value, dict):
            yield from get_all_keys(value, level+1)
        else:
            yield value, level + 1

        yield key, level

def get_operator(operator):
    if callable(operator):
        op_str = OPERATOR_FUNCS[operator]
        op_func = operator
    else:
        op_str = operator
        op_func = OPERATORS[operator]

    return op_str, op_func

class Rule:
    def __init__(self, series, operator, value, end_value=None):
        op_str, op_func = get_operator(operator)
        if end_value is None:
            if isinstance(value, Iterable):
                raise ValueError("Iterable values can only be used with Range as the operator")

            self.mask = op_func(series, value)
            self.str = f"{series.name} {op_str} {value}"
        elif issubclass(op_func, Range):
            self.mask =  op_func.left(series, value) & op_func.right(series, end_value)
            self.str = op_func.format_range(series.name, value, end_value)
        else:
            raise ValueError("End values can only be used with Range as the operator")

    def __str__(self):
        return self.str

    def __repr__(self):
        return f"MaskRule: {self.str}"

class CombinedRules(Rule):
    def __init__(self, operator, *rules):
        op_str, op_func = get_operator(operator)
        base = rules[0].mask
        self.str = f"({rules[0].str})"
        for rule in rules[1:]:
            base = op_func(base, rule.mask)
            self.str += f" {op_str} ({rule.str})"

        self.mask = base

def build_mask(data:pd.DataFrame, faux_mask:dict):
    if not faux_mask:
        return pd.Series(True, index=data.index)

    blocks = {}
    current_level = -1
    for thing, level in get_all_keys(faux_mask):
        if isinstance(thing, str) or callable(thing):
            current_lower_block = blocks[current_level]
            if len(current_lower_block) == 1:
                combined = current_lower_block[0]
            else:
                combined = CombinedRules(thing, *current_lower_block)

            blocks[current_level] = []
            current_block = blocks.setdefault(level, [])
            current_block.append(combined)
            current_level = level
        else:
            current_level = level
            current_lower_block = blocks.setdefault(level, [])
            for rule in thing:
                series = rule[0]
                if isinstance(series, str):
                    series = data[series]

                created_rule = Rule(series, *rule[1:])
                current_lower_block.append(created_rule)

    assert len(blocks[0]) == 1
    return blocks[0][0]
