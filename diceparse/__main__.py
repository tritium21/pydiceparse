import sys
from diceparse import roll


def main():
    argv = ' '.join(sys.argv[1:])
    try:
        for line in roll(argv):
            print(line)
    except Exception as e:
        sys.exit(str(e))
    sys.exit(0)

if __name__ == '__main__':
    main()
