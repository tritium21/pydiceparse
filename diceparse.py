from collections import namedtuple
from operator import add, sub, ge, le

from pyparsing import Literal, nums, NotAny, Optional, Or, Word, WordStart


def make_optional(parser, action, name):
    op = Optional(parser.setParseAction(action)(name), None)
    no = NotAny(parser)
    return op, no

# Data types
def integer_action(s, loc, tok):
    return int(tok[0])

integer = Word(nums).setParseAction(integer_action)

# Basic Dice Types
standard_type = integer('count') + Literal('d')('type') + integer('sides')
fate_type = integer('count') + Literal('df')('type') + NotAny(integer)


# Operator base
Operation = namedtuple('Operation', 'partial operator operand')

def operator_action(mapping):
    def closure(s, loc, tok):
        operator = tok[0]
        operand = tok[1]
        f = mapping[operator]

        def partial(first):
            return f(first, second)
        return Operation(partial, operator, operand)

# Modifiers
modifier_map = {'+': add, '-': sub}
modifier_action = operator_action(modifier_map)
modifier, _ = make_optional(
    Or(list(modifier_map.keys())) + integer, modifier_action, 'modifier'
)

# Comparators
compare_map = {'<': le, '>': ge}
compare_action = operator_action(compare_map)
compare, no_compare = make_optional(
    Or(list(compare_map.keys())) + integer, compare_action, 'compare'
)

suffix = modifier+compare

# Repetitions
def pos_action(pos):
    def action(s, lok, tok):
        return tok[pos]
    return action

repete, _ = make_optional(integer + Literal('#'), pos_action(0), 'repete')
reject, no_reject = make_optional(
    integer + Word(r'\/', max=1), pos_action(0), 'reject'
)
pool, no_pool = make_optional(Literal('/') + integer, pos_action(1), 'pool')
explode, no_explode = make_optional(
    Literal('!') + integer, pos_action(1), 'explode'
)
no_pool = no_pool + no_explode

standard = repete + reject + standard_type + no_pool + suffix
fate = repete + no_reject + fate_type + no_pool + modifier + no_compare
pool = repete + no_reject + standard_type + pool + explode + suffix

roll = WordStart() + Or([standard, pool, fate])

KEYS = 'count type sides modifier compare repete reject pool explode'.split()
PROTOTYPE = dict.fromkeys(KEYS)
RollSpec = namedtuple('RollSpec', ['rollstr'] + KEYS)


def validate(rollstr, result, prototype=None):
    prototype = prototype if prototype is not None else PROTOTYPE
    values = dict(prototype)
    values.update(dict(result))
    return RollSpec(rollstr, **values)


if __name__ == '__main__':
    import sys
    argv = ' '.join(sys.argv[1:])
    scanner = roll.scanString(argv)
    for res, start, end in scanner:
        st = argv[start:end]
        print(validate(st, res))
