#!/usr/bin/env python3
import subprocess

import rclpy
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Joy

LIN_MAX = 2.0
ANG_MAX = 4.0
RAMP_RATE = 8.0
DEADZONE = 0.15
AXIS_LIN_X = 3
AXIS_LIN_Y = 2
AXIS_ANG_Z = 0
BTN_LIN_SPEED_UP = 5
BTN_LIN_SPEED_DOWN = 4
BTN_ANG_SPEED_UP = 7
BTN_ANG_SPEED_DOWN = 6
BTN_ENABLE = 9
BTN_RESPAWN = 8


class TeleopJoy:
    def __init__(self, node):
        self.node = node
        self.lin_speed = 0.5
        self.ang_speed = 1.0
        self.current_x = 0.0
        self.current_y = 0.0
        self.current_w = 0.0
        self.enabled = True
        self.last_time = node.get_clock().now()
        self._joy_received = False
        self._prev_buttons = []

        node.declare_parameter('world', 'maze2')
        node.declare_parameter('spawn_z', 0.1)
        self.world = node.get_parameter('world').value
        self.spawn_z = node.get_parameter('spawn_z').value

        self.pub = node.create_publisher(Twist, 'cmd_vel', 10)
        self.sub = node.create_subscription(Joy, 'joy', self._joy_callback, 10)

        node.get_logger().info(
            f'Teleop Joy ready | axes: lin_x={AXIS_LIN_X} lin_y={AXIS_LIN_Y} ang_z={AXIS_ANG_Z}'
            f' | btns: lin+={BTN_LIN_SPEED_UP} lin-={BTN_LIN_SPEED_DOWN}'
            f' ang+={BTN_ANG_SPEED_UP} ang-={BTN_ANG_SPEED_DOWN}'
            f' enable={BTN_ENABLE} respawn={BTN_RESPAWN}'
        )

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

    @staticmethod
    def _apply_deadzone(val, deadzone):
        if abs(val) < deadzone:
            return 0.0
        return val

    def _button_pressed(self, msg, index):
        if len(msg.buttons) <= index or len(self._prev_buttons) <= index:
            return False
        return msg.buttons[index] and not self._prev_buttons[index]

    def _respawn(self):
        self.pub.publish(Twist())
        self.current_x = 0.0
        self.current_y = 0.0
        self.current_w = 0.0
        try:
            subprocess.Popen([
                'ign', 'service',
                '-s', f'/world/{self.world}/set_pose',
                '--reqtype', 'ignition.msgs.Pose',
                '--reptype', 'ignition.msgs.Boolean',
                '--timeout', '1000',
                '--req', (
                    f'name: "omni_robot" '
                    f'position: {{x: 0, y: 0, z: {self.spawn_z}}} '
                    f'orientation: {{x: 0, y: 0, z: 0, w: 1}}'
                ),
            ])
            self.node.get_logger().info('Robot respawned')
        except FileNotFoundError:
            self.node.get_logger().error("'ign' command not found, cannot respawn")

    def _compute_dt(self):
        now = self.node.get_clock().now()
        dt = (now - self.last_time).nanoseconds / 1e9
        self.last_time = now
        if dt <= 0.0 or dt > 0.5:
            dt = 0.02
        return dt

    def _handle_buttons(self, msg):
        if self._button_pressed(msg, BTN_ENABLE):
            self.enabled = not self.enabled
            state = 'ENABLED' if self.enabled else 'DISABLED'
            self.node.get_logger().info(f'Joystick {state}')
            if not self.enabled:
                self._reset_velocity()

        if not self.enabled:
            self._prev_buttons = list(msg.buttons)
            return False

        if self._button_pressed(msg, BTN_LIN_SPEED_UP):
            self.lin_speed = self._clamp(self.lin_speed + 0.1, 0.1, LIN_MAX)
            self.node.get_logger().info(f'linear: {self.lin_speed:.2f} m/s')
        if self._button_pressed(msg, BTN_LIN_SPEED_DOWN):
            self.lin_speed = self._clamp(self.lin_speed - 0.1, 0.1, LIN_MAX)
            self.node.get_logger().info(f'linear: {self.lin_speed:.2f} m/s')
        if self._button_pressed(msg, BTN_ANG_SPEED_UP):
            self.ang_speed = self._clamp(self.ang_speed + 0.2, 0.2, ANG_MAX)
            self.node.get_logger().info(f'angular: {self.ang_speed:.2f} rad/s')
        if self._button_pressed(msg, BTN_ANG_SPEED_DOWN):
            self.ang_speed = self._clamp(self.ang_speed - 0.2, 0.2, ANG_MAX)
            self.node.get_logger().info(f'angular: {self.ang_speed:.2f} rad/s')
        if self._button_pressed(msg, BTN_RESPAWN):
            self._respawn()

        self._prev_buttons = list(msg.buttons)
        return True

    def _update_velocity(self, msg, dt):
        lin_x = self._apply_deadzone(msg.axes[AXIS_LIN_X], DEADZONE) if len(msg.axes) > AXIS_LIN_X else 0.0
        lin_y = self._apply_deadzone(msg.axes[AXIS_LIN_Y], DEADZONE) if len(msg.axes) > AXIS_LIN_Y else 0.0
        ang_z = self._apply_deadzone(msg.axes[AXIS_ANG_Z], DEADZONE) if len(msg.axes) > AXIS_ANG_Z else 0.0

        target_x = self._clamp(lin_x * self.lin_speed, -LIN_MAX, LIN_MAX)
        target_y = self._clamp(lin_y * self.lin_speed, -LIN_MAX, LIN_MAX)
        target_w = self._clamp(ang_z * self.ang_speed, -ANG_MAX, ANG_MAX)

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

    def _reset_velocity(self):
        self.current_x = 0.0
        self.current_y = 0.0
        self.current_w = 0.0
        self.pub.publish(Twist())

    def _joy_callback(self, msg):
        if not self._joy_received:
            self.node.get_logger().info(
                f'First joy message received: {len(msg.axes)} axes, {len(msg.buttons)} buttons'
            )
            self._joy_received = True

        dt = self._compute_dt()

        if not self._handle_buttons(msg):
            return

        self._update_velocity(msg, dt)

    def stop(self):
        self.pub.publish(Twist())


def main(args=None):
    rclpy.init(args=args)
    node = rclpy.create_node('teleop_joy')
    teleop = TeleopJoy(node)

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        teleop.stop()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
