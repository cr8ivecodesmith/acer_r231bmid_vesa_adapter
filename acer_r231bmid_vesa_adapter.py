from pathlib import Path

from solid import (
    # Objects
    part,
    cube,
    polygon,
    cylinder,

    # Transformations
    hull,
    rotate,
    translate,
    linear_extrude,

    # Operations
    union,
    difference,

    # Utils
    scad_render_to_file,
)


# ### Configuration ###
SCAD_OUT = f'{Path(__file__).stem}.scad'
FRAGMENTS = 32

SHOW_MONITOR_MOUNT = False
SHOW_VESA_MOUNT = True

# Distance of the vesa holes typical are 75 100 or 200
VESA = 100

# General material thickness of the monitor mount
THICKNESS = 3

# General material thickness of the vesa mount plate
PLATE_THICKNESS = 5

# Depth for the monitor mount part (smaller part)
# keep in mind that the shorter this part the less
# stress is going through this part
DEPTH = 50

# Mounting point between the 2 parts
H_OFFSET = 0

# Additional material width of vesa mount plate
# around the mounting holes
EXTRA_WIDTH = 5


def _mount_finger_t(thickness):
    """acer_mount Right and Left Finger Top

    """
    p = part()
    p.add(
        cube((8, thickness, 39.5))
    )
    p.add(translate((2.5, 0, 0))(
        cube((3, thickness, 42.7))
    ))
    return hull()(p)


def _mount_finger_mt(thickness):
    """acer_mount Middle Finger Top

    """
    p = part()
    p.add(cube((12, thickness, 35.75)))
    p.add(translate((0, -4.5, 35.75 - 2.05))(
        cube((12, 4.5, 2.05))
    ))
    return p


def _mount_strong_angle(thickness):
    p = part()

    h = 33.75
    h_cut = h - thickness
    for i in range(2):
        ob = polygon(
            points=(
                (0, 0),
                (h, 0),
                (0, DEPTH - thickness),
                (0, 0),
                (h_cut - thickness, 0),
                (0, DEPTH - thickness * 3)
            ),
            paths=(
                (0, 1, 2),
                (3, 4, 5)
            ),
            convexity=10
        )
        ob = linear_extrude(height=45)(ob)
        ob = rotate((180, -90, 0))(ob)
        ob = translate((0, -thickness, 0))(ob)
        ob = rotate((0, 0, 180 * i))(ob)
        ob = translate((i * 45, i * -DEPTH + 2.5, 0))(ob)

        p.add(ob)

    return p


def acer_mount(thickness: bool = 1):
    main_obj = part()

    # Part 1
    p1 = part()
    p1.add(translate((-45 / 2, 0, 0))(
        cube((45, DEPTH, thickness * 2))
    ))

    # Part 2
    p2 = part()

    # Part 2 Sub-parts
    p2_sub1 = part()
    p2_sub1_objs = [
        cube((45, thickness, 10.75)),
        translate((-4, 0, 3))(
            cube((53, thickness, 4)),
        ),
        # Right corner rounding
        translate((-0.25, 0, 7))(
            rotate((-90, 0, 0))(
                cylinder(d=7.55, h=thickness)
            )
        ),
        # Left corner rounding
        translate((46-0.75, 0, 7))(
            rotate((-90, 0, 0))(
                cylinder(d=7.55, h=thickness)
            )
        ),
        # Middle part
        translate((0, -thickness, 0))(
            cube((45, 2 * thickness, 33.7)),
        ),
        # Right finger top
        translate((5.5, 0, 0))(
            _mount_finger_t(thickness)
        ),
        # Middle finger top
        translate((16.5, 0, 0))(
            _mount_finger_mt(thickness)
        ),
        # Left Finger Top
        translate((31.5, 0, 0))(
            _mount_finger_t(thickness)
        ),
        # Stronger angle part
        _mount_strong_angle(thickness),
        # Mount plate
        translate((0, thickness - DEPTH, -17))(
            cube((45, thickness * 2, 58))
        ),
    ]
    p2_sub1.add(union()(p2_sub1_objs))

    p2_sub2 = translate((13.5, -thickness, 8))(
        cube((18, 2 * thickness, 8))
    )

    # Put Part 2 together
    p2.add(difference()((
        p2_sub1,
        p2_sub2
    )))
    p2 = translate((0, DEPTH - thickness, 5))(p2)
    p2 = translate((-45 / 2, 0, 0))(p2)

    # Put the main object together
    main_obj.add((p1, p2))

    return main_obj


def vesa_holes(
    thickness,
    screw_holes_d: bool = 5,
    holes_distance: bool = 100
):
    holes = part()
    for x in range(2):
        for y in range(2):
            ob = cylinder(d=screw_holes_d, h=thickness)
            ob = translate((
                holes_distance / 2 - x * holes_distance,
                holes_distance - y * holes_distance,
                -thickness
            ))(ob)
            holes.add(ob)
    holes = rotate((90, 0, 0))(holes)
    return holes


def vesa_mount(
    thickness,
    screw_holes_d: bool = 5,
    holes_distance: bool = 100
):
    w = holes_distance + EXTRA_WIDTH

    p1 = union()((
        hull()(vesa_holes(
            screw_holes_d=10,
            holes_distance=holes_distance + EXTRA_WIDTH,
            thickness=thickness
        )),
        translate((-45 / 2, 0, 0))(
            cube((45, thickness, H_OFFSET + w))
        ),
    ))
    p2 = translate((0, -1, H_OFFSET))(vesa_holes(
        screw_holes_d=screw_holes_d,
        holes_distance=holes_distance,
        thickness=thickness + 2
    ))

    return difference()((p1, p2))


def main():
    ob = part()

    mount_plate = []

    if SHOW_MONITOR_MOUNT:
        # The acer mount
        mount_plate.append(acer_mount(thickness=THICKNESS))

    if SHOW_VESA_MOUNT:
        # The vesa interface
        plate = vesa_mount(
            holes_distance=VESA,
            thickness=PLATE_THICKNESS
        )
        plate = translate((0, -THICKNESS * 2 - 10, -12))(plate)
        mount_plate.append(plate)

    mount_plate = union()(mount_plate)

    # Screw holes between parts
    holes = []
    for x in (-15, 15):
        for y in (-8, 42):
            hole = cylinder(d=3, h=30)
            hole = rotate((90, 0))(hole)
            hole = translate((x, 10, y))(hole)
            holes.append(hole)
    holes = union()(holes)

    # Put them all together
    ob.add(mount_plate - holes)

    return ob


if __name__ == '__main__':
    scad_render_to_file(
        main(), filepath=SCAD_OUT, file_header=f'$fn = {FRAGMENTS};'
    )
