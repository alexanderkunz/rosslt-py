from itertools import chain
from typing import Iterable
from struct import pack, unpack
import zlib
import rosslt
import rosslt_py_msgs.msg


class ExpressionMsgElement:
    INT32 = 1
    INT64 = 2
    DOUBLE = 3
    COMPLEX = 4
    STRING = 5


class ExpressionMsgCompression:
    NONE = 0
    ZLIB = 1
    STRING = 2
    STRING_ZLIB = 3


class Expression:

    def __init__(self, history: Iterable = None, packed=None):
        self._history = list(history or [])
        self._packed = packed

    def __add__(self, other: list | tuple):

        # verify
        if other is None or not len(other):
            return self

        # copy and append to history
        history = list(self.history())
        Expression._append(history, other)

        # create expression with new history
        return Expression(history)

    def __iadd__(self, other: list | tuple):

        # verify
        if other is None or not len(other):
            return self

        # append to history
        Expression._append(self.history(), other)

        # self reference
        return self

    def __str__(self):

        # fast pass if still packed as string
        if type(self._packed) is str:
            return self._packed

        # build string
        return ';'.join(repr(x) for x in self.history())

    def __repr__(self):
        return "Expression({})".format(str(self))

    def __len__(self):
        return len(self.history())

    def __bool__(self):

        # fast pass for packed state
        if self._packed:
            if type(self._packed) is str:
                return True
            elif type(self._packed) is rosslt_py_msgs.msg.Expression:
                return self._packed.elements_size > 0 or self._packed.data_size > 0

        # determine based on length
        return len(self) > 0

    def __call__(self, *args, **kwargs):

        # initialize stack
        stack = []
        for arg in args:

            # check for ros type
            if hasattr(arg, "SLOT_TYPES"):
                arg = arg.data

            # check for tracked
            if isinstance(arg, rosslt.Tracked):
                arg = arg._data

            # copy value to  stack
            stack.append(arg)

        # iterate elements in history
        for cur_element in self.history():

            # check for operator
            if type(cur_element) is rosslt.Operator:

                # check minimum size
                if len(stack) >= cur_element.arg_count:

                    # apply operator
                    cur_element(stack)

                else:

                    # skip operator
                    pass

            else:

                # push element on stack
                stack.append(cur_element)

        # return last value on stack
        if len(stack):
            return stack[-1]

    def __reversed__(self):

        # start with empty part and list
        part = []
        part_list = []
        swap_mode = False

        # iterate elements in history
        for cur_element in self.history():

            # check for operator
            if type(cur_element) is rosslt.Operator:

                # commutative check
                if cur_element.commutative:

                    # check for swap
                    if swap_mode:
                        part.append(rosslt.Operator.SWAP)

                    # append reversed operator
                    part.append(reversed(cur_element))

                else:

                    # only reverse if not swap
                    if not swap_mode:
                        cur_element = reversed(cur_element)

                    # append operator
                    part.append(cur_element)

                # check for swap
                swap_mode = cur_element == rosslt.Operator.SWAP

                # check for swap
                if not swap_mode:

                    # part complete
                    part_list.append(part)
                    part = []

            else:

                # append parameter
                part.append(cur_element)
                swap_mode = False

        # join parts in reverse
        part_list = chain.from_iterable(reversed(part_list))

        # return new expression
        return Expression(part_list)

    @staticmethod
    def _append(history, buffer):

        # verify
        if buffer is None or not len(buffer):
            return history

        # check for buffer operator with operand
        if rosslt.config.expr_chain and len(buffer) > 1:

            # check for new swap
            new_swap = buffer[1] is rosslt.Operator.SWAP

            # check for new operator
            op_new_index = 1 + int(new_swap)
            op_new = buffer[op_new_index]
            if type(op_new) is rosslt.Operator:

                # ignore neutral element
                if not new_swap or op_new.commutative:
                    if buffer[0] == op_new.neutral:
                        return Expression._append(history, buffer[op_new_index+1:])

                # simplify tree
                if len(history) > 1:

                    # check chain operator
                    op_chain = history[-1]
                    if type(op_chain) is rosslt.Operator and op_chain.group:

                        # check for chain swap
                        chain_swap = history[-2] is rosslt.Operator.SWAP
                        if chain_swap or type(history[-2]) is not rosslt.Operator:

                            # check if both operators are in same group
                            # guarantees new operator to be in a group as well
                            if op_new.group == op_chain.group:

                                # check for chain swap
                                if chain_swap:

                                    # apply operator in right hand mode
                                    history.pop()
                                    history[-1] = buffer[0]
                                    if new_swap:
                                        history[-1], history[-2] = history[-2], history[-1]
                                    op_new(history)
                                    history.append(rosslt.Operator.SWAP)

                                else:

                                    # apply operator in left hand mode
                                    history[-1] = buffer[0]
                                    if new_swap:
                                        history[-1], history[-2] = history[-2], history[-1]
                                    if op_chain.commutative:
                                        op_new(history)
                                    else:
                                        op_new.reversed(history)
                                    if new_swap:
                                        history.append(rosslt.Operator.SWAP)

                                # continue chain
                                if new_swap:
                                    if chain_swap and op_chain.negate:
                                        history.append(op_new.reversed)
                                    else:
                                        history.append(op_new)
                                else:
                                    history.append(op_chain)

                                # simplify neutral element
                                if chain_swap or new_swap:

                                    # left hand side works for commutative operators
                                    if history[-1].commutative:
                                        if history[-1].neutral == history[-3]:
                                            history.pop()
                                            history.pop()
                                            history.pop()
                                else:

                                    # right hand side neutral element
                                    if history[-1].neutral == history[-2]:
                                        history.pop()
                                        history.pop()

                                # check cursor position
                                if op_new_index + 1 < len(buffer):

                                    # process next operator
                                    return Expression._append(history, buffer[op_new_index + 1:])

                                else:

                                    # buffer complete
                                    return history

        # create expression with new history
        history.extend(buffer)
        return history

    def apply(self, *args):
        return self(*args)

    def reverse(self):
        # noinspection PyTypeChecker
        return reversed(self)

    def history(self):
        self.unpack()
        return self._history

    def packed(self):
        return self._packed is not None

    def unpack(self):

        # check type
        if self._packed is None:

            # already unpacked
            return

        elif type(self._packed) is str:

            # iterate parts
            history = self._history
            for part in self._packed.split(";"):

                # guard against leading/trailing/duplicate parts
                if len(part):

                    # check for operator
                    if part in rosslt.Operator.MAP:

                        # append operator to history
                        history.append(rosslt.Operator.MAP[part])

                    else:

                        # append value to history
                        if part.startswith("'") or part.startswith('"'):
                            history.append(part[1:len(part)-1])
                        elif "j" in part:
                            history.append(complex(part))
                        elif "." in part:
                            history.append(float(part))
                        else:
                            history.append(int(part))

        elif type(self._packed) is rosslt_py_msgs.msg.Expression:
            # unpack from message

            # prepare
            msg = self._packed
            history = self._history
            data = bytes(msg.data)
            elements = bytes(msg.elements)
            operators = rosslt.Operator.LIST
            compression = msg.compression

            # decompress zlib
            if compression in (ExpressionMsgCompression.ZLIB, ExpressionMsgCompression.STRING_ZLIB):
                compression -= ExpressionMsgCompression.ZLIB
                data = zlib.decompress(msg.data, bufsize=msg.data_size)
                elements = zlib.decompress(msg.elements, bufsize=msg.elements_size)

            # check for string message
            if compression == ExpressionMsgCompression.STRING:

                # decode from data array
                self._packed = data.decode("UTF-8")
                self.unpack()
                return

            else:

                # read data
                cursor = 0
                for element in elements:

                    # check for data type
                    if element < 64:

                        # get value from data
                        value = None
                        if element == ExpressionMsgElement.INT32:
                            value = int.from_bytes(data[cursor:cursor+4], "little", signed=True)
                            cursor += 4
                        elif element == ExpressionMsgElement.INT64:
                            value = int.from_bytes(data[cursor:cursor+8], "little", signed=True)
                            cursor += 8
                        elif element == ExpressionMsgElement.DOUBLE:
                            value = unpack("<d", data[cursor:cursor+8])[0]
                            cursor += 8
                        elif element == ExpressionMsgElement.COMPLEX:
                            value_real = unpack("<d", data[cursor:cursor+8])[0]
                            value_imag = unpack("<d", data[cursor+8:cursor+16])[0]
                            value = complex(value_real, value_imag)
                            cursor += 16
                        elif element == ExpressionMsgElement.STRING:
                            length = int.from_bytes(data[cursor:cursor+4], "little", signed=True)
                            value = data[cursor+4:cursor+4+length].decode("UTF-8")
                            cursor += 4 + length

                        # append to history
                        history.append(value)

                    else:

                        # add operator
                        history.append(operators[element - 64])

        # mark as unpacked and free memory
        self._packed = None

    def to_message(self):

        # fast pass if packed
        if type(self._packed) is rosslt_py_msgs.msg.Expression:
            return self._packed

        # create empty message
        elements = []
        data = []

        # check for message string option
        if rosslt.config.msg_str:

            # save string representation in data array
            compression = ExpressionMsgCompression.STRING
            data.extend(str(self).encode("UTF-8"))

        else:

            # build data arrays
            compression = ExpressionMsgCompression.NONE
            for element in self.history():
                if type(element) is rosslt.Operator:
                    elements.append(element.code + 64)
                elif type(element) is int:
                    if -2147483648 <= element <= 2147483647:
                        elements.append(ExpressionMsgElement.INT32)
                        data.extend(element.to_bytes(4, "little", signed=True))
                    elif -9223372036854775808 <= element <= 9223372036854775807:
                        elements.append(ExpressionMsgElement.INT64)
                        data.extend(element.to_bytes(8, "little", signed=True))
                    else:
                        elements.append(ExpressionMsgElement.DOUBLE)
                        data.extend(pack("<d", element))
                elif type(element) is float:
                    elements.append(ExpressionMsgElement.DOUBLE)
                    data.extend(pack("<d", element))
                elif type(element) is complex:
                    elements.append(ExpressionMsgElement.COMPLEX)
                    data.extend(pack("<d", element.real))
                    data.extend(pack("<d", element.imag))
                elif type(element) is str:
                    elements.append(ExpressionMsgElement.STRING)
                    data.extend(len(element).to_bytes(4, "little"))
                    data.extend(element.encode("UTF-8"))

        # compression
        elements_size = len(elements)
        data_size = len(data)
        if rosslt.config.zlib_enable:
            if max(len(elements), len(data)) > rosslt.config.zlib_threshold:

                # compress using zlib
                compression += ExpressionMsgCompression.ZLIB
                elements = zlib.compress(bytes(elements), rosslt.config.zlib_level)
                data = zlib.compress(bytes(data), rosslt.config.zlib_level)

        # complete
        return rosslt_py_msgs.msg.Expression(
            elements=elements,
            data=data,
            compression=compression,
            elements_size=elements_size,
            data_size=data_size)

    @staticmethod
    def from_message(msg: rosslt_py_msgs.msg.Expression):

        # lazy load using message
        return Expression(packed=msg)

    @staticmethod
    def from_string(history_str: str):

        # lazy load using str
        return Expression(packed=history_str)
