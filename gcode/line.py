__author__ = 'Richard'

# An enum of acceptable line types
class LineType:
    UNKNOWN, BLANK, COMMENT, SET_UNITS, SET_MOVEMENT_MODE, MOVE_LINEAR, MOVE_ARC, DWELL, TOOL_STATE = range(9)


class Line(object):

    def __init__(self, line_type=LineType.UNKNOWN, comment=None):
        self.type = line_type
        self.comment = comment

    def output(self, file):
        raise NotImplementedError("Please implement this method");

    def output_comment(self):
        if self.comment is not None:
            return "; {comment}".format(comment=self.comment)
        else:
            return ""

class BlankLine(Line):
    def __init__(self):
        super(BlankLine, self).__init__(LineType.BLANK)

    def output(self, file):
        return ""

class Comment(Line):

    def __init__(self, comment):
        super(Comment, self).__init__(LineType.COMMENT, comment)

    def output(self, file):
        return ""




class SetMovementMode(Line):
    def __init__(self, mode, comment=None):
        super(SetMovementMode, self).__init__(LineType.SET_MOVEMENT_MODE, comment)
        self.mode = mode

    def output(self, file):
        if self.mode == MovementMode.ABSOLUTE:
            return "G90"
        else:
            return "G91"


class MovementMode:
    RELATIVE, ABSOLUTE = range(2)


class SetUnits(Line):
    def __init__(self, units, comment=None):
        super(SetUnits, self).__init__(LineType.SET_UNITS, comment)
        self.units = units

    def output(self, file):
        if self.units == Units.MM:
            return "G21"
        else:
            return "G20"


class Units:
    MM, INCHES = range(2)



class MoveLinear(Line):
    def __init__(self, move_type, x=None, y=None, z=None, feed_rate=None, comment=None):
        super(MoveLinear, self).__init__(LineType.MOVE_LINEAR, comment)
        self.move_type = move_type
        self.x = x
        self.y = y
        self.z = z
        self.feed_rate = feed_rate

    def output(self, file):
        gcode_str = "G"
        if self.move_type == MoveType.FEED:
            gcode_str += "1"
        else:
            gcode_str += "0"

        if self.x is not None:
            gcode_str += " X{distance}".format(distance=file._format_distance(self.x))

        if self.y is not None:
            gcode_str += " Y{distance}".format(distance=file._format_distance(self.y))

        if self.z is not None:
            gcode_str += " Z{distance}".format(distance=file._format_distance(self.z))

        if self.feed_rate is not None:
            gcode_str += " F{distance}".format(distance=file._format_distance(self.feed_rate))

        return gcode_str

class MoveRapid(MoveLinear):
    def __init__(self, x=None, y=None, z=None, feed_rate=None, comment=None):
        super(MoveRapid, self).__init__(MoveType.RAPID, x, y, z, feed_rate, comment)

class MoveFeed(MoveLinear):
    def __init__(self, x=None, y=None, z=None, feed_rate=None, comment=None):
        super(MoveFeed, self).__init__(MoveType.FEED, x, y, z, feed_rate, comment)


class MoveType:
    RAPID, FEED = range(2)

class MoveArc(Line):
    def __init__(self, direction, end_x, end_y, center_offset_x, center_offset_y, comment=None):
        super(MoveArc, self).__init__(LineType.MOVE_ARC, comment)
        self.direction = direction
        self.end_x = end_x
        self.end_y = end_y
        self.center_offset_x = center_offset_x
        self.center_offset_y = center_offset_y

    def output(self, file):
        if self.direction == ArcDirection.CLOCKWISE:
            gcode_str = "G2"
        else:
            gcode_str = "G3"

        gcode_str += " X{} Y{} I{} J{}".format(self.end_x, self.end_y, self.center_offset_x, self.center_offset_y)
        return gcode_str

class ArcDirection:
    CLOCKWISE, ANTI_CLOCKWISE = range(2)


class SetToolState(Line):
    def __init__(self, tool_state, comment=None):
        super(SetToolState, self).__init__(LineType.TOOL_STATE, comment)
        self.tool_state = tool_state

    def output(self, file):
        #return "G01 Z{z_dir}\nM106 S{tool_state}".format(tool_state=self.tool_state,
        #                                                 z_dir=("3" if self.tool_state == ToolState.ON else "0"))
        return "M106 S{tool_state}".format(tool_state=self.tool_state)


class ToolState:
    ON = 255
    OFF = 0