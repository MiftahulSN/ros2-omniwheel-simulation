#!/usr/bin/env python3
import curses
import os
import sys
import time

import rclpy
from geometry_msgs.msg import Twist

LIN_MAX = 2.0
ANG_MAX = 4.0
KEY_TIMEOUT = 0.5
RAMP_RATE = 8.0

HELP_LINES = [
    '-------------------------------------------',
    '  Omni-Wheel Teleop  (WASD + QE layout)',
    '-------------------------------------------',
    '  Hold key to move, release to stop.',
    '',
    '  W / S  : forward / backward',
    '  A / D  : strafe left / strafe right',
    '  Q / E  : rotate left / rotate right',
    '',
    '  C / Z  : increase / decrease linear speed',
    '  V / X  : increase / decrease angular speed',
    '',
    '  Space  : emergency stop',
    '  Ctrl+C : quit',
    '-------------------------------------------',
]

MOVEMENT_KEYS = {
    ord('w'): ('linear_x', +1),
    ord('s'): ('linear_x', -1),
    ord('a'): ('linear_y', +1),
    ord('d'): ('linear_y', -1),
    ord('q'): ('angular_z', +1),
    ord('e'): ('angular_z', -1),
}


def clamp(value, lo, hi):
    return max(lo, min(hi, value))


def ramp(current, target, rate, dt):
    if target > current:
        return min(target, current + rate * dt)
    elif target < current:
        return max(target, current - rate * dt)
    return target


def _draw_speed(stdscr, row, lin_speed, ang_speed):
    text = f'  linear speed : {lin_speed:5.2f} m/s   angular speed : {ang_speed:5.2f} rad/s'
    stdscr.move(row, 0)
    stdscr.clrtoeol()
    stdscr.addstr(row, 2, text)
    stdscr.refresh()


def _loop(stdscr, pub):
    lin_speed = 0.5
    ang_speed = 1.0
    active_keys = {}
    current_x = 0.0
    current_y = 0.0
    current_w = 0.0

    stdscr.nodelay(True)
    curses.curs_set(0)
    stdscr.clear()

    row = 1
    for line in HELP_LINES:
        stdscr.addstr(row, 2, line)
        row += 1
    row += 1

    speed_row = row
    _draw_speed(stdscr, speed_row, lin_speed, ang_speed)
    stdscr.refresh()

    last_time = time.monotonic()

    while True:
        now = time.monotonic()
        dt = now - last_time
        last_time = now

        expired = [k for k, t in active_keys.items() if now - t > KEY_TIMEOUT]
        for k in expired:
            del active_keys[k]

        key = stdscr.getch()
        if key == 3:
            break
        elif key != -1 and key in MOVEMENT_KEYS:
            active_keys[key] = now
        elif key == ord(' '):
            active_keys.clear()
        elif key == ord('c'):
            lin_speed = clamp(lin_speed + 0.1, 0.1, LIN_MAX)
            _draw_speed(stdscr, speed_row, lin_speed, ang_speed)
        elif key == ord('z'):
            lin_speed = clamp(lin_speed - 0.1, 0.1, LIN_MAX)
            _draw_speed(stdscr, speed_row, lin_speed, ang_speed)
        elif key == ord('v'):
            ang_speed = clamp(ang_speed + 0.2, 0.2, ANG_MAX)
            _draw_speed(stdscr, speed_row, lin_speed, ang_speed)
        elif key == ord('x'):
            ang_speed = clamp(ang_speed - 0.2, 0.2, ANG_MAX)
            _draw_speed(stdscr, speed_row, lin_speed, ang_speed)

        target_x = 0.0
        target_y = 0.0
        target_w = 0.0

        for held_key in active_keys:
            axis, sign = MOVEMENT_KEYS[held_key]
            if axis == 'linear_x':
                target_x += sign * lin_speed
            elif axis == 'linear_y':
                target_y += sign * lin_speed
            elif axis == 'angular_z':
                target_w += sign * ang_speed

        target_x = clamp(target_x, -LIN_MAX, LIN_MAX)
        target_y = clamp(target_y, -LIN_MAX, LIN_MAX)
        target_w = clamp(target_w, -ANG_MAX, ANG_MAX)

        current_x = ramp(current_x, target_x, RAMP_RATE, dt)
        current_y = ramp(current_y, target_y, RAMP_RATE, dt)
        current_w = ramp(current_w, target_w, RAMP_RATE, dt)

        if abs(target_x) < 0.001 and abs(current_x) < 0.01:
            current_x = 0.0
        if abs(target_y) < 0.001 and abs(current_y) < 0.01:
            current_y = 0.0
        if abs(target_w) < 0.001 and abs(current_w) < 0.01:
            current_w = 0.0

        twist = Twist()
        twist.linear.x = current_x
        twist.linear.y = current_y
        twist.angular.z = current_w
        pub.publish(twist)

        time.sleep(0.02)


def main():
    os.environ['RCUTILS_LOGGING_DEFAULT_LEVEL'] = 'RCUTILS_LOG_SEVERITY_FATAL'
    _log = open(os.devnull, 'w')
    _orig_stderr = sys.stderr
    sys.stderr = _log

    rclpy.init()
    node = rclpy.create_node('omni_teleop')
    pub = node.create_publisher(Twist, 'cmd_vel', 10)

    try:
        curses.wrapper(_loop, pub)
    finally:
        pub.publish(Twist())
        node.destroy_node()
        rclpy.shutdown()
        sys.stderr = _orig_stderr
        _log.close()


if __name__ == '__main__':
    main()
