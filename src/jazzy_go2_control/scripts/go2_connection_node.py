#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

# Try importing the official Unitree SDK
try:
    from unitree_sdk2py.core.channel import ChannelFactoryInitialize
    from unitree_sdk2py.go2.sport.sport_client import SportClient
    HAS_UNITREE_SDK = True
except ImportError:
    HAS_UNITREE_SDK = False

class Go2ConnectionNode(Node):
    def __init__(self):
        super().__init__('go2_connection_node')
        self.get_logger().info("Go2 Connection Node Started.")
        
        # Subscribe to the commands published by the llm_node
        self.subscription = self.create_subscription(
            String,
            'go_command',
            self.command_callback,
            10)
        
        self.sport_client = None
        if HAS_UNITREE_SDK:
            try:
                # Initialize network channel
                ChannelFactoryInitialize(0, "")
                self.sport_client = SportClient()
                self.sport_client.SetTimeout(10.0)
                self.sport_client.Init()
                self.get_logger().info("Unitree Go2 SportClient initialized successfully.")
            except Exception as e:
                self.get_logger().error(f"Failed to initialize SportClient: {e}")
        else:
            self.get_logger().warning("unitree_sdk2py not found. Node will simulate SDK calls.")

    def stop(self):
        self.get_logger().info('Action: Stopping the robot.')
        if self.sport_client:
            try:
                self.sport_client.Move(0.0, 0.0, 0.0)
            except Exception as e:
                self.get_logger().error(f"Failed to execute stop: {e}")
        else:
            self.get_logger().info('[Simulated SDK] Stop (v_x=0.0, v_y=0.0, v_yaw=0.0)')

    def rotate(self, direction):
        self.get_logger().info(f'Action: Rotating the robot {direction}.')
        if direction == 'cw':
            vyaw = -0.5
        elif direction == 'ccw':
            vyaw = 0.5
        else:
            self.get_logger().warning(f'Unknown rotation direction: {direction}')
            return

        if self.sport_client:
            try:
                self.sport_client.Move(0.0, 0.0, vyaw)
            except Exception as e:
                self.get_logger().error(f"Failed to execute rotate: {e}")
        else:
            self.get_logger().info(f'[Simulated SDK] Rotate (v_yaw={vyaw})')

    def walk_forward(self):
        self.get_logger().info('Action: Walking forward.')
        if self.sport_client:
            try:
                self.sport_client.Move(0.3, 0.0, 0.0)
            except Exception as e:
                self.get_logger().error(f"Failed to execute walk forward: {e}")
        else:
            self.get_logger().info('[Simulated SDK] Walk forward (v_x=0.3)')

    def dance(self):
        self.get_logger().info('Action: Performing a dance / stretch.')
        if self.sport_client:
            try:
                # Use Stretch or other fun moves
                if hasattr(self.sport_client, 'Stretch'):
                    self.sport_client.Stretch()
                else:
                    # Fallback to a sequence or Move
                    self.sport_client.Move(0.0, 0.0, 0.3)
                    import time
                    time.sleep(1.0)
                    self.sport_client.Move(0.0, 0.0, -0.3)
            except Exception as e:
                self.get_logger().error(f"Failed to execute dance: {e}")
        else:
            self.get_logger().info('[Simulated SDK] Dance / Stretch performed.')

    def command_callback(self, msg):
        command = msg.data.strip().strip("'\"").lower()
        self.get_logger().info(f"Received command from LLM: '{command}'")
        
        parts = command.split()
        if not parts:
            return

        action = parts[0]

        if action == 'go' or action == 'walk':
            self.walk_forward()
        elif action == 'stop':
            self.stop()
        elif action == 'rotate':
            direction = parts[1] if len(parts) > 1 else 'cw'
            self.rotate(direction)
        elif action == 'dance':
            self.dance()
        else:
            self.get_logger().warning(f"Unknown action: '{action}'. Defaulting to stop.")
            self.stop()

def main(args=None):
    rclpy.init(args=args)
    node = Go2ConnectionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()

if __name__ == '__main__':
    main()
