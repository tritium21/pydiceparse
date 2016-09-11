from __future__ import print_function
from collections import Counter
import heapq
import math
import operator
import random
import re


class Roller(object):
    def __init__(self, rollers):
        self.rollers = rollers

    def roll(self, instr):
        strings = instr.split()
        for string in strings:
            for roller in self.rollers:
                ma = roller.match(string)
                if ma:
                    yield ma

    def __call__(self, instr, who='You'):
        fmt = '{} rolled {}'
        return '\n'.join(fmt.format(who, str(x)) for x in self.roll(instr))


class DiceBase(object):
    expression = ''

    def __init__(self,  match):
        self._match = match
        self.result = None
        self.total = None
        self.roll()

    @classmethod
    def match(cls, instr):
        m = re.match(cls.expression, instr, re.X | re.I)
        if m is None:
            return
        return cls(m)

    def roll(self, match=None):
        raise NotImplementedError

    def __str__(self):
        raise NotImplementedError


class Select(DiceBase):
    expression = r'^(\d+)?\[(.*)\]$'

    def roll(self):
        match = self._match
        count, blob = match.groups()
        self.count = count = int(count) if count is not None else 1
        self.items = items = blob.split(',')
        if count < len(items):
            self.result = random.sample(items, count)
            self.total = count
        else:
            self.result = items
            self.total = len(items)

    def __str__(self):
        fmt = '{count} selection from [{items}]: {result}'
        oput = {
            'count': self.total,
            'items': ','.join(self.items),
            'result': ', '.join(self.result),
        }
        return fmt.format(**oput)


class Fate(DiceBase):
    expression = r'^(?P<count>\d+)df(?P<modifier>[+-]\d+)?$'

    def roll(self):
        match = self._match
        gd = match.groupdict()
        modifier = int(gd['modifier']) if gd['modifier'] is not None else 0
        count = int(gd['count'])
        self.result = [random.randint(-1, 1) for _ in range(count)]
        self.total = sum(self.result) + modifier

    def __str__(self):
        instr = self._match.string
        results = ', '.join({-1: '-', 0: '_', 1: '+'}[k] for k in self.result)
        total = self.total
        out = '[{instr}: {results}] {total}'
        return out.format(instr=instr, results=results, total=total)

class SR(DiceBase):
    expression = r"^(?P<count>\d+)sr(?P<explodes>!)?$"

    def roll(self):
        match = self._match
        count = int(match.groupdict()["count"])
        does_explode = True if match.groupdict()["explodes"] == "!" else False
        rolls = [random.randint(1, 6) for _ in range(count)]
        if does_explode:
            explode = len([x for x in rolls if x == 6])
            while explode:
                rerolls = [random.randint(1, 6) for _ in range(explode)]
                rolls.extend(rerolls)
                explode = len([x for x in rerolls if x == 6])
        successes = sum(1 for x in rolls if x >= 5)
        ones = sum(x for x in rolls if x == 1)
        self.outcome = ""
        if successes:
            if ones >= round(count/2):
                self.outcome = "Success, Glitch"
            else:
                self.outcome = "Success"
        elif not successes:
            if ones >= round(count/2):
                self.outcome = "Critical Glitch"
            else:
                self.outcome = "Failure"
        self.results = rolls
        self.total = successes

    def __str__(self):
        vals = {
            "instr": self._match.string,
            "rolls": self.results,
            "total": self.total,
            "outcome": self.outcome,
        }
        fmt = "[{instr}: {rolls}] {total} -- {outcome}"
        return fmt.format(**vals)

class Standard(DiceBase):
    expression = r'''^(?:(?P<best>\d+)(?P<bestop>[/\\]))?
                     (?P<count>\d+)d(?P<sides>\d+)
                     (?:(?P<poolop>[/\\])(?P<pool>\d+))?
                     (?:!(?P<explode>\d+))?
                     (?:(?P<modop>[+\-*])(?P<mod>\d+))?$'''

    _bestop = {'/': heapq.nlargest, '\\': heapq.nsmallest}
    _poolop = {'/': operator.ge, '\\': operator.le}
    _modop = {'+': operator.add, '-': operator.sub, '*': operator.mul}

    def __str__(self):
        instr = self._match.string
        results = ', '.join(str(x) for x in self.results)
        total = self.total
        out = '[{instr}: {results}] {total}'
        return out.format(instr=instr, results=results, total=total)

    def _explode(self, rolls, explode, sides):
            more = sum(1 for x in rolls if x >= explode)
            if more <= 0:
                return []
            more = [random.randint(1, sides) for _ in range(more)]
            return more + self._explode(more, explode, sides)

    def roll(self):
        match = self._match
        gd = match.groupdict()
        best = bestop = poolop = pool = explode = modop = mod = None
        count = int(gd['count'])
        sides = int(gd['sides'])
        rolls = [random.randint(1, sides) for _ in range(count)]
        if gd['explode']:
            explode = int(gd['explode'])
            rolls += self._explode(rolls, explode, sides)
        if gd['bestop']:
            bestop = self._bestop[gd['bestop']]
            best = int(gd['best'])
            rolls = bestop(best, rolls)
        if gd['poolop']:
            poolop = self._poolop[gd['poolop']]
            pool = int(gd['pool'])
            total = sum(1 for x in rolls if poolop(x, pool))
        else:
            total = sum(rolls)
        if gd['modop']:
            modop = self._modop[gd['modop']]
            mod = int(gd['mod'])
            total = modop(total, mod)
        self.results = rolls
        self.total = total


class EOTE(DiceBase):
    expression = r'^[bsadpcf]+$'
    _order = dict(
        success=0, failure=1, advantage=2, threat=3, triumph=4,
        dispair=5, light=6, dark=7,
    )

    Advantage = Counter(advantage=1)
    Blank = Counter()
    Dark = Counter(dark=1)
    Dispair = Counter(dispair=1)
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
        Threat + Threat, Dispair
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

    def roll(self):
        instr = self._match.string.lower()
        self.results = self._roll(
            boost=instr.count('b'),
            setback=instr.count('s'),
            ability=instr.count('a'),
            difficulty=instr.count('d'),
            proficiency=instr.count('p'),
            challenge=instr.count('c'),
            force=instr.count('f')
        )

    def _str_order(self, item):
        return self._order[item[0]]

    def _str_block(self, items):
        items = sorted(items, key=self._str_order)
        items = ['{} {}'.format(k.title(), v) for k, v in items]
        line = ', '.join(items)
        return line

    def __str__(self):
        instr = self._match.string
        items = self.results.items()
        line = self._str_block(items)
        return '[{}: {}]'.format(instr, line)


class EOTECancel(EOTE):
    def _roll(self, *args, **kwargs):
        res = super(EOTECancel, self)._roll(*args, **kwargs)
        self.grossresults = res
        res = Counter(res)
        return self._cancel(res)

    def __str__(self):
        instr = self._match.string
        netitems = self.results.items()
        grossitems = self.grossresults.items()

        gross = self._str_block(grossitems)
        net = self._str_block(netitems)

        return '[{}: {}] Outcome: {}'.format(instr, gross, net)

    def _cancel(self, results):
        results['success'] = (
            results.get('triumph', 0) + results.get('success', 0)
        )
        results['failure'] = (
            results.get('dispair', 0) + results.get('failure', 0)
        )
        self._compare(results, 'success', 'failure')
        self._compare(results, 'advantage', 'threat')
        results += self.Blank
        return results

    def _compare(self, results, a, b):
        av, bv = results.get(a, 0), results.get(b, 0)
        high, low = (a, b) if av >= bv else (b, a)
        value = abs(av-bv)
        results[high] = value
        results[low] = 0


roll = Roller([Standard, SR, Fate, EOTE, Select])


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
