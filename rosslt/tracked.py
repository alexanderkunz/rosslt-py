import copy
import math
import rosslt
from rosslt import Location

# optional dependencies
try:
    from rosslt_py_msgs.msg import LocationHeader
except ModuleNotFoundError:
    pass


class Tracked:

    def __init__(self, data, location=None,
                 location_mgr: "rosslt.LocationManager" = None):

        self._data = data
        self._location_mgr = location_mgr

        # check for supplied location
        if location:

            # parse header
            try:
                if isinstance(location, LocationHeader):
                    location = Location.from_header(location)
            except NameError:
                pass

            # apply map
            self._location = location

        else:

            # create new location and map
            self._location = Location()

        # update location reference
        self._location.ref = self

    # Interface

    def unwrap(self):
        return self._data

    def get_location(self):
        return self._location

    def get_expression(self):
        return self._location.expr

    def get_original(self):
        return self.get_expression().reverse()(self._data)

    # Casts & Representations

    def __int__(self):
        return int(self._data)

    def __float__(self):
        return float(self._data)

    def __complex__(self):
        return complex(self._data)

    def __str__(self):
        return str(self._data)

    def __bool__(self):
        return bool(self._data)

    def __abs__(self):
        return abs(self._data)

    def __repr__(self):
        return f"Tracked({repr(self._data)}, {repr(self._location)})"

    def __format__(self, format_spec):
        return format(self._data, format_spec)

    def __hash__(self):
        return hash(self._data)

    def __reversed__(self):
        return Tracked(reversed(self._data))

    def __copy__(self):
        return Tracked(copy.copy(self._data),
                       self._location.__deepcopy__(),
                       self._location_mgr)

    def __deepcopy__(self, md=None):
        return Tracked(copy.deepcopy(self._data, md),
                       self._location.__deepcopy__(),
                       self._location_mgr)

    # Comparators

    def __eq__(self, other):
        return self._data == self._unpack(other)

    def __ne__(self, other):
        return self._data != self._unpack(other)

    def __lt__(self, other):
        return self._data < self._unpack(other)

    def __le__(self, other):
        return self._data <= self._unpack(other)

    def __gt__(self, other):
        return self._data > self._unpack(other)

    def __ge__(self, other):
        return self._data >= self._unpack(other)

    # Operator Helpers

    @staticmethod
    def _unpack(other: "Tracked"):
        return other._data if type(other) is Tracked else other

    def _create_location(self, name):

        # create new instance
        location_new = Location(self._location.node)

        # add new location to own location
        self._location.content_add(name, location_new)

        # register location
        if self._location_mgr:
            self._location_mgr.add_location(location_new)

        # return new location
        return location_new

    def _update_location(self, value: "Tracked", name):

        # copy location
        location_new = value._location.copy()

        # add copied location to own location
        self._location.content_add(name, location_new)

        # return copied location
        return location_new

    def _update(self, data_new, param):

        # set value
        self._data = data_new

        # append to expression
        self._location.expr += param

        # self reference
        return self

    def _build(self, data_new, param):

        # create tracked value with updated location map
        return Tracked(data_new, self._location.copy(param))

    def _verify_type(self, _type):
        if not isinstance(self._data, _type):
            raise TypeError(str(type(self._data)) + " != " + str(_type))

    # Collections

    def __len__(self):
        return len(self._data)

    def append(self, item):
        self._verify_type(list)

        # update location or convert to tracked
        if isinstance(item, Tracked):
            self._update_location(item, str(len(self)))
        else:
            item = Tracked(item, self._create_location(str(len(self))))

        # append item
        self._data.append(item)

    def pop(self, index=-1):
        self._verify_type(list)

        # normalize index
        if index < 0:
            index = len(self) + index

        # remove item
        self._data.pop(index)
        self._location.content_remove(str(index))

    def clear(self):
        self._verify_type(list)
        self._location.content_clear()

    def __getitem__(self, item):
        self._verify_type((list, dict))
        value = self._data[item]
        # TODO: getitem/setitem sync with getattr/setattr

        # convert to tracked
        if not isinstance(value, Tracked):
            value = Tracked(value,
                            self._create_location(item),
                            self._location_mgr)

        # done
        return value

    def __setitem__(self, key, value):
        self._verify_type((list, dict))

        # convert to tracked
        if not isinstance(value, Tracked):
            value = Tracked(value,
                            self._create_location(key),
                            self._location_mgr)

        # set
        self._data[key] = value

    def __iter__(self):
        # TODO: wrapped iterator
        return self._data.__iter__()

    # Custom Operators

    def sin(self):
        return self._build(math.sin(self._data), (rosslt.Operator.SIN,))

    def isin(self):
        return self._update(math.sin(self._data), (rosslt.Operator.SIN,))

    def cos(self):
        return self._build(math.cos(self._data), (rosslt.Operator.COS,))

    def icos(self):
        return self._update(math.cos(self._data), (rosslt.Operator.COS,))

    def asin(self):
        return self._build(math.asin(self._data), (rosslt.Operator.ASIN,))

    def iasin(self):
        return self._update(math.asin(self._data), (rosslt.Operator.ASIN,))

    def acos(self):
        return self._build(math.acos(self._data), (rosslt.Operator.ACOS,))

    def iacos(self):
        return self._update(math.acos(self._data), (rosslt.Operator.ACOS,))

    # Operators

    def __add__(self, other):
        other = self._unpack(other)
        return self._build(self._data + other,
                           (other, rosslt.Operator.ADD))

    def __radd__(self, other):
        other = self._unpack(other)
        return self._build(other + self._data,
                           (other, rosslt.Operator.SWAP, rosslt.Operator.ADD))

    def __iadd__(self, other):
        other = self._unpack(other)
        return self._update(self._data + other,
                            (other, rosslt.Operator.ADD))

    def __sub__(self, other):
        other = self._unpack(other)
        return self._build(self._data - other,
                           (other, rosslt.Operator.SUB))

    def __rsub__(self, other):
        other = self._unpack(other)
        return self._build(other - self._data,
                           (other, rosslt.Operator.SWAP, rosslt.Operator.SUB))

    def __isub__(self, other):
        other = self._unpack(other)
        return self._update(self._data - other,
                            (other, rosslt.Operator.SUB))

    def _mul(self, fn, other, mult, args):

        # convert to integers if possible
        # TODO: disabled because of ros message type assertion issues
        # self._data = int_convert(self._data)
        # other = int_convert(other)

        # check for integer multiplication
        operator = rosslt.Operator.MUL
        if type(self._data) is int and type(other) is int:
            operator = rosslt.Operator.MUL_INT

        # float multiplication
        return fn(mult(self._data, other), (other, *args, operator))

    def __mul__(self, other):
        other = self._unpack(other)
        return self._mul(self._build, other,
                         lambda a, b: a * b, ())

    def __rmul__(self, other):
        other = self._unpack(other)
        return self._mul(self._build, other,
                         lambda a, b: b * a,
                         (rosslt.Operator.SWAP,))

    def __imul__(self, other):
        other = self._unpack(other)
        return self._mul(self._update, other,
                         lambda a, b: a * b, ())

    def __truediv__(self, other):
        other = self._unpack(other)
        return self._build(self._data / other,
                           (other, rosslt.Operator.DIV))

    def __rtruediv__(self, other):
        other = self._unpack(other)
        return self._build(other / self._data,
                           (other, rosslt.Operator.SWAP, rosslt.Operator.DIV))

    def __itruediv__(self, other):
        other = self._unpack(other)
        return self._update(self._data / other,
                            (other, rosslt.Operator.DIV))

    def __floordiv__(self, other):
        other = self._unpack(other)
        return self._build(self._data // other,
                           (other, rosslt.Operator.DIV_FLOOR))

    def __rfloordiv__(self, other):
        other = self._unpack(other)
        return self._build(other // self._data,
                           (other, rosslt.Operator.SWAP, rosslt.Operator.DIV_FLOOR))

    def __ifloordiv__(self, other):
        other = self._unpack(other)
        return self._update(self._data // other,
                            (other, rosslt.Operator.DIV_FLOOR))

    def __pow__(self, power, modulo=None):
        if modulo is not None:
            raise NotImplementedError("unsupported use of modulo in pow")
        power = self._unpack(power)
        return self._build(self._data ** power,
                           (power, rosslt.Operator.POW))

    def __rpow__(self, other):
        other = self._unpack(other)
        return self._build(other ** self._data,
                           (other, rosslt.Operator.SWAP, rosslt.Operator.POW))

    def __ipow__(self, other):
        other = self._unpack(other)
        return self._update(self._data ** other,
                            (other, rosslt.Operator.POW))

    # Bitwise Operators

    def __and__(self, other):
        other = self._unpack(other)
        return self._mul(self._build, other,
                         lambda a, b: a * b, ())

    def __rand__(self, other):
        other = self._unpack(other)
        return self._mul(self._build, other,
                         lambda a, b: b * a,
                         (rosslt.Operator.SWAP,))

    def __iand__(self, other):
        other = self._unpack(other)
        return self._mul(self._update, other,
                         lambda a, b: a * b, ())

    def __or__(self, other):
        other = self._unpack(other)
        return self._build(self._data + other,
                           (other, rosslt.Operator.ADD))

    def __ror__(self, other):
        other = self._unpack(other)
        return self._build(other + self._data,
                           (other, rosslt.Operator.SWAP, rosslt.Operator.ADD))

    def __ior__(self, other):
        other = self._unpack(other)
        return self._update(self._data + other,
                            (other, rosslt.Operator.ADD))

    # Attribute Wrapping

    def __getattr__(self, item):

        # get attribute from data
        value = getattr(self._data, item)

        # convert to tracked
        if type(value) is not Tracked:

            # check location for tracked reference
            location = None
            if self._location.content_has(item):
                location = self._location.content_get(item)
                if location.ref is not None:
                    return location.ref

            # create new location if necessary
            if not location:
                location = self._create_location(item)

            # try to set as tracked
            value = Tracked(value, location, self._location_mgr)
            try:
                # set value
                setattr(self._data, item, value)

            except AssertionError:
                # required for ros message data type asserts
                pass

        # found
        return value

    def __setattr__(self, key, value):

        # required for constructor
        if key in ("_data", "_location", "_location_mgr"):
            return super().__setattr__(key, value)

        # check if already tracked
        is_tracked = type(value) is Tracked
        new_tracked = None

        # guard against type assertions
        try:
            if is_tracked:

                # update data
                setattr(self._data, key, value)

                # update location
                self._update_location(value, key)

            else:

                # check for existing location
                if self._location.content_has(key):
                    location = self._location.content_get(key)
                else:

                    # create new location
                    location = self._create_location(key)

                # check for force value
                if location.force is not None:

                    # check for type correct value
                    if type(location.force) is not str:

                        # apply force value instead
                        value = location.force

                # convert to tracked
                new_tracked = Tracked(value, location, self._location_mgr)
                setattr(self._data, key, new_tracked)

        except AssertionError:
            if not is_tracked:
                value = new_tracked

            # set original data
            setattr(self._data, key, value._data)

            # update location with expression
            self._location.content_add(key, value._location)

    # Message Conversions

    def to_msg(self, msg_type):

        # initialize message
        msg = msg_type()
        msg.data = self._data
        msg.loc = self._location.header_create()
        return msg

    @staticmethod
    def from_msg(msg):
        return Tracked(msg.data, msg.loc)
