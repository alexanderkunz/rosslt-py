import rosslt

# optional dependencies
try:
    import rosslt_py_msgs.msg
    import rosslt_py_msgs.srv
    import rclpy.qos
    import rclpy.node
    import rclpy.logging
    import rclpy.callback_groups
    from rclpy.logging import get_logger
except ModuleNotFoundError:
    from logging import getLogger as get_logger

LOG = get_logger(__name__)


class LocationManager:

    # node: rclpy.node.Node
    def __init__(self, node):
        self.node = node
        self.locations = []
        self.location_map = {}

        # settings
        qos_profile = rclpy.qos.qos_profile_services_default
        callback_group = rclpy.callback_groups.MutuallyExclusiveCallbackGroup()

        # subscription
        self.slt_set_sub = node.create_subscription(
            rosslt_py_msgs.msg.SetValue, "/slt_set",
            self.slt_set,
            qos_profile=qos_profile,
            callback_group=callback_group
        )

        # publisher
        self.slt_set_pub = node.create_publisher(
            rosslt_py_msgs.msg.SetValue, "/slt_set",
            qos_profile=qos_profile,
            callback_group=callback_group
        )

        # service
        self.slt_get_srv = node.create_service(
            rosslt_py_msgs.srv.GetValue, node.get_name() + "/slt_get",
            self.slt_get
        )

    def add_location(self, location: rosslt.Location):

        # check if already added
        if location.id >= 0:
            return location.id

        # allocate id and insert into list
        location.id = len(self.locations)
        self.locations.append(location)

        # return resulting id
        return location.id

    def get_location_for_source(self, source, node=""):

        # check if existing
        if source in self.location_map:
            return self.location_map[source]

        # allocate location with new id
        loc = rosslt.Location(node, len(self.locations))
        self.locations.append(loc)

        # add source reference to map
        self.location_map[source] = loc

        # pass resulting location
        return loc

    # msg: rosslt_py_msgs.msg.SetValue
    def slt_set(self, msg):

        # check for same node
        if msg.node == self.node.get_name():

            # check if location id is valid
            loc_id = msg.location
            if loc_id < 0 or loc_id >= len(self.locations):
                LOG.warn(f"invalid location id: {loc_id}")

            # apply new value
            self.locations[loc_id].set(msg.value)

    def slt_get(self, req: "rosslt_py_msgs.srv.GetValue.Request",
                res: "rosslt_py_msgs.srv.GetValue.Response"):

        # check for valid location id
        if 0 <= req.location < len(self.locations):

            # send value
            res.value = str((self.locations[req.location]).get(req.location))
            res.valid = True
            return res

        # invalid location id
        res.valid = False
        return res

    def change_location(self, node_name, loc_id, new_value):

        # build message
        msg = rosslt_py_msgs.msg.SetValue()
        msg.node = node_name
        msg.location = loc_id
        msg.value = str(new_value)  # TODO: look into string alternatives

        # publish
        if self.node.get_name() == node_name:
            self.slt_set(msg)
        else:
            self.slt_set_pub.publish(msg)
