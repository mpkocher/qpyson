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
