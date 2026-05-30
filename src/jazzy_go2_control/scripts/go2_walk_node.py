#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

# Try importing the official Unitree SDK
try:
    from unitree_sdk2py.core.channel import ChannelFactory
    from unitree_sdk2py.go2.sport.sport_client import SportClient
    HAS_UNITREE_SDK = True
except ImportError:
    HAS_UNITREE_SDK = False

class Go2WalkNode(Node):
    def __init__(self):
        super().__init__('go2_walk_node')
        self.get_logger().info("Go2 Walk Node Started.")
        
        # Subscribe to a command topic
        self.subscription = self.create_subscription(
            String,
            'go_command',
            self.command_callback,
            10)
        
        self.sport_client = None
        if HAS_UNITREE_SDK:
            try:
                # Initialize network channel (0 typically defaults to the primary interface)
                ChannelFactory.Instance().Init(0, "")
                self.sport_client = SportClient()
                self.sport_client.SetTimeout(10.0)
                self.sport_client.Init()
                self.get_logger().info("Unitree Go2 SportClient initialized successfully.")
            except Exception as e:
                self.get_logger().error(f"Failed to initialize SportClient: {e}")
        else:
            self.get_logger().warning("unitree_sdk2py not found. Node will simulate SDK calls.")

    def stop(self):
        self.get_logger().info('Stopping the robot.')
        if self.sport_client:
            self.sport_client.Move(0.0, 0.0, 0.0)
        else:
            self.get_logger().info('[Simulated SDK] Stopping (v_x=0.0, v_y=0.0, v_yaw=0.0)')

    def rotate(self, direction):
        self.get_logger().info(f'Rotating the robot {direction}.')
        # vyaw: positive for counter-clockwise, negative for clockwise
        if direction == 'cw':
            vyaw = -0.5
        elif direction == 'ccw':
            vyaw = 0.5
        else:
            self.get_logger().warning(f'Unknown rotation direction: {direction}')
            return

        if self.sport_client:
            self.sport_client.Move(0.0, 0.0, vyaw)
        else:
            self.get_logger().info(f'[Simulated SDK] Rotating (v_yaw={vyaw})')

    def command_callback(self, msg):
        command = msg.data.strip().lower()
        parts = command.split()
        if not parts:
            return

        action = parts[0]

        if action == 'go':
            self.get_logger().info('Received "go" command, making the robot walk straight forward.')
            if self.sport_client:
                # Move(vx, vy, vyaw)
                # vx: forward velocity in m/s
                self.sport_client.Move(0.3, 0.0, 0.0)
            else:
                self.get_logger().info('[Simulated SDK] Walking straight forward (v_x=0.3)')
        elif action == 'stop':
            self.stop()
        elif action == 'rotate':
            if len(parts) > 1:
                direction = parts[1]
                self.rotate(direction)
            else:
                self.get_logger().warning('Rotate command missing direction (cw or ccw).')
        else:
            self.get_logger().info(f'Received unknown command: "{command}"')

def main(args=None):
    rclpy.init(args=args)
    node = Go2WalkNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()

if __name__ == '__main__':
    main()
