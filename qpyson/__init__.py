#!/usr/bin/env python3
import codecs
import inspect
import json
import logging
import os
import os.path
import sys
import tempfile
import traceback
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from gettext import gettext
from inspect import Parameter
from typing import Callable, List, NoReturn, Optional, Text, Any

import tabulate

__version__ = "0.2.0"


log = logging.getLogger(__name__)


def _validate_file_exists(path):
    if not os.path.exists(path):
        raise IOError(f"File `{path}` does not exist", exit_code=2)
    return path


class ParserException(Exception):
    def __init__(self, message, exit_code=1):
        self.message = message
        self.exit_code = exit_code


class CustomParser(ArgumentParser):
    def print_message(self, message, file=None):
        if message:
            if file is None:
                file = sys.stderr
            file.write(message)

    def exit(self, status: int = 0, message: Optional[Text] = None) -> NoReturn:
        """
        This fundamentally changes the interface return type. It's now exit code (int)
        or raise exception.

        The error handling must be captured by caller and the caller should
        explicitly return the exit code via a sys.exit call
        """
        # if message:
        #     self._print_message(message, sys.stderr)

        if status != 0:
            raise ParserException(message, exit_code=status)
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
        "-n",
        "--no-pretty",
        action="store_true",
        help="(Non-table) Pretty print the output of dicts and list of dicts",
    )
    f("--indent", type=int, default=2, help="(Non-table) Pretty print indent spacing")
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

    f(
        "--log-level",
        help="Log level",
        default="NOTSET",
        choices=list(logging._levelToName.values()),
    )
    # There's a bit of messy munging of the input, so we're going store the state and let the
    # caller explicitly handle this
    f(
        "--help",
        action="store_true",
        help="Show this help message and exit",
        default=False,
    )
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


def load_func_from_file(path, func_name) -> Callable:
    with codecs.open(path) as __f:
        __code = __f.read().encode("utf-8")
    exec(__code, {}, locals())

    lx = locals()
    # for better error messages
    loaded_func_names = list(filter(lambda x: isinstance(lx[x], Callable), lx.keys()))

    if func_name in lx:
        return lx[func_name]
    else:
        raise KeyError(
            f"Unable to find func `{func_name}`. Found functions {','.join(loaded_func_names)}"
        )


def load_func_from_str_or_path(path_or_cmd: str, func_name: str = "f") -> Callable:

    try:
        if os.path.exists(path_or_cmd):
            return load_func_from_file(path_or_cmd, func_name)
        else:
            with tempfile.NamedTemporaryFile("w", suffix=".py", delete=True) as tmp:
                with open(tmp.name, "w") as io:
                    io.write(path_or_cmd)
                result = load_func_from_file(tmp.name, func_name)
            return result
    except Exception as ex:
        raise ValueError(f"Expected path or cmd for `{path_or_cmd}`\n{ex}")


def get_func_parameters(func: Callable) -> List[Parameter]:
    sig = inspect.signature(func)

    # the func should at least take one argument of the raw
    # contents of the JSON file
    items = list(sig.parameters.items())

    if len(items) < 1:
        raise ValueError(
            f"Function {func} should take at least one argument Signature:{items}"
        )
    if len(items) == 1:
        return []
    else:
        return [parameter for _, parameter in items[1:]]


def to_func_parameter_to_argparse_option(
    name, type_, default_value: Optional[Any], help=None
):

    prefix = "--"
    arg_id = "".join([prefix, name])

    def wrapper(p: CustomParser) -> CustomParser:
        if default_value is None:
            p.add_argument(arg_id, type=type_, help=help)
        else:
            p.add_argument(arg_id, type=type_, default=default_value, help=help)
        return p

    return wrapper


def parse_raw_args(argv, core_parser):
    """
    Because the system has to potentially load the python file or cmd from the commandline to
    get the full args, there has to manually step outside of the argparse layer

    This makes getting the help a bit tricky
    """
    log.debug(f"Parsing raw argv = {argv}")

    pargs, _ = core_parser.parse_known_args(argv)

    cmd_or_path = pargs.path_or_cmd
    func_name = pargs.function_name

    transform_func = load_func_from_str_or_path(cmd_or_path, func_name=func_name)

    transform_func_parameters = get_func_parameters(transform_func)
    option_funcs = [_add_core_options]

    for parameter in transform_func_parameters:
        help_msg = f"{parameter.name} type:{parameter.annotation} from custom func `{func_name}`"
        to_opt = to_func_parameter_to_argparse_option(
            parameter.name, parameter.annotation, parameter.default, help=help_msg
        )
        option_funcs.append(to_opt)

    p = to_parser(option_funcs)

    return p, transform_func_parameters


def to_printer_basic(indent=None):
    def jprinter(x):
        i = -1 if indent is None else indent
        print(json.dumps(x, indent=i))

    def printer_basic(dx):
        if isinstance(dx, (dict, list)):
            jprinter(dx)
        else:
            # this is mostly for raw strings
            # returned from
            print(dx)

    return printer_basic


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
    printer,
    custom_parameters: Optional[dict] = None,
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

    core_parser = get_core_parser()
    custom_parser = None

    def to_p():
        return core_parser if custom_parser is None else custom_parser

    try:
        custom_parser, transform_func_params = parse_raw_args(argv, core_parser)
        pargs = custom_parser.parse_args(argv)

        # Note, there's a delay in setting up the logging
        log_level = logging._nameToLevel[pargs.log_level]
        if log_level != logging.NOTSET:
            logging.basicConfig(
                level=log_level, format="%(asctime)s - [%(levelname)s] - %(message)s"
            )

        if pargs.help:
            custom_parser.print_help()
            return 0

        log.debug(pargs)
        custom_param_keys = {t.name for t in transform_func_params}
        custom_opts = {key: getattr(pargs, key) for key in custom_param_keys}
        indent_level = None if pargs.no_pretty else pargs.indent

        printer_func = (
            to_printer_table(pargs.table_style)
            if pargs.print_table
            else to_printer_basic(indent_level)
        )
        return run_main(
            pargs.json_file,
            pargs.path_or_cmd,
            pargs.function_name,
            printer=printer_func,
            custom_parameters=custom_opts,
        )
    except ParserException as ex:
        p = to_p()
        p.print_help()
        p.print_message(ex.message)
        return ex.exit_code
    except Exception as ex:
        traceback.print_exc(ex)
        return 2
