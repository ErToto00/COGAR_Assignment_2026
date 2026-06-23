#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import Twist
import time
import threading
import math

# Try importing the official Unitree SDK
try:
    from unitree_sdk2py.core.channel import ChannelFactoryInitialize
    from unitree_sdk2py.go2.sport.sport_client import SportClient
    HAS_UNITREE_SDK = True
except ImportError:
    HAS_UNITREE_SDK = False

class MovementNode(Node):
    def __init__(self):
        super().__init__('movement_node')
        self.get_logger().info("Go2 Walk Node Started.")
        
        # Subscribe to a command topic
        self.subscription = self.create_subscription(
            String,
            'go_command',
            self.command_callback,
            10)
            
        # Publisher for Gazebo simulation
        self.cmd_vel_pub = self.create_publisher(Twist, 'cmd_vel', 10)
        
        self.sport_client = None
        if HAS_UNITREE_SDK:
            try:
                # Initialize network channel (0 typically defaults to the primary interface)
                ChannelFactoryInitialize(0, "")
                self.sport_client = SportClient()
                self.sport_client.SetTimeout(10.0)
                self.sport_client.Init()
                self.get_logger().info("Unitree Go2 SportClient initialized successfully.")
            except Exception as e:
                self.get_logger().error(f"Failed to initialize SportClient: {e}")
        else:
            self.get_logger().warning("unitree_sdk2py not found. Node will simulate SDK calls.")
            
        self.action_queue = []
        self.lock = threading.Lock()
        self.executor_thread = threading.Thread(target=self.execute_commands_loop, daemon=True)
        self.executor_thread.start()

    def set_velocity(self, vx, vy, vyaw):
        if self.sport_client:
            self.sport_client.Move(vx, vy, vyaw)
        else:
            self.get_logger().info(f'[Simulated SDK] Move(vx={vx}, vy={vy}, vyaw={vyaw})')
            
        # Also publish to cmd_vel for Gazebo
        twist = Twist()
        twist.linear.x = float(vx)
        twist.linear.y = float(vy)
        twist.angular.z = float(vyaw)
        self.cmd_vel_pub.publish(twist)

    def execute_commands_loop(self):
        while rclpy.ok():
            command = None
            with self.lock:
                if self.action_queue:
                    command = self.action_queue.pop(0)
            
            if command:
                self.get_logger().info(f"Executing step: {command}")
                cmd = command.strip()
                if cmd == 'stop':
                    self.set_velocity(0.0, 0.0, 0.0)
                    time.sleep(1.0) # Small delay for stop to settle
                elif cmd == 'go forward' or cmd == 'forward' or cmd == 'go':
                    self.set_velocity(0.3, 0.0, 0.0)
                elif cmd == 'go back' or cmd == 'back':
                    self.set_velocity(-0.3, 0.0, 0.0)
                elif 'rotate' in cmd:
                    # 90 degrees rotation (pi/2 radians) at 0.5 rad/s takes ~3.14s
                    rot_speed = 0.5
                    duration = (math.pi / 2.0) / rot_speed
                    if 'left' in cmd or 'ccw' in cmd:
                        self.set_velocity(0.0, 0.0, rot_speed)
                    elif 'right' in cmd or 'cw' in cmd:
                        self.set_velocity(0.0, 0.0, -rot_speed)
                    else:
                        self.set_velocity(0.0, 0.0, rot_speed) # default
                    
                    # Wait for 90 deg rotation to complete
                    time.sleep(duration)
                    # Stop after rotation completes
                    self.set_velocity(0.0, 0.0, 0.0)
                else:
                    self.get_logger().warning(f"Unknown sub-command: {cmd}")
            else:
                time.sleep(0.1)

    def command_callback(self, msg):
        command = msg.data.strip().strip("'\"").lower()
        self.get_logger().info(f'Received full command sequence: "{command}"')
        
        # Split by comma to support sequences like "stop, rotate left, go forward"
        parts = [p.strip() for p in command.split(',') if p.strip()]
        
        with self.lock:
            # Clear existing queue if a new command arrives
            self.action_queue = parts
            # If the first command is not 'stop', force a stop first? Let's leave exactly as requested

def main(args=None):
    rclpy.init(args=args)
    node = MovementNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()

if __name__ == '__main__':
    main()
