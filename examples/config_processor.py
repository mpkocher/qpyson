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
