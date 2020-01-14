import codecs
import json
import logging
import os
import os.path
import sys
import tempfile
from argparse import ArgumentParser
from pprint import pprint

__version__ = '0.1.0'

__all__ = ['runner']

log = logging.getLogger()


def _add_options(p:ArgumentParser):
    p.add_argument('path_or_cmd', type=str, help="Path to python file, or python cmd")
    p.add_argument('json_file', type=str, help="Path to JSON file")
    p.add_argument('-f', '--function-name', type=str, help='Function name', default='f')
    return p


def get_parser() -> ArgumentParser:
    desc = "Util to use Python to process (e.g., filter, map) JSON files"
    p = ArgumentParser(description=desc)
    return _add_options(p)


def load_from_file(path, func_name):
    with codecs.open(path) as __f:
        __code = __f.read().encode("utf-8")
    exec(__code, {}, locals())
    return locals()[func_name]


def load_func_from_str_or_path(path_or_cmd: str, func_name: str='f'):

    try:
        if os.path.exists(path_or_cmd):
            return load_from_file(path_or_cmd, func_name)
        else:
            with tempfile.NamedTemporaryFile('w', suffix=".py", delete=True) as tmp:
                with open(tmp.name, 'w') as io:
                    io.write(path_or_cmd)
                result = load_from_file(tmp.name, func_name)
            return result
    except Exception as ex:
        raise ValueError(f"Expected path or cmd for `{path_or_cmd}`\n{ex}")


def run_main(json_path: str, path_or_cmd: str, func_name: str, printer=pprint):

    f = load_func_from_str_or_path(path_or_cmd, func_name)

    with open(json_path, 'r') as io:
        d = json.load(io)

    result = f(d)
    # TODO best way to configure indenting?
    print(json.dumps(result))
    return 0


def runner(argv):
    # logging.basicConfig(stream=sys.stdout, level="DEBUG")
    p = get_parser()
    pargs = p.parse_args(argv)
    log.debug(pargs)
    return run_main(pargs.json_file,  pargs.path_or_cmd, pargs.function_name)


if __name__ == '__main__':
    sys.exit(runner(sys.argv[1:]))
