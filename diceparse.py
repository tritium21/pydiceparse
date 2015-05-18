import collections
import operator
import random

import pyparsing as pp

OP_MAP = {
    '+': operator.add,
    '-': operator.sub,
    '*': operator.mul,
    '/': operator.truediv,
}
TARG_MAP = {
    '<': operator.le,
    '>': operator.ge,
}


OpTuple = collections.namedtuple('OpTuple', 'partial operator operand')
RollSpec = collections.namedtuple(
    'RollSpec',
    'input count sides modifier target'
)


def make_rollspecs(parser, instring):
    scanner = parser.scanString(instring)
    for res, start, end in scanner:
        st = instring[start:end]
        yield RollSpec(st, **res)


def int_action(s, loc, tok):
    return int(tok[0])


def mod_action(MAP):
    def inner(s, loc, tok):
        op = tok[0]
        op_func = MAP[op]
        second = tok[1]

        def partial(first):
            return op_func(first, second)
        return (OpTuple(partial, op, second),)
    return inner

# DATA TYPES
integer = pp.Word(pp.nums).setParseAction(int_action)

# MODIFIERS
mod_op = pp.Or(list(OP_MAP.keys()))
modifier = (mod_op + integer).setParseAction(mod_action(OP_MAP))
modifier = pp.Optional(modifier('modifier'), None)

# TARGET
targ_op = pp.Or(list(TARG_MAP.keys()))
target = (targ_op + integer).setParseAction(mod_action(TARG_MAP))
target = pp.Optional(target('target'), None)

# BASIC SYNTAX
basic = integer('count') + pp.Literal('d') + integer('sides')

# BTING IT ALL TOGETHER
roll = basic + modifier + target


def roller(rollspec):
    rolls = [random.randint(1, rollspec.sides) for _ in range(rollspec.count)]
    total = sum(rolls)
    success = None
    if rollspec.modifier:
        total = rollspec.modifier.partial(total)
    if rollspec.target:
        success = rollspec.target.partial(total)
    return rollspec, rolls, total, success


if __name__ == '__main__':
    import sys
    argv = ' '.join(sys.argv[1:])
    for spec in make_rollspecs(roll, argv):
        print(roller(spec))
