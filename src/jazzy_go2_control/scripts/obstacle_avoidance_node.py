#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from std_msgs.msg import String

class ObstacleAvoidanceNode(Node):
    def __init__(self):
        super().__init__('obstacle_avoidance_node')
        self.get_logger().info("Obstacle Avoidance Node Started")
        
        # Parameters
        self.declare_parameter('mode', 'autonomous') # 'autonomous' or 'llm'
        self.declare_parameter('threshold', 0.5) # meters
        
        self.mode = self.get_parameter('mode').get_parameter_value().string_value
        self.threshold = self.get_parameter('threshold').get_parameter_value().double_value
        
        # Subscription to lidar
        self.subscription = self.create_subscription(
            LaserScan,
            '/scan',
            self.scan_callback,
            10)
            
        # Publisher for direct commands (autonomous mode)
        self.cmd_pub = self.create_publisher(String, 'go_command', 10)
        
        # Publisher for LLM data (llm mode)
        self.llm_pub = self.create_publisher(String, 'manus_data', 10)
        
        self.last_llm_time = self.get_clock().now()
        
    def scan_callback(self, msg):
        # Calculate minimum distance from ranges, ignoring inf and zero
        valid_ranges = [r for r in msg.ranges if r > 0.01 and r < float('inf')]
        if not valid_ranges:
            return
            
        r = min(valid_ranges)
        min_distance = r
        
        if self.mode == 'autonomous':
            out_msg = String()
            if min_distance < self.threshold:
                out_msg.data = "stop, rotate right" # Basic avoidance action
                self.get_logger().info(f"Obstacle detected at {min_distance:.2f}m. Autonomous action: {out_msg.data}")
            else:
                out_msg.data = "go forward"
                
            self.cmd_pub.publish(out_msg)
            
        elif self.mode == 'llm':
            # Throttle LLM requests to once every 5 seconds
            current_time = self.get_clock().now()
            if (current_time - self.last_llm_time).nanoseconds > 5e9:
                out_msg = String()
                out_msg.data = f"Lidar sensor reports the nearest obstacle is at {min_distance:.2f} meters. The safe threshold is {self.threshold} meters. Should I 'go forward', 'stop', or 'rotate right'?"
                self.llm_pub.publish(out_msg)
                self.get_logger().info(f"Sent lidar data to LLM: min_distance={min_distance:.2f}m")
                self.last_llm_time = current_time

def main(args=None):
    rclpy.init(args=args)
    node = ObstacleAvoidanceNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()

if __name__ == '__main__':
    main()
