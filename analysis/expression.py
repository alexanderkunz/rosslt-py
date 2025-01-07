import timeit


def expression_pack(expr):
    setup = f"""
import rosslt
import rosslt_py_msgs.msg
exp = rosslt.Expression.from_string("{expr}")
    """

    a = min(timeit.Timer("exp.to_message()", setup=setup).repeat(3, 1000))
    b = min(timeit.Timer("str(exp)", setup=setup).repeat(3, 1000))
    print("to_message:     {:.6f}ms".format(a))
    print("str(exp):       {:.6f}ms".format(b))


def expression_unpack(expr):
    setup = f"""
import rosslt
import rosslt_py_msgs.msg
exp = rosslt.Expression.from_string("{expr}")
msg = exp.to_message()
expr_str = str(exp)
    """

    a = min(timeit.Timer("rosslt.Expression.from_message(msg)", setup=setup).repeat(3, 1000))
    b = min(timeit.Timer("rosslt.Expression.from_string(expr_str)", setup=setup).repeat(3, 1000))
    print("from_message:   {:.6f}ms".format(a))
    print("from_string:    {:.6f}ms".format(b))


def main():
    print(f"Expression")
    expr = "2" + ";5;swap;+;2;*;8;swap;-;sin" * 512
    print(f"len(expr):      {len(expr)}")
    print("\nPack")
    expression_pack(expr)
    print("\nUnpack")
    expression_unpack(expr)


if __name__ == "__main__":
    main()
