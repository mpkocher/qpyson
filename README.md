# qpyson

Tool to explore, transform, or munge JSON using Python.  

## Goals

- Process JSON file using Python
- Thin layer to process or apply

### Non-Goals

- Not a replacement for `jq`
- No 


# Femto-sec Quick Start

## Example Usage

Using an Iris data JSON file that contains a list of Iris records.

```bash
$> head iris.json
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

```


Directly write the function to process

```bash
qpyson "def f(d): return d[0]" path/to/iris.json
```

Or pass processing function defined, `f` defined in `explore.py`.

```python
# explore.py
def f(d):
    return d[0]
```


And calling from the commandline.

```bash
qpyson ./explore.py iris.json
```


# Related JQ-ish tools

https://github.com/dbohdan/structured-text-tools#json
