
def int_convert(value):
    t = type(value)
    if t is int:
        return value
    elif t is float and value.is_integer():
        return int(value)
    return value


def apply_random(val, rng, operand, div=True):
    case = rng.randint(1, 8 if div else 6)
    if case == 1:
        val = val + operand
    elif case == 2:
        val = val - operand
    elif case == 3:
        val = val * (operand + 1)
    elif case == 4:
        val += operand
    elif case == 5:
        val -= operand
    elif case == 6:
        val *= (operand + 1)
    elif case == 7:
        val = val / (operand + 1)
    elif case == 8:
        val /= (operand + 1)
    return val
