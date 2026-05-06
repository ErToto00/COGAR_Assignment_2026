import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class JazzyUR5eControlNode(Node):
    def __init__(self):
        super().__init__('jazzy_ur5e_control_node')
        self.subscription = self.create_subscription(
            String,
            'input_string',
            self.listener_callback,
            10)
        self.subscription  # prevent unused variable warning

    def listener_callback(self, msg):
        if msg.data == "grasp":
            self.get_logger().info('Activating gripper...')
            # Add code to activate the robot gripper here
        else:
            self.get_logger().info(f'Received string: {msg.data}')

def main(args=None):
    rclpy.init(args=args)
    jazzy_ur5e_control_node = JazzyUR5eControlNode()
    rclpy.spin(jazzy_ur5e_control_node)
    jazzy_ur5e_control_node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
