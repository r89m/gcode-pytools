__author__ = 'Richard'

from gcode.line import LineType

class BaseMachine(object):

    def __init__(self):
        self.output_properties = {
            "movement_precision": 2,
            "line_endings": "\n",
            "line_numbers": False,
            "include_comments": True
        }

    def set_output_property(self, property, value):
        self.output_properties[property] = value

    def get_output_properties(self):
        return self.output_properties

    def output(self, gcode_file):
        return gcode_file.output(None)

    def line_output_function(self, file, line):

        line_type = line.type

        if line_type == LineType.COMMENT:
            return self._output_line_comment(file, line)
        elif line_type == LineType.SET_UNITS:
            return self._output_line_set_units(file, line)
        elif line_type == LineType.SET_MOVEMENT_MODE:
            return self._output_line_set_movement_mode(file, line)
        elif line_type == LineType.MOVE_LINEAR:
            return self._output_line_move_linear(file, line)
        elif line_type == LineType.MOVE_ARC:
            return self._output_line_move_arc(file, line)
        elif line_type == LineType.DWELL:
            return self._output_line_move_dwell(file, line)
        elif line_type == LineType.TOOL_STATE:
            return self._output_line_tool_state(file, line)
        else:
            return line.output(file)

    def _output_line_comment(self, file, line):
        return line.output(file)

    def _output_line_set_units(self, file, line):
        return line.output(file)

    def _output_line_set_movement_mode(self, file, line):
        return line.output(file)

    def _output_line_move_linear(self, file, line):
        return line.output(file)

    def _output_line_move_arc(self, file, line):
        return line.output(file)

    def _output_line_move_dwell(self, file, line):
        return line.output(file)

    def _output_line_tool_state(self, file, line):
        return line.output(file)


class BaseMachineArcNotationR(BaseMachine):

    def _output_line_move_arc(self, file, line):
        return "Do it with Rs"

