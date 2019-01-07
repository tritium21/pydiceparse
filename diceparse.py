from collections import Counter
import operator
import heapq
from random import SystemRandom
from functools import total_ordering
import math

from lark import Lark, Transformer, v_args
from lark.exceptions import LarkError

random = SystemRandom()

GRAMMAR = """\
?start: oper [comment]  -> start
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

?dice_atom: standard_atom | fate_atom

?standard_atom: best_atom
    | best_atom "<=" number -> poolle
    | best_atom ">=" number -> poolge
    | best_atom "<" number  -> poollt
    | best_atom ">" number  -> poolgt
?best_atom: base_atom
    | number "!" base_atom -> besttop
    | number "!!" base_atom -> bestbot
?base_atom: number "d"i number -> standard

?fate_atom: number "df"i -> fate

?number: INT -> number

?comment: " " /[^\\n]+/* -> comment

%import common.INT
%import common.WS_INLINE
%ignore WS_INLINE
"""

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

class EOTE:
    _order = dict(
        success=0, failure=1, advantage=2, threat=3, triumph=4,
        despair=5, light=6, dark=7,
    )

    Advantage = Counter(advantage=1)
    Blank = Counter()
    Dark = Counter(dark=1)
    Despair = Counter(despair=1)
    Failure = Counter(failure=1)
    Light = Counter(light=1)
    Success = Counter(success=1)
    Threat = Counter(threat=1)
    Triumph = Counter(triumph=1)

    Difficulty = (
        Blank, Failure, Failure + Failure, Threat, Threat,
        Threat, Threat + Threat, Threat + Failure,
    )
    Ability = (
        Blank, Success, Success, Success + Success, Advantage,
        Advantage, Advantage + Success, Advantage + Advantage
    )
    Boost = (
        Blank, Blank, Advantage + Advantage, Advantage,
        Success + Advantage, Success
    )
    Setback = (
        Blank, Blank, Failure, Failure, Threat, Threat
    )
    Proficiency = (
        Blank, Success, Success, Success + Success, Success + Success,
        Advantage, Success + Advantage, Success + Advantage,
        Success + Advantage, Advantage + Advantage, Advantage + Advantage,
        Triumph
    )
    Challenge = (
        Blank, Failure, Failure, Failure + Failure, Failure + Failure, Threat,
        Threat, Failure + Threat, Failure + Threat, Threat + Threat,
        Threat + Threat, Despair
    )
    Force = (
        Dark, Dark, Dark, Dark, Dark, Dark, Dark + Dark,
        Light, Light, Light + Light, Light + Light, Light + Light
    )

    def _roll(
        self,
        boost=0,
        setback=0,
        ability=0,
        difficulty=0,
        proficiency=0,
        challenge=0,
        force=0
    ):
        boost = sum(
            (random.choice(self.Boost) for _ in range(boost)),
            self.Blank,
        )
        setback = sum(
            (random.choice(self.Setback) for _ in range(setback)),
            self.Blank,
        )
        ability = sum(
            (random.choice(self.Ability) for _ in range(ability)),
            self.Blank,
        )
        difficulty = sum(
            (random.choice(self.Difficulty) for _ in range(difficulty)),
            self.Blank,
        )
        proficiency = sum(
            (random.choice(self.Proficiency) for _ in range(proficiency)),
            self.Blank,
        )
        challenge = sum(
            (random.choice(self.Challenge) for _ in range(challenge)),
            self.Blank,
        )
        force = sum(
            (random.choice(self.Force) for _ in range(force)),
            self.Blank
        )
        result = (
            boost + setback + ability + difficulty
            + proficiency + challenge + force
        )
        return {k: v for k, v in result.items() if v > 0}

    def __init__(self, instr):
        self.input = instr = instr.lower()
        self.results = self._roll(
            boost=instr.count('b'),
            setback=instr.count('s'),
            ability=instr.count('a'),
            difficulty=instr.count('d'),
            proficiency=instr.count('p'),
            challenge=instr.count('c'),
            force=instr.count('f')
        )

    def _str_block(self, items):
        items = sorted(items, key=lambda x:self._order[x[0]])
        items = ['{} {}'.format(k.title(), v) for k, v in items]
        line = ', '.join(items)
        return line

    def __str__(self):
        instr = self.input
        items = self.results.items()
        line = self._str_block(items)
        return '{} = {}'.format(instr, line)


@total_ordering
class BaseRoll:
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
        self.total = sum(x for x in self.results if x > 0)

    def __repr__(self):
        return "{self.__class__.__qualname__}({self.count})".format(self=self)

    def __str__(self):
        fatemap = {-1: '-', 0: '_', 1:'+'}
        res = ','.join(fatemap[x] for x in self.results)
        return "({count}df = [{results}] = {total})".format(count=self.count, results=res, total=self.total)

class StandardRoll(BaseRoll):
    def __init__(self, count, sides, best_operator=None, best_compare=None, operator=None, compare=None):
        self.count = count
        self.sides = sides
        self.operator = None
        self.compare = None
        self.best_operator = None
        self.best_compare = None
        self.results = self._results = [random.randint(1, self.sides) for _ in range(self.count)]
        self.total = sum(self._results)
        if best_compare and best_operator:
            self.best(best_operator, best_compare)
        if compare and operator:
            self.pool(operator, compare)

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
        if self.operator:
            op = OP_MAP[self.operator] + str(self.compare)
        dicespec = "{}{}d{}{}".format(best, self.count, self.sides, op)
        results = ','.join(str(x) for x in self.results)
        return "({} = [{}] = {})".format(dicespec, results, self.total)

@v_args(inline=True)
class CalculateTree(Transformer):
    from operator import add, sub, mul, truediv, floordiv, neg
    number = Number

    def start(self, roll, comment=None):
        comment = (" # " + comment) if comment is not None else ""
        if isinstance(roll, Math):
            return "{} = {}{}".format(roll, int(roll), comment)
        return "{}{}".format(str(roll).strip("()"), comment)

    def eote(self, args):
        return EOTE(args)

    def comment(self, args):
        return str(args).strip()

    def fate(self, count):
        return FateRoll(int(count))

    def standard(self, count, sides):
        return StandardRoll(int(count), int(sides))

    def _pool(self, roll, comp, op):
        roll.pool(op, int(comp))
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

parser = Lark(GRAMMAR, start='start')

def roll(spec, who='You'):
    try:
        tree = parser.parse(spec)
        res = CalculateTree().transform(tree)
        return "{} rolled: {}".format(who, res)
    except (ArithmeticError, LarkError) as e:
        return


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
