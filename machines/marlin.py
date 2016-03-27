__author__ = 'Richard'

from machine import BaseMachine, BaseMachineArcNotationR

class Marlin(BaseMachine):

    def _output_line_tool_state(self, file, line):
        if line.tool_state > 0:
            tool = 3
        else:
            tool = 5

        response = ["M0{tool}".format(tool=tool), "G00 Z{z_pos:.3f}".format(z_pos=float(line.tool_state) / 100)]
        return response

