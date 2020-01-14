#!/usr/bin/env python3
import codecs
import inspect
import json
import logging
import os
import os.path
import sys
import tempfile
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from argparse import _HelpAction as HelpAction
from gettext import gettext
from inspect import Parameter
from typing import Callable, List, NoReturn, Optional, Text

import tabulate

__version__ = "0.1.0"


log = logging.getLogger(__name__)


def _validate_file_exists(path):
    if not os.path.exists(path):
        raise ParserException(f"File {path} does not exist")
    return path


class ParserException(Exception):
    def __init__(self, message):
        self.message = message


class ShowHelp(Exception):
    # This might not be the best idea
    pass


class CustomHelpAction(HelpAction):
    def __call__(self, parser, namespace, values, option_string=None):
        # Not sure this is a good idea, however this is the fallout from
        # getting around the sys.exit usage in the core argparse API
        raise ShowHelp(parser.format_help())


class CustomParser(ArgumentParser):
    def print_message(self, message, file=None):
        if message:
            if file is None:
                file = sys.stderr
            file.write(message)

    def exit(self, status: int = 0, message: Optional[Text] = None) -> NoReturn:
        """
        This semantically changes the interface quite a bit.

        The error handling must be captured by caller and the caller should
        explicitly return the exit code via a sys.exit call
        """
        # if message:
        #     self._print_message(message, sys.stderr)

        if status != 0:
            raise ParserException(message)
        return status

    def error(self, message: Text) -> NoReturn:
        args = {"prog": self.prog, "message": message}
        self.exit(2, gettext("%(prog)s: error: %(message)s\n") % args)


def _add_core_options(p: CustomParser):
    f = p.add_argument

    f("path_or_cmd", type=str, help="Path to python file, or python cmd")
    f("json_file", type=_validate_file_exists, help="Path to JSON file")
    f("-f", "--function-name", type=str, help="Function name", default="f")
    f(
        "-t",
        "--print-table",
        action="store_true",
        help="Pretty print results",
        default=False,
    )
    f(
        "--table-style",
        type=str,
        help="Table fmt style using Tabulate. See https://github.com/astanin/python-tabulate#table-format for available options",
        default="simple",
    )
    f("--help", action=CustomHelpAction, help="Show this help message and exit")
    return p


def to_parser(options) -> CustomParser:
    desc = "Util to use Python to process (e.g., filter, map) JSON files"
    p = CustomParser(
        description=desc, formatter_class=ArgumentDefaultsHelpFormatter, add_help=False
    )
    for opt in options:
        opt(p)
    return p


def get_core_parser() -> CustomParser:
    return to_parser([_add_core_options])


def load_from_file(path, func_name) -> Callable:
    with codecs.open(path) as __f:
        __code = __f.read().encode("utf-8")
    exec(__code, {}, locals())
    return locals()[func_name]


def load_func_from_str_or_path(path_or_cmd: str, func_name: str = "f") -> Callable:

    try:
        if os.path.exists(path_or_cmd):
            return load_from_file(path_or_cmd, func_name)
        else:
            with tempfile.NamedTemporaryFile("w", suffix=".py", delete=True) as tmp:
                with open(tmp.name, "w") as io:
                    io.write(path_or_cmd)
                result = load_from_file(tmp.name, func_name)
            return result
    except Exception as ex:
        raise ValueError(f"Expected path or cmd for `{path_or_cmd}`\n{ex}")


def get_func_parameters(func: Callable) -> List[Parameter]:
    sig = inspect.signature(func)
    # the func should at least take one argument
    items = list(sig.parameters.items())

    if len(items) < 1:
        raise ValueError(
            f"Function {func} should take atleast one argument Signature:{items}"
        )
    if len(items) == 1:
        return []
    else:
        return [parameter for _, parameter in items[1:]]


def to_func_parameter_to_argparse_option(name, type_, default):

    prefix = "--"
    arg_id = "".join([prefix, name])

    def wrapper(p: CustomParser) -> CustomParser:
        if default is None:
            p.add_argument(arg_id, type=type_)
        else:
            p.add_argument(arg_id, type=type_, default=default)
        return p

    return wrapper


def _find_argument(short_name, long_name, argv):
    len_argv = len(argv)

    def is_arg(v):
        return any(v == name for name in (short_name, long_name))

    for i, value in enumerate(argv):
        if is_arg(value) and (i + 1) <= len_argv:
            return argv[i + 1]

    return None


def _find_argument_or_raise(short_name, long_name, argv):
    result = _find_argument(short_name, long_name, argv)
    if result is None:
        raise ValueError(f"Unable to find ({short_name} or {long_name}) in {argv}")
    return result


def parse_raw_args(argv, core_parser):
    """
    Because the system has to potentially load the python file or cmd from the commandline to
    get the full args, there has to manually step outside of the argparse layer

    This makes getting the help a bit tricky
    """
    log.debug(f"Parsing raw argv = {argv}")
    # this needs to check for --help
    if len(argv) < 2:
        # this will raise
        core_parser.parse_args(argv)

    cmd_or_path = argv[0]
    # json_file = argv[1]

    function_name = _find_argument("-f", "--function-name", argv) or "f"
    transform_func = load_func_from_str_or_path(cmd_or_path, func_name=function_name)

    # get args from func and build parser
    transform_func_parameters = get_func_parameters(transform_func)
    option_funcs = [_add_core_options]

    for parameter in transform_func_parameters:
        to_opt = to_func_parameter_to_argparse_option(
            parameter.name, parameter.annotation, parameter.default
        )
        option_funcs.append(to_opt)

    p = to_parser(option_funcs)

    return p, transform_func_parameters


def printer_basic(dx):
    if isinstance(dx, dict):
        print(json.dumps(dx))
    elif isinstance(dx, str):
        print(dx)
    elif isinstance(dx, list):
        # dict, primitive
        print(json.dumps(dx))
    else:
        print(dx)


def to_printer_table(table_fmt="simple"):
    def tabulate_printer(items):
        print(tabulate.tabulate(items, headers="keys", tablefmt=table_fmt))

    def printer_table(dx):
        if isinstance(dx, dict):
            tabulate_printer([dx])
        elif isinstance(dx, str):
            print(dx)
        elif isinstance(dx, list):
            tabulate_printer(dx)
        else:
            print(dx)

    return printer_table


def run_main(
    json_path: str,
    path_or_cmd: str,
    func_name: str,
    custom_parameters: Optional[dict] = None,
    printer=printer_basic,
) -> int:

    f = load_func_from_str_or_path(path_or_cmd, func_name)

    with open(json_path, "r") as io:
        d = json.load(io)

    if custom_parameters:
        log.debug(f"Calling {f} with custom params {custom_parameters}")
        result = f(d, **custom_parameters)
    else:
        result = f(d)

    printer(result)
    return 0


def runner(argv) -> int:
    # logging.basicConfig(stream=sys.stdout, level="DEBUG")

    core_parser = get_core_parser()
    parser, transform_func_params = parse_raw_args(argv, core_parser)

    try:
        pargs = parser.parse_args(argv)
        log.debug(pargs)
        custom_param_keys = {t.name for t in transform_func_params}
        custom_opts = {key: getattr(pargs, key) for key in custom_param_keys}
        printer_func = (
            to_printer_table(pargs.table_style) if pargs.print_table else printer_basic
        )
        return run_main(
            pargs.json_file,
            pargs.path_or_cmd,
            pargs.function_name,
            custom_parameters=custom_opts,
            printer=printer_func,
        )
    except ShowHelp:
        parser.print_help()
        return 0
    except ParserException as ex:
        parser.print_help()
        parser.print_message(ex.message)
        return 1
    except Exception as ex:
        parser.print_message(f"Failed {ex}")
        return 1
