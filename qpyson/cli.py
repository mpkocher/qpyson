import sys
from . import runner


def run_main():
    sys.exit(runner(sys.argv[1:]))


if __name__ == "__main__":
    run_main()
