from __future__ import division
# Script to convert a bitmap to gcode for engraving with a laser

__author__ = 'Richard'

import sys
import argparse

from PIL import Image
import json
import math

from gcode.file import File as GCodeFile
from gcode.line import (SetUnits, SetMovementMode, BlankLine, Comment, MoveRapid, MoveFeed, SetToolState,
                        Units, MovementMode, ToolState)


def scale(val, src_range, dest_range):
    """
    Scale the given value from the scale of src to the scale of dst.
    """
    return (float(val - src_range[0]) / (src_range[1]-src_range[0])) * (dest_range[1]-dest_range[0]) + dest_range[0]


def bitmap_to_laser(source_image=None, mm_per_pass=0.1, feedrate_lase=1000, feedrate_rapid=None, invert=False,
                    dimension_width=None, dimension_height=None, rapid_min_distance=20,
                    laser_power_min=0, laser_power_max=255,
                    colour_mode_bw=False, bw_threshold=125,
                    offset_x=0, offset_y=0, offset_z=0):

    if feedrate_rapid is None:
        feedrate_rapid = feedrate_lase

    # Check that only one dimension was provided
    if dimension_width is not None and dimension_height is not None:
        raise ValueError("Please only provide one dimension")

    pixels = source_image.load()
    num_pixels_wide = source_image.size[0]
    num_pixels_high = source_image.size[1]

    if dimension_width:
        mm_per_pixel = dimension_width / num_pixels_wide
    elif dimension_height:
        mm_per_pixel = dimension_height / num_pixels_high
    else:
        # Default resolution
        mm_per_pixel = 0.1


    print dimension_width, num_pixels_wide, mm_per_pixel

    output_width_mm = num_pixels_wide * mm_per_pixel
    output_height_mm = num_pixels_high * mm_per_pixel

    # Calculate how many passes you'd need given the distance between passes and the size of the pixel
    # Be sure to round up and convert to an integer
    passes_per_pixel = int(math.ceil(mm_per_pixel / mm_per_pass))

    # Now, recalculate the distance between passes, as it may need to be smaller than before
    mm_per_pass = float(mm_per_pass) / passes_per_pixel

    # Init GCode file
    gcode_file = GCodeFile()
    gcode_file.add_line(SetMovementMode(MovementMode.ABSOLUTE, "Set movement to absolute"))
    gcode_file.add_line(SetUnits(Units.MM, "Set units to mm"))
    gcode_file.add_line(MoveRapid(0, 0, 0, feedrate_rapid, "Move to the origin"))
    gcode_file.add_line(SetToolState(ToolState.OFF))
    gcode_file.add_line(BlankLine())

    # Initial direction is RTL, as it is switched before each iteration
    pass_direction = PassDirection.RIGHT_TO_LEFT

    # Image rows go from top left, we want to go from bottom left
    rows = range(num_pixels_high)
    columns = range(num_pixels_wide)
    rows.reverse()
    # Columns is also reversed as it is reversed again before each iteration
    columns.reverse()

    # Iterate over each row
    for row in rows:
        gcode_file.add_line(BlankLine())
        gcode_file.add_line(BlankLine())

        row_y_pos = (num_pixels_high - (row + 1)) * mm_per_pixel

        # Generate moves for each pass
        for laser_pass in range(passes_per_pixel):
            # Reset the laser state
            previous_laser_state = LaserState.OFF

            # Set the Y position
            pass_y_offset = (float(laser_pass) / passes_per_pixel) * mm_per_pixel
            pass_y_pos = row_y_pos + pass_y_offset
            gcode_file.add_line(MoveRapid(None, pass_y_pos, None, feedrate_rapid))

            # Reverse the direction of passes
            columns.reverse()
            if pass_direction == PassDirection.LEFT_TO_RIGHT:
                pass_direction = PassDirection.RIGHT_TO_LEFT
                laser_last_x_pos = output_width_mm
            else:
                pass_direction = PassDirection.LEFT_TO_RIGHT
                laser_last_x_pos = 0

            laser_state = laser_power_min

            # Iterate over each column
            for col in columns:
                # Check if the pixel grayscale has changed - if so, move to the end of the pixel.
                #                                            if not, move onto the next pixel.
                this_pixel_value = pixels[col, row][0]
                # print row, laser_pass, col, this_pixel_value

                # Get the state of the laser given this pixel's value
                laser_state = this_pixel_value

                if not invert:
                    laser_state = LaserState.ON - laser_state

                # Check whether we're doing black and white only mode
                if colour_mode_bw:
                    if laser_state >= bw_threshold:
                        laser_state = laser_power_max
                    else:
                        laser_state = laser_power_min

                laser_state = int(scale(laser_state, [0, 255], [laser_power_min, laser_power_max]))

                # Generate the physical position of each pixel
                pixel_start_x_pos = mm_per_pixel * col
                if pass_direction == PassDirection.RIGHT_TO_LEFT:
                    pixel_start_x_pos += mm_per_pixel

                if previous_laser_state != laser_state:

                    # If the laser was off and the distance travelled with it off is greater than rapid_min_distance
                    move_distance = abs(pixel_start_x_pos - laser_last_x_pos)
                    if previous_laser_state == laser_power_min and move_distance > rapid_min_distance:
                        gcode_file.add_line(MoveRapid(pixel_start_x_pos, None, None, feedrate_rapid))
                    else:
                        gcode_file.add_line(MoveFeed(pixel_start_x_pos, None, None, feedrate_lase))

                    laser_last_x_pos = pixel_start_x_pos

                    # Enable or disable the laser, depending on the pixel colour and whether we're inverting
                    gcode_file.add_line(SetToolState(laser_state))

                    previous_laser_state = laser_state

            if pass_direction == PassDirection.LEFT_TO_RIGHT:
                pass_end_pos = pixel_start_x_pos + mm_per_pixel
            else:
                pass_end_pos = pixel_start_x_pos - mm_per_pixel

            # Turn off the tool at the end of each pass
            if laser_state != laser_power_min:
                gcode_file.add_line(MoveFeed(pass_end_pos, None, None, feedrate_lase))
                gcode_file.add_line(SetToolState(ToolState.OFF))

    # Shift the file if necessary
    if not (offset_x == 0 or offset_y == 0 or offset_z == 0):
        gcode_file.translate(offset_x, offset_y, offset_y)

    return gcode_file


class PassDirection:
    LEFT_TO_RIGHT, RIGHT_TO_LEFT = range(2)


class LaserState:
    OFF = 0
    ON = 255


from machines import machine, marlin

machine_instance = marlin.Marlin()
machine_instance = machine.BaseMachine()

# Setup command line parameters
parser = argparse.ArgumentParser(description='Generate laser engraving G-Code from a bitmap image.')
parser.add_argument('--src', type=str, dest='source_image', help='The source image')
parser.add_argument('--out', type=str, dest='output_file', help='The output file. Leave blank to write to console')
parser.add_argument('--feedrate-lase', type=int, dest='feedrate_lase', default=1000,
                    help='Feedrate when lasing')
parser.add_argument('--feedrate-rapid', type=int, dest='feedrate_rapid', default=2000,
                    help='Feedrate when moving between lased areas')
parser.add_argument('--rapid-min-distance', type=int, dest='rapid_min_distance', default=0,
                    help='Minimum distance moved that will generate a rapid. Otherwise a normal speed move is used.')
parser.add_argument('--dimension-width', type=int, dest='dimension_width', default=None,
                    help='The desired output width in mm. Output will have same aspect ratio as input image')
parser.add_argument('--dimension-height', type=int, dest='dimension_height', default=None,
                    help='The desired output height in mm. Output will have same aspect ratio as input image')
parser.add_argument('--mm-per-pass', type=int, dest='mm_per_pass', default=0.1,
                    help='The distance between each pass (in mm)')
parser.add_argument('--invert', dest='invert', default=False, action="store_true",
                    help='The output file. Leave blank to write to console')
parser.add_argument('--laser-power-min', type=int, dest='laser_power_min', default=100,
                    help='Minimum laser power')
parser.add_argument('--laser-power-max', type=int, dest='laser_power_max', default=255,
                    help='Maximum laser power')
parser.add_argument('--colour-mode-bw', dest='colour_mode_bw', default=False, action="store_true",
                    help='Use Black or white mode, rather than grayscale')
parser.add_argument('--colour-mode-bw-threshold', type=int, dest='bw_threshold', default=125,
                    help='Grayscale threshold for black or white lasing')
parser.add_argument('--offset-x', type=float, dest='offset_x', default=0,
                    help='How far from the origin should the lasing start (x distance)')
parser.add_argument('--offset-y', type=float, dest='offset_y', default=0,
                    help='How far from the origin should the lasing start (y distance)')
parser.add_argument('--offset-z', type=float, dest='offset_z', default=0,
                    help='How far from the origin should the lasing start (z distance)')
parser.add_argument('--json-config', type=str, dest='json_config', default=None,
                    help='Supply configuration as a JSON encoded object. Each argument is represented by a key')

# Parse command line arguments
args = parser.parse_args()
args_as_dict = vars(args)
output_file = args_as_dict.pop("output_file", None)
json_config_str = args_as_dict.pop("json_config", None)

if json_config_str is not None:
    json_args = json.loads(json_config_str)
    args_as_dict.update(json_args)

import pprint
pprint.pprint(args_as_dict)

from datetime import datetime

startTime = datetime.now()
scriptStartTime = startTime

src_image = Image.open(args.source_image).convert('LA')

print "Loading image took: {}".format(datetime.now() - startTime)
startTime = datetime.now()

# TODO: min / max laser power

args_as_dict["source_image"] = src_image

resultant_gcode = bitmap_to_laser(**args_as_dict)

print "Generating GCode commands took: {}".format(datetime.now() - startTime)
startTime = datetime.now()

output_gcode = resultant_gcode.output(machine_instance)

print "Generating GCode file took: {}".format(datetime.now() - startTime)
startTime = datetime.now()

print resultant_gcode.bounding_box

try:
    with open(output_file, "w+") as output:
        output.write(output_gcode)
except TypeError:
    sys.stdout.write(output_gcode)

print "Writing GCode file took: {}".format(datetime.now() - startTime)
print "Script took: {}".format(datetime.now() - scriptStartTime)
