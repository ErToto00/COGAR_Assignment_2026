import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from std_srvs.srv import SetBool

class JazzyUR5eControlNode(Node):
    def __init__(self):
        super().__init__('jazzy_ur5e_control_node')
        self.subscription = self.create_subscription(
            String,
            'input_string',
            self.listener_callback,
            10)
        self.subscription  # prevent unused variable warning

        # Create a client to the gripper control service
        self.gripper_client = self.create_client(SetBool, '/ur5e/gripper_control')

    def listener_callback(self, msg):
        if msg.data == "grasp":
            self.get_logger().info('Activating gripper...')
            self.activate_gripper()
        else:
            self.get_logger().info(f'Received string: {msg.data}')

    def activate_gripper(self):
        while not self.gripper_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Service not available, waiting again...')
        request = SetBool.Request()
        request.data = True
        future = self.gripper_client.call_async(request)
        future.add_done_callback(self.gripper_response_callback)

    def gripper_response_callback(self, future):
        try:
            response = future.result()
            if response.success:
                self.get_logger().info('Gripper activated successfully.')
            else:
                self.get_logger().error('Failed to activate gripper.')
        except Exception as e:
            self.get_logger().error(f'Service call failed: {e}')

def main(args=None):
    rclpy.init(args=args)
    jazzy_ur5e_control_node = JazzyUR5eControlNode()
    rclpy.spin(jazzy_ur5e_control_node)
    jazzy_ur5e_control_node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
