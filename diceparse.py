import collections
import collections.abc
import functools
import heapq
import math
import operator
import random as _random

import lark
import lark.exceptions

random = _random.SystemRandom()


def truediv(left, right):
    "Integer division, ceil."
    return int(math.ceil(left / right))

OP_MAP = {
    operator.add: '+',
    operator.sub: '-',
    operator.mul: '*',
    operator.floordiv: '//',
    truediv: '/',
    operator.ge: '>=',
    operator.gt: '>',
    operator.le: '<=',
    operator.lt: '<',
    heapq.nlargest: '!',
    heapq.nsmallest: '!!',
}

def eote(instr):
    instr = instr.lower()
    _order = dict(
        success=0, failure=1, advantage=2, threat=3, triumph=4,
        despair=5, light=6, dark=7,
    )

    Ad = collections.Counter(advantage=1)
    Ad2 = collections.Counter(advantage=2)
    Bl = collections.Counter()
    Da = collections.Counter(dark=1)
    Da2 = collections.Counter(dark=2)
    De = collections.Counter(despair=1)
    Fa = collections.Counter(failure=1)
    Fa2 = collections.Counter(failure=2)
    Li = collections.Counter(light=1)
    Li2 = collections.Counter(light=2)
    Su = collections.Counter(success=1)
    Su2 = collections.Counter(success=2)
    SuAd = Su + Ad
    Th = collections.Counter(threat=1)
    Th2 = collections.Counter(threat=2)
    ThFa = Th + Fa
    Tr = collections.Counter(triumph=1)

    def _sum(population, weights, count):
        return sum(random.choices(population, weights, k=count), Bl)

    boost = _sum([Bl, Ad2, Ad, SuAd, Su], [2, 1, 1, 1, 1], instr.count('b'))
    setback = _sum([Bl, Fa, Th], [2, 2, 2], instr.count('s'))
    ability = _sum([Bl, Su, Su2, Ad, SuAd, Ad2], [1, 2, 1, 2, 1, 1], instr.count('a'))
    difficulty = _sum([Bl, Fa, Fa2, Th, Th2, ThFa], [1, 1, 1, 3, 1, 1], instr.count('d'))
    proficiency = _sum([Bl, Su, Su2, Ad, SuAd, Ad2, Tr], [1, 2, 2, 1, 3, 2, 1], instr.count('p'))
    challenge = _sum([Bl, Fa, Fa2, Th, ThFa, Th2, De], [1, 2, 2, 2, 2, 2, 1], instr.count('c'))
    force = _sum([Da, Da2, Li, Li2], [6, 1, 2, 3], instr.count('f'))

    result = (boost + setback + ability + difficulty + proficiency + challenge + force)
    result = ((k, v) for k, v in sorted(result.items(), key=lambda x: _order[x[0]]) if v > 0)

    line = ', '.join("{} {}".format(k.title(), v) for k, v in result)
    return "{} = {}".format(instr, line)

@functools.total_ordering
class BaseRoll:
    def __index__(self):
        return self.total

    def __int__(self):
        return self.total

    def __eq__(self, value):
        return self.total == value

    def __lt__(self, value):
        return self.total < value


    def _binop(self, other, op):
       return Math(self, op, other)

    __radd__ = __add__ = lambda s, o: s._binop(o, operator.add)
    __rsub__ = __sub__ = lambda s, o: s._binop(o, operator.sub)
    __rmul__ = __mul__ = lambda s, o: s._binop(o, operator.mul)
    __rfloordiv__ = __floordiv__ = lambda s, o: s._binop(o, operator.floordiv)
    __rtruediv__ = __truediv__ = lambda s, o: s._binop(o, truediv)

class Math(BaseRoll):
    def __init__(self, left, operator, right):
        self.left = left
        self.right = right
        self.operator = operator
        left = int(left)
        right = int(right)
        self.total = self.operator(left, right)

    def __repr__(self):
        return (
            "{self.__class__.__qualname__}"
            "({self.left!r}, {self.operator!r}, {self.right!r})"
        ).format(self=self)

    def __str__(self):
        return "{} {} {}".format(self.left, OP_MAP[self.operator], self.right)


class Number(BaseRoll):
    def __init__(self, num):
        self.total = int(num)

    def __repr__(self):
        return (
            "{self.__class__.__qualname__}"
            "({self.total})"
        ).format(self=self)

    def __str__(self):
        return str(self.total)


class FateRoll(BaseRoll):
    def __init__(self, count):
        self.count = count
        self.results = [random.randint(-1, 1) for _ in range(self.count)]
        self.total = sum(x for x in self.results)

    def __repr__(self):
        return "{self.__class__.__qualname__}({self.count})".format(self=self)

    def __str__(self):
        fatemap = {-1: '[-]', 0: '[ ]', 1:'[+]'}
        res = ','.join(fatemap[x] for x in self.results)
        return "({count}df = [{results}] = {total})".format(count=self.count, results=res, total=self.total)

class StandardRoll(BaseRoll):
    def __init__(self, count, sides, best_operator=None, best_compare=None, operator=None, compare=None, explode_operator=None, explode_compare=None):
        self.count = count
        self.sides = sides
        self.operator = None
        self.compare = None
        self.best_operator = None
        self.best_compare = None
        self.explode_operator = None
        self.explode_compare = None
        self.results = self._results = [random.randint(1, self.sides) for _ in range(self.count)]
        self.total = sum(self._results)
        if explode_compare and explode_operator:
            self.explode(explode_operator, explode_compare)        
        if best_compare and best_operator:
            self.best(best_operator, best_compare)
        if compare and operator:
            self.pool(operator, compare)

    def roll_again(self):
        return type(self)(
            self.count,
            self.sides,
            self.best_operator,
            self.best_compare,
            self.operator,
            self.compare,
            self.explode_operator,
            self.explode_compare,
        )

    def best(self, operator, compare):
        if not self.best_compare or self.best_operator:
            self.best_operator = operator
            self.best_compare = compare
        self._results = self.best_operator(self.best_compare, self.results)
        self.total = sum(self._results)

    def pool(self, operator, compare):
        if not self.compare or self.operator:
            self.operator = operator
            self.compare = compare
        inpool = [r for r in self._results if operator(r, compare)]
        self.total = sum(1 for x in inpool)

    def explode(self, operator, compare):
        if not self.explode_operator or self.explode_compare:
            self.explode_operator = operator
            self.explode_compare = compare
        def _explode_check(r_set):
            return sum(1 for r in r_set if self.explode_operator(r, self.explode_compare))
        new_rolls = _explode_check(self._results)
        while new_rolls > 0:
            new_res = [random.randint(1, self.sides) for _ in range(new_rolls)]
            new_rolls = _explode_check(new_res)
            self._results += new_res
        self.results = self._results
        self.total = sum(self._results)

    def __repr__(self):
        args_i = (
            ('count', repr(self.count)),
            ('sides', repr(self.sides)),
            ('best_operator', repr(self.best_operator)),
            ('best_compare', repr(self.best_compare)),
            ('operator', repr(self.operator)),
            ('compare', repr(self.compare)),
        )
        args = ', '.join("{}={}".format(*x) for x in args_i)
        return (
            "{self.__class__.__qualname__}"
            "({args})"
        ).format(self=self, args=args)

    def __str__(self):
        best = ""
        if self.best_operator:
            best = str(self.best_compare) + OP_MAP[self.best_operator]
        op = ""
        explode = ""
        if self.explode_operator:
            explode = "x{}".format(self.explode_compare)
        if self.operator:
            op = OP_MAP[self.operator] + str(self.compare)
        dicespec = "{}{}d{}{}{}".format(best, self.count, self.sides, explode, op)
        results = ','.join(str(x) for x in self.results)
        return "({} = [{}] = {})".format(dicespec, results, self.total)

@lark.v_args(inline=True)
class CalculateTree(lark.Transformer):
    from operator import add, sub, mul, truediv, floordiv, neg
    number = Number


    def start(self, *items):
        for item in items:
            yield from item

    def item(self, rolls, comment=None):
        comment = (" # " + comment) if comment is not None else ""
        if not isinstance(rolls, collections.abc.Iterable):
            rolls = [rolls]
        for roll in rolls:
            if isinstance(roll, Math):
                yield "{} = {}{}".format(roll, int(roll), comment)
                continue
            yield "{}{}".format(str(roll).strip("()"), comment)

    def eote(self, args):
        return (eote(args),)

    def comment(self, args):
        return str(args).strip()

    def fate(self, count):
        return FateRoll(int(count))

    def repeat(self, count, roll):
        for _ in range(count):
            yield roll.roll_again()

    def standard(self, count, sides):
        return StandardRoll(int(count), int(sides))

    def _pool(self, roll, comp, op):
        roll.pool(op, int(comp))
        return roll
    
    def _explode(self, roll, comp, op):
        roll.explode(op, int(comp))
        return roll

    def _best(self, roll, comp, op):
        roll.best(op, int(comp))
        return roll

    besttop = lambda s, c, r: s._best(r, c, heapq.nlargest)
    bestbot = lambda s, c, r: s._best(r, c, heapq.nsmallest)
    poolge = lambda s, r, c: s._pool(r, c, operator.ge)
    poolgt = lambda s, r, c: s._pool(r, c, operator.gt)
    poolle = lambda s, r, c: s._pool(r, c, operator.le)
    poollt = lambda s, r, c: s._pool(r, c, operator.lt)
    explodeover = lambda s, r, c: s._explode(r, c, operator.ge)

GRAMMAR = """\
?start: item ("|" item)* -> start
?item: oper [comment]  -> item
?oper: sum | eote_atom

?eote_atom: /[bsadpcf]+/i -> eote

?sum: product
    | sum "+" product   -> add
    | sum "-" product   -> sub
?product: atom
    | product "*" atom  -> mul
    | product "//" atom  -> floordiv
    | product "/" atom  -> truediv
?atom: number
    | "-" atom          -> neg
    | dice_atom
    | "(" sum ")"

?dice_atom: standard | fate_atom

?standard: standard_atom
    | number "#" standard_atom -> repeat

?standard_atom: best_atom
    | best_atom "<=" number -> poolle
    | best_atom ">=" number -> poolge
    | best_atom "<" number  -> poollt
    | best_atom ">" number  -> poolgt
?best_atom: explode_atom
    | number "!" explode_atom -> besttop
    | number "!!" explode_atom -> bestbot
?explode_atom: base_atom
    | base_atom "x" number -> explodeover
?base_atom: number "d"i number -> standard

?fate_atom: number "df"i -> fate

?number: INT -> number

?comment: " " /[^\\n|]+/* -> comment

%import common.INT
%import common.WS_INLINE
%ignore WS_INLINE
"""

parser = lark.Lark(GRAMMAR, start='start')

def rolls(spec, who='You'):
    try:
        tree = parser.parse(spec)
        res = CalculateTree().transform(tree)
        for line in res:
            yield "{} rolled: {}".format(who, line)
    except (ArithmeticError, lark.exceptions.LarkError) as e:
        return

def roll(spec, who='You'):
    res = list(rolls(spec, who))
    return '\n'.join(res)

def main(argv=None):
    import argparse
    import getpass
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--who', '-w',
        default=getpass.getuser(),
        metavar='NAME',
        help="Who is this roll for (string formatting test)",
    )
    parser.add_argument('rolls', nargs='+')
    args = parser.parse_args(args=argv)
    r = roll(' '.join(args.rolls), args.who)
    if r:
        print(r)
        return
    return "Invalid roll"

if __name__ == '__main__':
    import sys
    sys.exit(main())
