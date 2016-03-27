__author__ = 'Richard'

from gcode.line import LineType
import math

class File(object):
    def __init__(self, line_ending="\n", line_numbers=False, include_comments=True, movement_precision=3):
        self.lines = []
        self.line_index = 1
        self.line_number_digits = 3
        self.bounding_box = {"min_x": 0, "min_y": 0, "min_z": 0, "max_x": 0, "max_y": 0, "max_z": 0}
        self.output_properties = {
            "line_ending" : line_ending,
            "line_numbers" : line_numbers,
            "include_comments" : include_comments,
            "movement_precision" : movement_precision
        }

    def add_line(self, line, index=None):

        if index is None:
            self.lines.append(line)
        else:
            self.lines.insert(index, line)

        if line.type == LineType.MOVE_LINEAR:
            for axis in ["x", "y", "z"]:
                bounding_min = "min_{}".format(axis)
                bounding_max = "max_{}".format(axis)
                value = getattr(line, axis)

                if value is None:
                    value = 0

                self.bounding_box[bounding_min] = min(self.bounding_box[bounding_min], value)
                self.bounding_box[bounding_max] = max(self.bounding_box[bounding_max], value)

    def set_output_properties(self, properties):
        for prop in self.output_properties.keys():
            try:
                if properties[prop] is not None:
                    self.output_properties[prop] = properties[prop]
            except KeyError:
                pass #Do nothing

    def get_output_property(self, property):
        try:
            return self.output_properties[property]
        except KeyError:
            return None

    def output(self, machine):

        self.set_output_properties(machine.get_output_properties())

        # Calculate how many digits the line numbers should have so that everything lines up nicely
        self.line_number_digits = int(math.ceil(math.log10(len(self.lines))))

        output_str = ""

        for line in self.lines:
            # Use the passed output function to output the line. It may return a string or a list of strings
            command_output = machine.line_output_function(self, line)

            if type(command_output) is list:
                for command_output_line in command_output:
                    output_str += self.__output_line(line, command_output_line)
            else:
                output_str += self.__output_line(line, command_output)

        return output_str

    def __output_line(self, line, line_str):

        line_output = ""
        line_number_str = ""

        if self.get_output_property("line_numbers"):
            line_number_str = "N{line_number:0{line_number_digits}.0f} ".format(line_number=self.line_index, line_number_digits=self.line_number_digits)

        if self.get_output_property("include_comments"):
            line_str += " " + line.output_comment()

        if line_str.strip() != "":
            line_output += line_number_str + line_str.strip() + self.get_output_property("line_ending")
            self.line_index += 1
        elif line.type == LineType.BLANK:
            line_output += self.get_output_property("line_ending")

        return line_output


    def _format_distance(self, movement):
        return round(movement, self.get_output_property("movement_precision"))

    def set_line_ending(self, line_ending):
        self.line_ending = line_ending

    def set_line_numbers(self, line_numbers):
        self.line_numbers = line_numbers

    def set_include_comments(self, include_comments):
        self.include_comments = include_comments



    def translate(self, x=0, y=0, z=0):
        for line in self.lines:
            if line.type == LineType.MOVE_LINEAR or line.type == LineType.MOVE_ARC:
                if line.x is not None:
                    line.x += x

                if line.y is not None:
                    line.y += y

                if line.z is not None:
                    line.z += z
