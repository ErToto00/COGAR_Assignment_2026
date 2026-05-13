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

    def command_callback(self, msg):
        command = msg.data.strip().lower()
        if command == 'go':
            self.get_logger().info('Received "go" command, making the robot walk straight forward.')
            if self.sport_client:
                # Move(vx, vy, vyaw)
                # vx: forward velocity in m/s
                self.sport_client.Move(0.3, 0.0, 0.0)
            else:
                self.get_logger().info('[Simulated SDK] Walking straight forward (v_x=0.3)')
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
