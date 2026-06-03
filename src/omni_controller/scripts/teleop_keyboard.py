#!/usr/bin/env python3
import curses
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


class TeleopKeyboard:
    def __init__(self, node):
        self.node = node
        self.lin_speed = 0.5
        self.ang_speed = 1.0
        self.current_x = 0.0
        self.current_y = 0.0
        self.current_w = 0.0

        self.pub = node.create_publisher(Twist, 'cmd_vel', 10)

    @staticmethod
    def _clamp(value, lo, hi):
        return max(lo, min(hi, value))

    @staticmethod
    def _ramp(current, target, rate, dt):
        if target > current:
            return min(target, current + rate * dt)
        elif target < current:
            return max(target, current - rate * dt)
        return target

    def _draw_speed(self, stdscr, row):
        text = f'  linear speed : {self.lin_speed:5.2f} m/s   angular speed : {self.ang_speed:5.2f} rad/s'
        stdscr.move(row, 0)
        stdscr.clrtoeol()
        stdscr.addstr(row, 2, text)
        stdscr.refresh()

    def _update_velocity(self, active_keys, dt):
        target_x = 0.0
        target_y = 0.0
        target_w = 0.0

        for held_key in active_keys:
            axis, sign = MOVEMENT_KEYS[held_key]
            if axis == 'linear_x':
                target_x += sign * self.lin_speed
            elif axis == 'linear_y':
                target_y += sign * self.lin_speed
            elif axis == 'angular_z':
                target_w += sign * self.ang_speed

        target_x = self._clamp(target_x, -LIN_MAX, LIN_MAX)
        target_y = self._clamp(target_y, -LIN_MAX, LIN_MAX)
        target_w = self._clamp(target_w, -ANG_MAX, ANG_MAX)

        self.current_x = self._ramp(self.current_x, target_x, RAMP_RATE, dt)
        self.current_y = self._ramp(self.current_y, target_y, RAMP_RATE, dt)
        self.current_w = self._ramp(self.current_w, target_w, RAMP_RATE, dt)

        if abs(target_x) < 0.001 and abs(self.current_x) < 0.01:
            self.current_x = 0.0
        if abs(target_y) < 0.001 and abs(self.current_y) < 0.01:
            self.current_y = 0.0
        if abs(target_w) < 0.001 and abs(self.current_w) < 0.01:
            self.current_w = 0.0

        twist = Twist()
        twist.linear.x = self.current_x
        twist.linear.y = self.current_y
        twist.angular.z = self.current_w
        self.pub.publish(twist)

    def _handle_key(self, key, speed_row, stdscr):
        if key == ord('c'):
            self.lin_speed = self._clamp(self.lin_speed + 0.1, 0.1, LIN_MAX)
            self._draw_speed(stdscr, speed_row)
        elif key == ord('z'):
            self.lin_speed = self._clamp(self.lin_speed - 0.1, 0.1, LIN_MAX)
            self._draw_speed(stdscr, speed_row)
        elif key == ord('v'):
            self.ang_speed = self._clamp(self.ang_speed + 0.2, 0.2, ANG_MAX)
            self._draw_speed(stdscr, speed_row)
        elif key == ord('x'):
            self.ang_speed = self._clamp(self.ang_speed - 0.2, 0.2, ANG_MAX)
            self._draw_speed(stdscr, speed_row)

    def _loop(self, stdscr):
        active_keys = {}

        stdscr.nodelay(True)
        curses.curs_set(0)
        stdscr.clear()

        row = 1
        for line in HELP_LINES:
            stdscr.addstr(row, 2, line)
            row += 1
        row += 1

        speed_row = row
        self._draw_speed(stdscr, speed_row)
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
            else:
                self._handle_key(key, speed_row, stdscr)

            self._update_velocity(active_keys, dt)
            time.sleep(0.02)

    def run(self):
        curses.wrapper(self._loop)

    def stop(self):
        self.pub.publish(Twist())


def main(args=None):
    rclpy.init(args=args)
    node = rclpy.create_node('teleop_keyboard')
    teleop = TeleopKeyboard(node)

    try:
        teleop.run()
    finally:
        teleop.stop()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
