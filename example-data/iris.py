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