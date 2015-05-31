from collections import namedtuple
from heapq import nlargest, nsmallest
from functools import partial
from operator import add, sub, ge, le
from random import randint

from pyparsing import (
    CaselessLiteral as Literal,
    nums, NotAny, Optional, Or, Word, WordStart
)

Operation = namedtuple('Operation', 'partial operator operand')
KEYS = 'count type sides modifier compare repete reject pool explode'.split()
PROTOTYPE = dict.fromkeys(KEYS)
RollSpec = namedtuple('RollSpec', ['rollstr'] + KEYS)
ResultSpec = namedtuple('ResultSpec', 'rolls total success')
Result = namedtuple('Result', 'rollspec results total')

modifier_map = {'+': add, '-': sub}
compare_map = {'<': le, '>': ge}
reject_mapping = {'\\': nlargest, '/': nsmallest}
pool_map = {'/<': le, '/>': ge, '/': ge}
explode_map = {'!<': le, '!>': ge, '!': ge}


def make_optional(parser, action, name):
    op = Optional(parser.setParseAction(action)(name), None)
    no = NotAny(parser)
    return op, no


def integer_action(s, loc, tok):
    return int(tok[0])


def operator_action(mapping, swap=False):
    def closure(s, loc, tok):
        seq = tok[:2] if not swap else tok[:2][::-1]
        operator = seq[0]
        operand = second = seq[1]
        f = mapping[operator]

        if swap:
            fp = partial(f, second)
        else:
            def fp(first):
                return f(first, second)
        return (Operation(fp, operator, operand),)
    return closure


def mapped_option(mapping, name, swap=False):
    action = operator_action(mapping, swap=swap)
    return make_optional(
        Or(list(mapping.keys())) + integer, action, name
    )


def pos_action(pos):
    def action(s, lok, tok):
        return tok[pos]
    return action


reject_action = operator_action(reject_mapping, swap=True)

integer = Word(nums).setParseAction(integer_action)
standard_type = integer('count') + Literal('d')('type') + integer('sides')
fate_type = integer('count') + Literal('df')('type') + NotAny(integer)
modifier, _ = mapped_option(modifier_map, 'modifier')
compare, no_compare = mapped_option(compare_map, 'compare')
suffix = modifier+compare
repete, _ = make_optional(integer + Literal('#'), pos_action(0), 'repete')
reject, no_reject = make_optional(
    integer + Word(r'\/', max=1), reject_action, 'reject'
)
pool, no_pool = mapped_option(pool_map, 'pool')
explode, no_explode = mapped_option(explode_map, 'explode')
no_pool = no_pool + no_explode
standard = repete + reject + standard_type + no_pool + suffix
fate = repete + no_reject + fate_type + no_pool + modifier + no_compare
pool = repete + no_reject + standard_type + pool + explode + suffix
expression = WordStart() + Or([standard, pool, fate])


def validate(rollstr, result, prototype=None):
    prototype = prototype if prototype is not None else PROTOTYPE
    values = dict(prototype)
    values.update(dict(result))
    return RollSpec(rollstr, **values)


def fate_roller(rs):
    rolls = [randint(-1, 1) for _ in range(rs.count)]
    total = sum(rolls)
    if rs.modifier:
        total = rs.modifier.partial(total)
    success = total >= 1
    _str = {-1: "-", 0: " ", 1: "+"}
    rolls = [_str[d] for d in rolls]
    spec = ResultSpec(rolls, total, success)
    return spec


def explode(rolls, sides, trigger):
    newrolls = []
    _last = rolls
    while True:
        e = sum(trigger(d) for d in _last)
        if e:
            _last = [randint(1, sides) for _ in range(e)]
            newrolls.extend(_last)
            continue
        break
    return newrolls


def standard_roller(rs):
    rolls = [randint(1, rs.sides) for _ in range(rs.count)]
    success = None
    if rs.reject:
        rolls = rs.reject.partial(rolls)
    if rs.pool:
        op = rs.pool.partial
        if rs.explode:
            rolls.extend(explode(rolls, rs.sides, rs.explode.partial))
        total = sum(op(d) for d in rolls)
        success = total >= 1
    else:
        total = sum(rolls)
    if rs.modifier:
        total = rs.modifier.partial(total)
    if rs.compare:
        success = rs.compare.partial(total)
    return ResultSpec(rolls, total, success)


def roller(rs):
    typemap = {'df': fate_roller, 'd': standard_roller}
    repete = range(rs.repete if rs.repete is not None else 1)
    _results = []
    _total = 0
    for _ in repete:
        spec = typemap[rs.type](rs)
        _results.append(spec)
        _total += spec.total
    return Result(rs, _results, _total)


def roll_format(result, person='You'):
    _suc = {True: ' Success', False: ' Failure', None: ''}
    rollspec = result.rollspec
    rollstr = rollspec.rollstr
    total = result.total
    results = result.results
    if rollspec.modifier:
        mod = ' {}{}'.format(*rollspec.modifier[1:])
    else:
        mod = ''
    output = []
    roll_fmt = '{person} rolled {rollstr}: [{rolls}]{mod} = {total}{success}'
    total_fmt = 'Total: {total}'
    for res in results:
        rolls = ', '.join(str(x) for x in res.rolls)
        suc = _suc[res.success]
        s = roll_fmt.format(
            person=person, rollstr=rollstr.strip(), rolls=rolls,
            total=res.total, mod=mod, success=suc,
        )
        output.append(s)
    if len(results) > 1:
        output.append(total_fmt.format(total=total))
    return '\n'.join(output)


def roll(instr):
    scanner = expression.scanString(argv)

    def g():
        for res, start, end in scanner:
            st = argv[start:end]
            yield roll_format(roller(validate(st, res)))
    return list(g())


if __name__ == '__main__':
    import sys
    argv = ' '.join(sys.argv[1:])
    print(roll(argv))
