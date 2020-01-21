qpyson (WIP)
============

The JSON querying tool, [jq](https://stedolan.github.io/jq/), is a
really powerful tool. However, it’s sometimes a bit involved and has a
learning curve that requires digging into the [jq
manual](https://stedolan.github.io/jq/manual/) and familiarizing
yourself with a custom language.

`qpyson` is a thin tool to explore, transform, or munge JSON using
Python as the processing language.

Goals
-----

-   Process JSON file using Python
-   Thin layer to process or apply transforms written in Python
-   Provide the Python func as a string to the commandline or reference
    an external file where the function is defined
-   Custom functions can be paramaterized and configured from the
    commandline
-   Output results are emitted as JSON or in tabular form (using
    [tabulate](https://pypi.org/project/tabulate/) for quick viewing
    from the commandline

### Non-Goals

-   A replacement for `jq`
-   No custom DSL for filtering or querying (use Python directly)
-   Does not support streaming (JSON files are loaded into memory)

Installation
------------

Recommended to install using a
[virtualenv](https://docs.python-guide.org/dev/virtualenvs/) or
[conda](https://docs.conda.io/en/latest/) env to install.

    pip install qpyson

Quick Tour
----------

Example data from the Iris dataset.

    head examples/iris.json

    [
      {"sepalLength": 5.1, "sepalWidth": 3.5, "petalLength": 1.4, "petalWidth": 0.2, "species": "setosa"},
      {"sepalLength": 4.9, "sepalWidth": 3.0, "petalLength": 1.4, "petalWidth": 0.2, "species": "setosa"},
      {"sepalLength": 4.7, "sepalWidth": 3.2, "petalLength": 1.3, "petalWidth": 0.2, "species": "setosa"},
      {"sepalLength": 4.6, "sepalWidth": 3.1, "petalLength": 1.5, "petalWidth": 0.2, "species": "setosa"},
      {"sepalLength": 5.0, "sepalWidth": 3.6, "petalLength": 1.4, "petalWidth": 0.2, "species": "setosa"},
      {"sepalLength": 5.4, "sepalWidth": 3.9, "petalLength": 1.7, "petalWidth": 0.4, "species": "setosa"},
      {"sepalLength": 4.6, "sepalWidth": 3.4, "petalLength": 1.4, "petalWidth": 0.3, "species": "setosa"},
      {"sepalLength": 5.0, "sepalWidth": 3.4, "petalLength": 1.5, "petalWidth": 0.2, "species": "setosa"},
      {"sepalLength": 4.4, "sepalWidth": 2.9, "petalLength": 1.4, "petalWidth": 0.2, "species": "setosa"},

We can define a custom function to process the JSON dataset. By default
the function is named `f` and can be customized by `-f` or
`--function-name` commandline argument.

    qpyson "def f(d): return d[0]" examples/iris.json

    {
      "sepalLength": 5.1,
      "sepalWidth": 3.5,
      "petalLength": 1.4,
      "petalWidth": 0.2,
      "species": "setosa"
    }

We can also write custom functions in a Python file.

    cat examples/iris_explore.py

    def f(d):
        return d[0]


    def f2(d, max_items: int = 10):
        return d[:max_items]


    def f3(d, max_items: int = 5):
        return [x for x in d if x["species"] == "setosa"][:max_items]


    def f4(d, sort_field: str, sort_direction: str = "asc", max_items: int = 5):
        reverse = not (sort_direction == "asc")
        d.sort(key=lambda x: x[sort_field], reverse=reverse)
        return d[:max_items]


    def f0(d):
        # Identity operator
        return d


    def first(d):
        return d[0]


    def p(d, field: str = "sepalLength"):
        import pandas as pd

        df = pd.DataFrame.from_dict(d)
        sdf = df.describe()
        return sdf.to_dict()[field]

Executing `--help` will show the output options.

    qpyson examples/iris_explore.py examples/iris.json --help

    usage: qpyson [-f FUNCTION_NAME] [-n] [--indent INDENT] [-t]
                  [--table-style TABLE_STYLE]
                  [--log-level {CRITICAL,ERROR,WARNING,INFO,DEBUG,NOTSET}]
                  [--help]
                  path_or_cmd json_file

    Util to use Python to process (e.g., filter, map) JSON files

    positional arguments:
      path_or_cmd           Path to python file, or python cmd
      json_file             Path to JSON file

    optional arguments:
      -f FUNCTION_NAME, --function-name FUNCTION_NAME
                            Function name (default: f)
      -n, --no-pretty       Non-table Pretty print the output of dicts and list of
                            dicts (default: False)
      --indent INDENT       Non-table Pretty print indent spacing (default: 2)
      -t, --print-table     Pretty print results (default: False)
      --table-style TABLE_STYLE
                            Table fmt style using Tabulate. See
                            https://github.com/astanin/python-tabulate#table-
                            format for available options (default: simple)
      --log-level {CRITICAL,ERROR,WARNING,INFO,DEBUG,NOTSET}
                            Log level (default: NOTSET)
      --help                Show this help message and exit (default: False)

Executing function `f`, yields:

    qpyson examples/iris_explore.py examples/iris.json 

    {
      "sepalLength": 5.1,
      "sepalWidth": 3.5,
      "petalLength": 1.4,
      "petalWidth": 0.2,
      "species": "setosa"
    }

The output view can be changed to a table view using `--print-table` or
`-t`.

    qpyson examples/iris_explore.py examples/iris.json --print-table --table-style github

    |   sepalLength |   sepalWidth |   petalLength |   petalWidth | species   |
    |---------------|--------------|---------------|--------------|-----------|
    |           5.1 |          3.5 |           1.4 |          0.2 | setosa    |

A better example using function `f2` defined in `iris_explore.py`

    qpyson examples/iris_explore.py examples/iris.json  --function-name f2 --print-table

      sepalLength    sepalWidth    petalLength    petalWidth  species
    -------------  ------------  -------------  ------------  ---------
              5.1           3.5            1.4           0.2  setosa
              4.9           3              1.4           0.2  setosa
              4.7           3.2            1.3           0.2  setosa
              4.6           3.1            1.5           0.2  setosa
              5             3.6            1.4           0.2  setosa
              5.4           3.9            1.7           0.4  setosa
              4.6           3.4            1.4           0.3  setosa
              5             3.4            1.5           0.2  setosa
              4.4           2.9            1.4           0.2  setosa
              4.9           3.1            1.5           0.1  setosa

Custom functions can be defined with required or optional values (with
defaults) combined with Python 3 type annotations to generate

    cat examples/iris.py

    # More examples that demonstrate generating commandline arguments


    def f(d, sort_field: str, sort_direction: str = "asc", max_items: int = 5):
        reverse = not (sort_direction == "asc")
        d.sort(key=lambda x: x[sort_field], reverse=reverse)
        return d[:max_items]


    def g(d, field: str = "sepalLength"):
        import pandas as pd

        df = pd.DataFrame.from_dict(d)
        sdf = df.describe()
        return sdf.to_dict()[field]

And calling `--help` will show the custom function specific arguments
(e.g., `--max_items` and `--sort_direction`)

    qpyson examples/iris.py examples/iris.json --help

    usage: qpyson [-f FUNCTION_NAME] [-n] [--indent INDENT] [-t]
                  [--table-style TABLE_STYLE]
                  [--log-level {CRITICAL,ERROR,WARNING,INFO,DEBUG,NOTSET}]
                  [--help] [--sort_field SORT_FIELD]
                  [--sort_direction SORT_DIRECTION] [--max_items MAX_ITEMS]
                  path_or_cmd json_file

    Util to use Python to process (e.g., filter, map) JSON files

    positional arguments:
      path_or_cmd           Path to python file, or python cmd
      json_file             Path to JSON file

    optional arguments:
      -f FUNCTION_NAME, --function-name FUNCTION_NAME
                            Function name (default: f)
      -n, --no-pretty       Non-table Pretty print the output of dicts and list of
                            dicts (default: False)
      --indent INDENT       Non-table Pretty print indent spacing (default: 2)
      -t, --print-table     Pretty print results (default: False)
      --table-style TABLE_STYLE
                            Table fmt style using Tabulate. See
                            https://github.com/astanin/python-tabulate#table-
                            format for available options (default: simple)
      --log-level {CRITICAL,ERROR,WARNING,INFO,DEBUG,NOTSET}
                            Log level (default: NOTSET)
      --help                Show this help message and exit (default: False)
      --sort_field SORT_FIELD
                            sort_field type:<class 'str'> from custom func `f`
                            (default: _empty)
      --sort_direction SORT_DIRECTION
                            sort_direction type:<class 'str'> from custom func `f`
                            (default: asc)
      --max_items MAX_ITEMS
                            max_items type:<class 'int'> from custom func `f`
                            (default: 5)

And calling with custom options yields:

    qpyson examples/iris.py examples/iris.json -t --max_items=3 --sort_direction=desc --sort_field sepalLength

      sepalLength    sepalWidth    petalLength    petalWidth  species
    -------------  ------------  -------------  ------------  ---------
              7.9           3.8            6.4           2    virginica
              7.7           3.8            6.7           2.2  virginica
              7.7           2.6            6.9           2.3  virginica

Another Example calling pandas underneath the hood to get a quick
summary of the data.

    qpyson examples/iris.py examples/iris.json -t -f g --field=sepalLength

      count     mean       std    min    25%    50%    75%    max
    -------  -------  --------  -----  -----  -----  -----  -----
        150  5.84333  0.828066    4.3    5.1    5.8    6.4    7.9

It’s also possible to create thin JSON munging tools for configuration
of systems or tools that take JSON as input.

For example a JSON configuration template with defaults.

    cat examples/config_template.json

    {
      "alpha":  1234,
      "beta": null,
      "gamma": 90.1234
    }

And a processing function, `f`.

    cat examples/config_processor.py

    def f(dx, alpha: float, beta: float, gamma: float):
        """Simple example of config munging"""

        def _set(k, v):
            if v:
                dx[k] = v

        items = [("alpha", alpha), ("beta", beta), ("gamma", gamma)]

        for name, value in items:
            _set(name, value)

        dx["_comment"] = "Configured with qpyson"
        return dx

Running `--help` will show the supported configuration options.

    qpyson examples/config_processor.py examples/config_template.json --help

    usage: qpyson [-f FUNCTION_NAME] [-n] [--indent INDENT] [-t]
                  [--table-style TABLE_STYLE]
                  [--log-level {CRITICAL,ERROR,WARNING,INFO,DEBUG,NOTSET}]
                  [--help] [--alpha ALPHA] [--beta BETA] [--gamma GAMMA]
                  path_or_cmd json_file

    Util to use Python to process (e.g., filter, map) JSON files

    positional arguments:
      path_or_cmd           Path to python file, or python cmd
      json_file             Path to JSON file

    optional arguments:
      -f FUNCTION_NAME, --function-name FUNCTION_NAME
                            Function name (default: f)
      -n, --no-pretty       Non-table Pretty print the output of dicts and list of
                            dicts (default: False)
      --indent INDENT       Non-table Pretty print indent spacing (default: 2)
      -t, --print-table     Pretty print results (default: False)
      --table-style TABLE_STYLE
                            Table fmt style using Tabulate. See
                            https://github.com/astanin/python-tabulate#table-
                            format for available options (default: simple)
      --log-level {CRITICAL,ERROR,WARNING,INFO,DEBUG,NOTSET}
                            Log level (default: NOTSET)
      --help                Show this help message and exit (default: False)
      --alpha ALPHA         alpha type:<class 'float'> from custom func `f`
                            (default: _empty)
      --beta BETA           beta type:<class 'float'> from custom func `f`
                            (default: _empty)
      --gamma GAMMA         gamma type:<class 'float'> from custom func `f`
                            (default: _empty)

Now configuring `alpha`, `beta` and `gamma`.

    qpyson examples/config_processor.py examples/config_template.json --alpha 1.23 --beta 2.34 --gamma 3.45

    {
      "alpha": 1.23,
      "beta": 2.34,
      "gamma": 3.45,
      "_comment": "Configured with qpyson"
    }

Testing
=======

Testing is currently done using RMarkdown using the make target `doc`.

This should probably be ported to non-R based approach. However, this
current approach does keep the docs (e.g., README.md) up to date.

Related JQ-ish tools
====================

<https://github.com/dbohdan/structured-text-tools#json>
