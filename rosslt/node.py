import traceback
import rosslt
from rclpy.node import Node
from rclpy.logging import get_logger

LOG = get_logger(__name__)


class TrackingNode(Node):

    def __init__(self, node_name: str):
        super().__init__(node_name)
        self.loc_mgr = rosslt.LocationManager(self)
        self.loc_id_map = {}

    def location(self, data, source=None):

        # check if source information is not provided
        if source is None:

            # automatically get file and line from caller
            # there seems to be no easy way to get the line column as well
            # as python bytecode only contains line number references
            # related: https://peps.python.org/pep-0657/
            source = traceback.extract_stack()[-2][:2]

        # get location
        location = self.loc_mgr.get_location_for_source(source, self.get_name())
        location.clear()

        # check for tracked instance
        if isinstance(data, rosslt.Tracked):

            # register nested locations
            if data._location.content:
                location.apply(data._location)
                location.register(self.loc_mgr)

            # unpack data
            data = data._data

        # apply forced values
        data = location.read(data)

        # create tracked
        return rosslt.Tracked(data, location, self.loc_mgr)

    def force_value(self, tracked: rosslt.Tracked, new_value):

        # verify location
        location = tracked.get_location()
        if not location:
            LOG.warn(f"unable to force value of object without location")
            return False
        if location.id < 0:
            LOG.warn(f"unable to force value of object with invalid location id: {location.id}")
            return False

        # apply reverse expression on new value
        reverse_expr = location.expr.reverse()
        try:
            new_value = reverse_expr(new_value)
        except ZeroDivisionError:

            # multiplication by 0 can not be reversed
            return False

        # notify location manager
        self.loc_mgr.change_location(location.node, location.id, new_value)
        return True

    @staticmethod
    def publish(publisher, tracked: rosslt.Tracked):
        return publisher.publish(tracked.to_msg(publisher.msg_type))
