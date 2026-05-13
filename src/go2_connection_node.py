#!/usr/bin/env python3
import rclpy
from rclpy.node import Node

class Go2ConnectionNode(Node):
    def __init__(self):
        super().__init__('go2_connection_node')
        self.get_logger().info("Go2 Connection Node Skeleton Started.")

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
