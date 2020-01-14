qpyson (WIP)
============

Tool to explore, transform, or munge JSON using Python.

Goals
-----

-   Process JSON file using Python
-   Thin layer to process or apply transforms shim to call Python custom
    funcs
-   Provide the Python func as a string to the commandline or reference
    an external file where the function is defined
-   Custom processing functions can be parameterized and configured from
    the commandline
-   Output results are emitted as JSON or in tabular form (using
    [tabulate](https://pypi.org/project/tabulate/) for quick viewing
    from the commandline

### Non-Goals

-   A replacement for `jq`
-   No custom DSL for filtering or querying (use Python directly)
-   Does not support streaming (JSON files are loaded into memory)

Installation
------------

Recommend using a virtualenv or conda env to install.

    pip install qpyson

Quick Tour
----------

Example data from the Iris dataset.

    head example-data/iris.json

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

    qpyson "def f(d): return d[0]" example-data/iris.json

    {"sepalLength": 5.1, "sepalWidth": 3.5, "petalLength": 1.4, "petalWidth": 0.2, "species": "setosa"}

We can also write custom functions in a Python file.

    cat example-data/iris_explore.py

    def f(d):
        return d[0]


    def f2(d, max_items:int = 10):
        return d[:max_items]


    def f3(d, max_items:int = 5):
        return [x for x in d if x['species'] == 'setosa'][:max_items]


    def f4(d, sort_field:str, sort_direction:str = 'asc', max_items:int = 5):
        reverse = not (sort_direction == 'asc')
        d.sort(key=lambda x: x[sort_field], reverse=reverse)
        return d[:max_items]


    def f0(d):
        # Identity operator
        return d


    def first(d):
        return d[0]


    def p(d, field:str = "sepalLength"):
        import pandas as pd
        df = pd.DataFrame.from_dict(d)
        sdf = df.describe()
        return sdf.to_dict()[field]

Executing `--help` will show the output options.

    qpyson example-data/iris_explore.py example-data/iris.json --help

    usage: qpyson [-f FUNCTION_NAME] [-t] [--table-style TABLE_STYLE] [--help]
                  path_or_cmd json_file

    Util to use Python to process (e.g., filter, map) JSON files

    positional arguments:
      path_or_cmd           Path to python file, or python cmd
      json_file             Path to JSON file

    optional arguments:
      -f FUNCTION_NAME, --function-name FUNCTION_NAME
                            Function name (default: f)
      -t, --print-table     Pretty print results (default: False)
      --table-style TABLE_STYLE
                            Table fmt style using Tabulate. See
                            https://github.com/astanin/python-tabulate#table-
                            format for available options (default: simple)
      --help                Show this help message and exit

Executing function `f`, yields:

    qpyson example-data/iris_explore.py example-data/iris.json 

    {"sepalLength": 5.1, "sepalWidth": 3.5, "petalLength": 1.4, "petalWidth": 0.2, "species": "setosa"}

The output view can be changed to a table view using `--print-table` or
`-t`.

    qpyson example-data/iris_explore.py example-data/iris.json --print-table --table-style github

    |   sepalLength |   sepalWidth |   petalLength |   petalWidth | species   |
    |---------------|--------------|---------------|--------------|-----------|
    |           5.1 |          3.5 |           1.4 |          0.2 | setosa    |

A better example using function `f2` defined in `iris_explore.py`

    qpyson example-data/iris_explore.py example-data/iris.json  --function-name f2 --print-table

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

    cat example-data/iris.py

    # More examples that demonstrate generating commandline arguments


    def f(d, sort_field:str, sort_direction:str = 'asc', max_items:int = 5):
        reverse = not (sort_direction == 'asc')
        d.sort(key=lambda x: x[sort_field], reverse=reverse)
        return d[:max_items]


    def g(d, field:str = "sepalLength"):
        import pandas as pd
        df = pd.DataFrame.from_dict(d)
        sdf = df.describe()
        return sdf.to_dict()[field]

And calling `--help` will show the custom function specific arguments
(e.g., `--max_items` and `--sort_direction`)

    qpyson example-data/iris.py example-data/iris.json --help

    usage: qpyson [-f FUNCTION_NAME] [-t] [--table-style TABLE_STYLE] [--help]
                  [--sort_field SORT_FIELD] [--sort_direction SORT_DIRECTION]
                  [--max_items MAX_ITEMS]
                  path_or_cmd json_file

    Util to use Python to process (e.g., filter, map) JSON files

    positional arguments:
      path_or_cmd           Path to python file, or python cmd
      json_file             Path to JSON file

    optional arguments:
      -f FUNCTION_NAME, --function-name FUNCTION_NAME
                            Function name (default: f)
      -t, --print-table     Pretty print results (default: False)
      --table-style TABLE_STYLE
                            Table fmt style using Tabulate. See
                            https://github.com/astanin/python-tabulate#table-
                            format for available options (default: simple)
      --help                Show this help message and exit
      --sort_field SORT_FIELD
      --sort_direction SORT_DIRECTION
      --max_items MAX_ITEMS

And calling with custom options yields:

    qpyson example-data/iris.py example-data/iris.json -t --max_items=3 --sort_direction=desc --sort_field sepalLength

      sepalLength    sepalWidth    petalLength    petalWidth  species
    -------------  ------------  -------------  ------------  ---------
              7.9           3.8            6.4           2    virginica
              7.7           3.8            6.7           2.2  virginica
              7.7           2.6            6.9           2.3  virginica

Another Example calling pandas underneath the hood to get a quick
summary of the data.

    qpyson example-data/iris.py example-data/iris.json -t -f g --field=sepalLength

      count     mean       std    min    25%    50%    75%    max
    -------  -------  --------  -----  -----  -----  -----  -----
        150  5.84333  0.828066    4.3    5.1    5.8    6.4    7.9

Related JQ-ish tools
====================

<https://github.com/dbohdan/structured-text-tools#json>
