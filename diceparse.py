import pyparsing as pp
assert pp
from pyparsing import nums, Word, Optional, Each


integer = Word(nums)

modifier = Word('+-*/', max=1) + integer
target = Word('<>', max=1) + integer
suffix = Each([
    Optional(modifier('modifier'), None),
    Optional(target('target'), None),
])
repete = Optional((integer + '#')('repete'), None)

pool = '!' + integer('pool')
reject = integer('reject') + Word(r'\/', max=1)

basic = integer('count') + 'd' + integer('sides')

with_pool = repete + basic + pool + suffix
with_reject = repete + reject + basic + suffix
standard = repete + basic + suffix
roll = with_pool ^ with_reject ^ standard

if __name__ == '__main__':
    import sys
    argv = ' '.join(sys.argv[1:])
    scanner = standard.scanString(argv)
    for res, start, end in scanner:
        st = argv[start:end]
        print(st, res.asDict())
