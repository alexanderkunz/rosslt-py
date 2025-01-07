import rosslt
import rosslt_py_msgs.msg
import rosslt_py_msgs.srv


class Location:

    def __init__(self, node="", loc_id=-1, expr=None, content=None):
        self.id = loc_id
        self.node = node
        self.expr = expr or rosslt.Expression()
        self.content = content
        self.ref = None
        self.force = None

    def __eq__(self, other):
        return self.node == other.node and self.id == other.id

    def __str__(self):
        return "Location({}, '{}', {}, {}, [{}])".format(
            self.id, self.node, repr(self.expr), repr(self.force),
            ", ".join(repr(x) for x in self.content.items()) if self.content else "")

    def __repr__(self):
        return str(self)

    def __copy__(self):

        # copy with content (shallow) but discard location id
        return self.copy(None, False, False, True)

    def __deepcopy__(self, memodict=None):

        # copy without content nor location id
        loc = self.copy(None, False, False, False)

        # recursively copy locations
        if self.content:
            for name, item in self.content.items():
                loc.content_add(name, item.__deepcopy__())

        # return resulting location
        return loc

    def has_state(self):
        return self.id >= 0 or self.expr

    def copy(self, expr=None, keep_id=True, keep_expr=True, keep_content=True):
        return Location(self.node,
                        self.id if keep_id else -1,
                        self.expr + expr if keep_expr else None,
                        dict(self.content) if keep_content and self.content else None)

    def clear(self):

        # clear expression and tracked reference
        self.expr = rosslt.Expression()
        self.ref = None

        # recursively clear tree
        if self.content:
            for item in self.content.values():
                item.clear()

    def apply(self, loc_tree: "rosslt.Location" = None):

        # apply tree
        if loc_tree.content:
            for name, item in loc_tree.content.items():
                if self.content_has(name):
                    loc = self.content_get(name)
                else:
                    loc = item.copy(None, False, False, False)
                    self.content_add(name, loc)
                loc.apply(item)

    def register(self, loc_mgr: "rosslt.LocationManager"):

        # register if necessary
        if self.id < 0:
            loc_mgr.add_location(self)

        # recursively register tree
        if self.content:
            for item in self.content.values():
                item.register(loc_mgr)

    def get(self):
        return self.ref

    def set(self, value):

        # set value override of own node
        self.force = value

    def read(self, value, value_type=None):

        # read own node
        if self.force is not None:

            # check if conversion needed
            if type(self.force) is str:

                # set data property
                # types: float, double, int8, uint8, int16, uint16, int32, uint32, int64, uint64
                if value_type is not None \
                        and (value_type.startswith("int") or value_type.startswith("uint")):
                    value = int(round(float(self.force)))
                else:
                    value = float(self.force)

                # store converted value
                self.force = value

            else:

                # use stored value
                value = self.force

        # check for child nodes
        if self.content:

            # get slot types if existing
            types = getattr(value, "_fields_and_field_types") \
                if hasattr(value, "_fields_and_field_types") else None

            # recursively process child nodes
            for name, item in self.content.items():

                # get type
                value_type = None
                if types is not None:
                    value_type = types[name]

                # read and apply attribute
                setattr(value, name, item.read(getattr(value, name), value_type))

        # pass value in case root content changed
        return value

    def content_add(self, name: str, location: "rosslt.Location"):

        # add to content
        if self.content:
            self.content[name] = location
        else:
            self.content = {name: location}

    def content_remove(self, name: str):

        # delete if initialized
        if self.content:
            del self.content[name]

    def content_clear(self):

        # clear if initialized
        if self.content:
            self.content.clear()

    def content_has(self, name):

        # in case content is not initialized
        if not self.content:
            return False

        # dictionary contains lookup
        return name in self.content

    def content_get(self, name):

        # trivial dictionary accessor
        return self.content[name]

    def content_get_or_default(self, name):

        # initialize content if necessary
        if not self.content:
            self.content = {name: Location()}

        # check if not existing
        if name not in self.content:
            location = Location()
            self.content_add(name, location)

        # forward to content getter
        return self.content_get(name)

    def header_write(self, header: rosslt_py_msgs.msg.LocationHeader, parent=0, name=""):

        # get next index
        loc_index = len(header.locations)

        # get node id
        try:
            node_id = header.locations.index(self.node)
        except ValueError:
            node_id = len(header.locations)
            header.nodes.append(self.node)

        # append location
        header.locations.append(self.to_message(node_id, name))

        # update graph
        if loc_index:
            header.graph.append(parent)
            header.graph.append(loc_index)

        # set new parent
        parent = loc_index

        # iterate content
        if self.content:
            for name, item in self.content.items():

                # add content path and recurse
                item.header_write(header, parent, name)

    def header_create(self) -> rosslt_py_msgs.msg.LocationHeader:

        # recursively fill with location tree
        header = rosslt_py_msgs.msg.LocationHeader()
        header.nodes.append(self.node)
        self.header_write(header)

        # header is done
        return header

    def to_message(self, node, name):

        # create message from location data
        return rosslt_py_msgs.msg.Location(
            id=self.id,
            node=node,
            name=name,
            expr=self.expr.to_message()
        )

    @staticmethod
    def from_message(msg: rosslt_py_msgs.msg.Location, node):

        # create location from message data
        return Location(
            node=node,
            loc_id=msg.id,
            expr=rosslt.Expression.from_message(msg.expr)
        )

    @staticmethod
    def from_header(msg: rosslt_py_msgs.msg.LocationHeader):

        # find root location
        if not len(msg.locations):
            raise RuntimeError("no locations in header")

        # create locations
        locations = [Location.from_message(i, msg.nodes[i.node]) for i in msg.locations]
        root = locations[0]

        # build graph
        for parent, child in zip(msg.graph[::2], msg.graph[1::2]):
            locations[parent].content_add(msg.locations[child].name, locations[child])

        # location is done
        return root
