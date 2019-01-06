import operator
from random import SystemRandom

from lark import Lark, Transformer, v_args

random = SystemRandom()


#class EOTE(DiceBase):
#    expression = r'^[bsadpcf]+$'
#    _order = dict(
#        success=0, failure=1, advantage=2, threat=3, triumph=4,
#        dispair=5, light=6, dark=7,
#    )

#    Advantage = Counter(advantage=1)
#    Blank = Counter()
#    Dark = Counter(dark=1)
#    Dispair = Counter(dispair=1)
#    Failure = Counter(failure=1)
#    Light = Counter(light=1)
#    Success = Counter(success=1)
#    Threat = Counter(threat=1)
#    Triumph = Counter(triumph=1)

#    Difficulty = (
#        Blank, Failure, Failure + Failure, Threat, Threat,
#        Threat, Threat + Threat, Threat + Failure,
#    )
#    Ability = (
#        Blank, Success, Success, Success + Success, Advantage,
#        Advantage, Advantage + Success, Advantage + Advantage
#    )
#    Boost = (
#        Blank, Blank, Advantage + Advantage, Advantage,
#        Success + Advantage, Success
#    )
#    Setback = (
#        Blank, Blank, Failure, Failure, Threat, Threat
#    )
#    Proficiency = (
#        Blank, Success, Success, Success + Success, Success + Success,
#        Advantage, Success + Advantage, Success + Advantage,
#        Success + Advantage, Advantage + Advantage, Advantage + Advantage,
#        Triumph
#    )
#    Challenge = (
#        Blank, Failure, Failure, Failure + Failure, Failure + Failure, Threat,
#        Threat, Failure + Threat, Failure + Threat, Threat + Threat,
#        Threat + Threat, Dispair
#    )
#    Force = (
#        Dark, Dark, Dark, Dark, Dark, Dark, Dark + Dark,
#        Light, Light, Light + Light, Light + Light, Light + Light
#    )

#    def _roll(
#        self,
#        boost=0,
#        setback=0,
#        ability=0,
#        difficulty=0,
#        proficiency=0,
#        challenge=0,
#        force=0
#    ):
#        boost = sum(
#            (random.choice(self.Boost) for _ in range(boost)),
#            self.Blank,
#        )
#        setback = sum(
#            (random.choice(self.Setback) for _ in range(setback)),
#            self.Blank,
#        )
#        ability = sum(
#            (random.choice(self.Ability) for _ in range(ability)),
#            self.Blank,
#        )
#        difficulty = sum(
#            (random.choice(self.Difficulty) for _ in range(difficulty)),
#            self.Blank,
#        )
#        proficiency = sum(
#            (random.choice(self.Proficiency) for _ in range(proficiency)),
#            self.Blank,
#        )
#        challenge = sum(
#            (random.choice(self.Challenge) for _ in range(challenge)),
#            self.Blank,
#        )
#        force = sum(
#            (random.choice(self.Force) for _ in range(force)),
#            self.Blank
#        )
#        result = (
#            boost + setback + ability + difficulty
#            + proficiency + challenge + force
#        )
#        return {k: v for k, v in result.items() if v > 0}

#    def roll(self):
#        instr = self._match.string.lower()
#        self.results = self._roll(
#            boost=instr.count('b'),
#            setback=instr.count('s'),
#            ability=instr.count('a'),
#            difficulty=instr.count('d'),
#            proficiency=instr.count('p'),
#            challenge=instr.count('c'),
#            force=instr.count('f')
#        )

#    def _str_order(self, item):
#        return self._order[item[0]]

#    def _str_block(self, items):
#        items = sorted(items, key=self._str_order)
#        items = ['{} {}'.format(k.title(), v) for k, v in items]
#        line = ', '.join(items)
#        return line

#    def __str__(self):
#        instr = self._match.string
#        items = self.results.items()
#        line = self._str_block(items)
#        return '[{}: {}]'.format(instr, line)

GRAMMAR = """\
?start: sum [comment]  -> start
?sum: product
    | sum "+" product   -> add
    | sum "-" product   -> sub
?product: atom
    | product "*" atom  -> mul
    | product "/" atom  -> div
?atom: number
    | "-" atom          -> neg
    | dice_atom
    | "(" sum ")"

?dice_atom: pool_atom | fate_atom
?pool_atom: standard_atom
    | standard_atom "<=" number -> poolle
    | standard_atom ">=" number -> poolge
    | standard_atom "<" number  -> poollt
    | standard_atom ">" number  -> poolgt
?standard_atom: number "d"i number -> standard
?fate_atom: number "df"i -> fate

?number: INT -> number

?comment: "#" /[^\\n]+/* -> comment

%import common.INT
%import common.WS_INLINE
%ignore WS_INLINE
"""

OP_MAP = {
    operator.add: '+',
    operator.sub: '-',
    operator.mul: '*',
    operator.floordiv: '/',
    operator.ge: '>=',
    operator.gt: '>',
    operator.le: '<=',
    operator.lt: '<',
}

class BaseRoll:
    def __init__(self, left, operator, right):
        self.left = left
        self.right = right
        self.operator = operator
        left = int(left)
        right = int(right)
        self.total = self.operator(left, right)

    def __int__(self):
        return self.total

    def __repr__(self):
        return (
            "{self.__class__.__qualname__}"
            "({self.left}, {self.operator}, {self.right})"
        ).format(self=self)

    def __str__(self):
        return "{} {} {}".format(self.left, OP_MAP[self.operator], self.right)

    def _binop(self, other, op):
       return BaseRoll(self, op, other)

    __radd__ = __add__ = lambda s, o: s._binop(o, operator.add)
    __rsub__ = __sub__ = lambda s, o: s._binop(o, operator.sub)
    __rmul__ = __mul__ = lambda s, o: s._binop(o, operator.mul)
    __rfloordiv__ = __floordiv__ = lambda s, o: s._binop(o, operator.floordiv)

class FateRoll(BaseRoll):
    def __init__(self, count):
        self.count = count
        self.results = [random.randint(-1, 1) for _ in range(self.count)]
        self.total = sum(x for x in self.results if x > 0)

    def __repr__(self):
        return "{self.__class__.__qualname__}({self.count})".format(self=self)

    def __str__(self):
        res = ','.join(str(x) for x in self.results)
        return "({count}df = [{results}] = {total})".format(count=self.count, results=res, total=self.total)

class StandardRoll(BaseRoll):
    def __init__(self, count, sides, operator=None, compare=None):
        self.count = count
        self.sides = sides
        self.operator = None
        self.compare = None
        self.results = [random.randint(1, sides) for _ in range(count)]
        self.total = sum(self.results)
        if compare and operator:
            self.pool(operator, compare)

    def pool(self, operator, compare):
        if not self.compare or self.operator:
            self.operator = operator
            self.compare = compare
        self.total = sum(1 for x in self.results if operator(x, compare))

    def __repr__(self):
        return (
            "{self.__class__.__qualname__}"
            "({self.count}, {self.sides}, {self.operator}, {self.compare})"
        ).format(self=self)

    def __str__(self):
        op = ""
        if self.operator:
            op = OP_MAP[self.operator] + str(self.compare)
        dicespec = "{}d{}{}".format(self.sides, self.count, op)
        results = ','.join(str(x) for x in self.results)
        return "({} = [{}] = {})".format(dicespec, results, self.total)

class CommandResult:
    def __init__(self, roll, comment=None):
        self.roll = roll
        self.total = int(roll)
        self.comment = (" # " + comment) if comment is not None else ""

    def __repr__(self):
        return "{self.__class__.__qualname__}({self.rolls}, {self.comment!r})".format(self=self)

    def __str__(self):
        return "{} = {}{}".format(self.roll, self.total, self.comment)


@v_args(inline=True)
class CalculateTree(Transformer):
    from operator import add, sub, mul, floordiv as div, neg
    number = int

    def start(self, roll, comment=None):
        return CommandResult(roll, comment)

    def comment(self, args):
        return str(args).strip()

    def fate(self, count):
        return FateRoll(count)

    def standard(self, count, sides):
        return StandardRoll(count, sides)

    def _pool(self, roll, comp, op):
        roll.pool(op, comp)
        return roll
    
    poolge = lambda s, r, c: s._pool(r, c, operator.ge)
    poolgt = lambda s, r, c: s._pool(r, c, operator.gt)
    poolle = lambda s, r, c: s._pool(r, c, operator.le)
    poollt = lambda s, r, c: s._pool(r, c, operator.lt)


parser = Lark(GRAMMAR, start='start')

def roll(spec, who=None):
    tree = parser.parse(spec)
    return CalculateTree().transform(tree)


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--who', '-w',
        default='You',
        metavar='NAME',
        help="Who is this roll for (string formatting test)",
    )
    parser.add_argument('rolls', nargs='+')
    args = parser.parse_args(args=argv)
    print(roll(' '.join(args.rolls), args.who))

if __name__ == '__main__':
    main()
