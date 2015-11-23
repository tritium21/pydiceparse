from __future__ import print_function
from collections import Counter as _counter
from random import choice


class Counter(_counter):
    def __add__(self, other):
        if not isinstance(other, _counter):
            return NotImplemented
        result = Counter()
        for elem, count in self.items():
            result[elem] = count + other[elem]
        for elem, count in other.items():
            if elem not in self:
                result[elem] = count
        return result

_order = dict(
    success=0, failure=1, advantage=2, threat=3, triumph=4,
    dispair=5, light=6, dark=7,
)


def order(item):
    return _order[item[0]]

# Advantage = Counter(advantage=1, threat=-1)
Advantage = Counter(advantage=1)
Blank = Counter()
Dark = Counter(dark=1)
# Dispair = Counter(dispair=1, success=-1)
# Failure = Counter(failure=1, success=-1)
Dispair = Counter(dispair=1)
Failure = Counter(failure=1)
Light = Counter(light=1)
Success = Counter(success=1)
# Threat = Counter(threat=1, advantage=-1)
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
    Blank, Success, Success, Success + Success, Success + Success, Advantage,
    Success + Advantage, Success + Advantage, Success + Advantage,
    Advantage + Advantage, Advantage + Advantage, Triumph
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


def roll(
    boost=0,
    setback=0,
    ability=0,
    difficulty=0,
    proficiency=0,
    challenge=0,
    force=0
):
    boost = sum((choice(Boost) for _ in range(boost)), Blank)
    setback = sum((choice(Setback) for _ in range(setback)), Blank)
    ability = sum((choice(Ability) for _ in range(ability)), Blank)
    difficulty = sum((choice(Difficulty) for _ in range(difficulty)), Blank)
    proficiency = sum((choice(Proficiency) for _ in range(proficiency)), Blank)
    challenge = sum((choice(Challenge) for _ in range(challenge)), Blank)
    force = sum((choice(Force) for _ in range(force)), Blank)
    result = (
        boost + setback + ability + difficulty
        + proficiency + challenge + force
    )
    return {k: v for k, v in result.items() if v > 0}


def parse(instr):
    return roll(
        boost=instr.count('b'),
        setback=instr.count('s'),
        ability=instr.count('a'),
        difficulty=instr.count('d'),
        proficiency=instr.count('p'),
        challenge=instr.count('c'),
        force=instr.count('f')
    )


def eoteformat(instr, person='You'):
    instr = instr.lower()
    r = parse(instr)
    items = r.items()
    items = sorted(items, key=order)
    items = ['{} {}'.format(k.title(), v) for k, v in items]
    line = ', '.join(items)
    return '{} rolled {}: {}'.format(person, instr, line)

if __name__ == '__main__':
    print(eoteformat('paabsdd'))
