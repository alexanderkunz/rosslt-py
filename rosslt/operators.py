import math
from functools import wraps


# operator function wrapper
def _fn_wrap(fn):

    @wraps(fn)
    def inner(self, args: list):

        # call operator function
        fn(self, args)

        # delete excess data
        excess_count = self.arg_count - self.res_count
        if excess_count > 0:
            del args[-excess_count:]

    # pass function
    return inner


class Operator:

    # operators
    SWAP = None
    ADD = None
    SUB = None
    MUL = None
    MUL_INT = None
    DIV = None
    DIV_FLOOR = None
    SIN = None
    COS = None
    ASIN = None
    ACOS = None
    POW = None
    IPOW = None

    # containers
    LIST = None
    MAP = None

    def __init__(self, code, content, commutative, arg_count, res_count, group=None, neutral=None, negate=False):
        self.code = code
        self.content = content
        self.commutative = commutative
        self.arg_count = arg_count
        self.res_count = res_count
        self.reversed = self
        self.group = group
        self.neutral = neutral
        self.negate = negate
        self.fn = lambda _, stack: None

    def __call__(self, stack):
        return self.fn(self, stack)

    def __str__(self):
        return self.content

    def __repr__(self):
        return self.content

    def __reversed__(self):
        return self.reversed

    @_fn_wrap
    def fn_swap(self, args):
        args[-1], args[-2] = args[-2], args[-1]

    @_fn_wrap
    def fn_add(self, args):
        args[-2] = args[-2] + args[-1]

    @_fn_wrap
    def fn_sub(self, args):

        # length subtraction for strings
        if type(args[-2]) is str:
            args[-2] = args[-2][:len(args[-2]) - len(args[-1])]
        else:

            # generic subtraction
            args[-2] = args[-2] - args[-1]

    @_fn_wrap
    def fn_mul(self, args):
        args[-2] = args[-2] * args[-1]

    @_fn_wrap
    def fn_div(self, args):

        # length division for strings
        if type(args[-2]) is str:
            args[-2] = args[-2][:len(args[-2]) // args[-1]]
        else:

            # generic division
            args[-2] = args[-2] / args[-1]

    @_fn_wrap
    def fn_div_floor(self, args):

        # length floor division for strings
        if type(args[-2]) is str:
            args[-2] = args[-2][:len(args[-2]) // args[-1]]
        else:

            # generic floor division
            args[-2] = args[-2] // args[-1]

    @_fn_wrap
    def fn_sin(self, args):
        args[-1] = math.sin(args[-1])

    @_fn_wrap
    def fn_cos(self, args):
        args[-1] = math.cos(args[-1])

    @_fn_wrap
    def fn_asin(self, args):
        args[-1] = math.asin(args[-1])

    @_fn_wrap
    def fn_acos(self, args):
        args[-1] = math.acos(args[-1])

    @_fn_wrap
    def fn_pow(self, args):
        args[-2] = args[-2] ** args[-1]

    @_fn_wrap
    def fn_ipow(self, args):
        args[-2] = args[-2] ** (1 / args[-1])


# instantiate operators
Operator.SWAP = Operator(0, "swap", commutative=False, arg_count=2, res_count=2)
Operator.ADD = Operator(1, "+", commutative=True, arg_count=2, res_count=1, group=1, neutral=0)
Operator.SUB = Operator(2, "-", commutative=False, arg_count=2, res_count=1, group=1, neutral=0, negate=True)
Operator.MUL_INT = Operator(3, "*", commutative=True, arg_count=2, res_count=1, group=0, neutral=1)
Operator.MUL = Operator(4, "*", commutative=True, arg_count=2, res_count=1, group=2, neutral=1)
Operator.DIV = Operator(5, "/", commutative=False, arg_count=2, res_count=1, group=2, neutral=1)
Operator.DIV_FLOOR = Operator(6, "//", commutative=False, arg_count=2, res_count=1, group=0, neutral=1)
Operator.SIN = Operator(7, "sin", commutative=True, arg_count=1, res_count=1, group=0)
Operator.COS = Operator(8, "cos", commutative=True, arg_count=1, res_count=1, group=0)
Operator.ASIN = Operator(9, "asin", commutative=True, arg_count=1, res_count=1, group=0)
Operator.ACOS = Operator(10, "acos", commutative=True, arg_count=1, res_count=1, group=0)
Operator.POW = Operator(11, "pow", commutative=False, arg_count=2, res_count=1, group=0)
Operator.IPOW = Operator(12, "ipow", commutative=False, arg_count=2, res_count=1, group=0)

# operator containers
Operator.LIST = (
    Operator.SWAP,
    Operator.ADD,
    Operator.SUB,
    Operator.MUL_INT,  # before MUL for expression string compatibility
    Operator.MUL,
    Operator.DIV,
    Operator.DIV_FLOOR,
    Operator.SIN,
    Operator.COS,
    Operator.ASIN,
    Operator.ACOS,
    Operator.POW,
    Operator.IPOW,
)
Operator.MAP = {op.content: op for op in Operator.LIST}

# reverse links
# noinspection DuplicatedCode
Operator.SWAP.reversed = Operator.SWAP
Operator.ADD.reversed = Operator.SUB
Operator.SUB.reversed = Operator.ADD
Operator.MUL.reversed = Operator.DIV
Operator.MUL_INT.reversed = Operator.DIV_FLOOR
Operator.DIV.reversed = Operator.MUL
Operator.DIV_FLOOR.reversed = Operator.MUL_INT
Operator.SIN.reversed = Operator.ASIN
Operator.COS.reversed = Operator.ACOS
Operator.ASIN.reversed = Operator.SIN
Operator.ACOS.reversed = Operator.COS
Operator.POW.reversed = Operator.IPOW
Operator.IPOW.reversed = Operator.POW

# assign functions
# noinspection DuplicatedCode
Operator.SWAP.fn = Operator.fn_swap
Operator.ADD.fn = Operator.fn_add
Operator.SUB.fn = Operator.fn_sub
Operator.MUL.fn = Operator.fn_mul
Operator.MUL_INT.fn = Operator.fn_mul
Operator.DIV.fn = Operator.fn_div
Operator.DIV_FLOOR.fn = Operator.fn_div_floor
Operator.SIN.fn = Operator.fn_sin
Operator.COS.fn = Operator.fn_cos
Operator.ASIN.fn = Operator.fn_asin
Operator.ACOS.fn = Operator.fn_acos
Operator.POW.fn = Operator.fn_pow
Operator.IPOW.fn = Operator.fn_ipow
