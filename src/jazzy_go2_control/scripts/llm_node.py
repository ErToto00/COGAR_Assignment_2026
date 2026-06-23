#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import requests
import threading

class LLMNode(Node):
    def __init__(self):
        super().__init__('llm_node')
        self.get_logger().info("LLM Node Started with Fused Context.")
        
        # Parameters
        self.declare_parameter('ollama_url', 'http://localhost:11434/api/generate')
        self.declare_parameter('model_name', 'qwen2.5-coder:7b')
        self.declare_parameter('llm_mode', 'simple')
        
        self.ollama_url = self.get_parameter('ollama_url').get_parameter_value().string_value
        self.model_name = self.get_parameter('model_name').get_parameter_value().string_value
        self.llm_mode = self.get_parameter('llm_mode').get_parameter_value().string_value
        
        # Subscriptions
        self.gesture_sub = self.create_subscription(
            String,
            'predicted_gesture',
            self.gesture_callback,
            10)
            
        self.lidar_sub = self.create_subscription(
            String,
            'lidar_context',
            self.lidar_callback,
            10)
        
        # Publisher
        self.publisher = self.create_publisher(
            String,
            'go_command',
            10)
        
        # Inference state
        self.is_processing = False
        self.latest_gesture = None
        self.latest_lidar = "No obstacles detected."
        self.lock = threading.Lock()

    def gesture_callback(self, msg):
        with self.lock:
            self.latest_gesture = msg.data
            
        if not self.is_processing:
            threading.Thread(target=self.process_llm).start()
            
    def lidar_callback(self, msg):
        with self.lock:
            self.latest_lidar = msg.data

    def process_llm(self):
        self.is_processing = True
        
        while True:
            current_gesture = None
            current_lidar = None
            with self.lock:
                if self.latest_gesture is None:
                    break
                current_gesture = self.latest_gesture
                current_lidar = self.latest_lidar
                self.latest_gesture = None # Consume the gesture trigger
            
            if self.llm_mode == 'baseline':
                self.get_logger().info(f"[BASELINE MODE] Bypassing LLM. Sending direct mapping: {current_gesture}")
                out_msg = String()
                out_msg.data = current_gesture
                self.publisher.publish(out_msg)
                continue
            
            # Construct a fused prompt for Qwen
            prompt = (
                f"You are a robot controller for a Unitree Go2.\n"
                f"Current Context:\n"
                f"- User Gesture: The user is pointing or performing a '{current_gesture}' gesture.\n"
                f"- Lidar Sensor: {current_lidar}\n\n"
                f"Based on this context, respond with a short command or sequence of commands separated by commas. "
                f"Valid commands are: 'stop', 'go forward', 'go back', 'rotate left', 'rotate right'. "
                f"Examples: 'stop', 'rotate left', 'go back', 'stop, rotate left, go forward'."
            )
            
            self.get_logger().info(f"Sending to LLM:\n{prompt}")
            
            try:
                payload = {
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False
                }
                
                response = requests.post(self.ollama_url, json=payload, timeout=30.0)
                response.raise_for_status()
                
                result = response.json()
                llm_output = result.get('response', '').strip()
                
                self.get_logger().info(f"LLM Response: {llm_output}")
                
                # Publish the result
                out_msg = String()
                out_msg.data = llm_output
                self.publisher.publish(out_msg)
                
            except Exception as e:
                self.get_logger().error(f"Error calling Ollama: {e}")
                
        self.is_processing = False

def main(args=None):
    rclpy.init(args=args)
    node = LLMNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()

if __name__ == '__main__':
    main()
