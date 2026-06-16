#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import requests
import json
import threading
import os
import numpy as np

# Try importing ML libraries
try:
    import joblib
    HAS_ML = True
except ImportError:
    HAS_ML = False

class LLMNode(Node):
    def __init__(self):
        super().__init__('llm_node')
        self.get_logger().info("LLM Node Started with Classifier Integration.")
        
        # Parameters
        self.declare_parameter('ollama_url', 'http://localhost:11434/api/generate')
        self.declare_parameter('model_name', 'qwen2.5-coder:7b')
        self.declare_parameter('classifier_path', 'models/gesture_classifier.pkl')
        
        self.ollama_url = self.get_parameter('ollama_url').get_parameter_value().string_value
        self.model_name = self.get_parameter('model_name').get_parameter_value().string_value
        self.classifier_path = self.get_parameter('classifier_path').get_parameter_value().string_value
        
        # Load Classifier
        self.classifier = None
        if HAS_ML:
            if os.path.exists(self.classifier_path):
                try:
                    self.classifier = joblib.load(self.classifier_path)
                    self.get_logger().info(f"Loaded gesture classifier from {self.classifier_path}")
                except Exception as e:
                    self.get_logger().error(f"Failed to load classifier: {e}")
            else:
                self.get_logger().warning(f"Classifier not found at {self.classifier_path}. Running in raw mode.")
        else:
            self.get_logger().warning("joblib/sklearn not found. Classifier disabled.")

        # Subscriptions & Publications
        self.subscription = self.create_subscription(
            String,
            'manus_data',
            self.manus_callback,
            10)
        
        self.publisher = self.create_publisher(
            String,
            'go_command',
            10)
        
        # Inference state
        self.is_processing = False
        self.latest_input = None
        self.lock = threading.Lock()

    def manus_callback(self, msg):
        input_data = msg.data
        
        # If we have a classifier, try to predict the gesture first
        gesture_label = "unknown"
        if self.classifier:
            try:
                # Expecting input_data to be a JSON string like: {"joint_angles": [...]}
                data = json.loads(input_data)
                if 'joint_angles' in data:
                    angles = np.array(data['joint_angles']).reshape(1, -1)
                    prediction = self.classifier.predict(angles)
                    gesture_label = str(prediction[0])
                    self.get_logger().info(f"Predicted Gesture: {gesture_label}")
                    input_data = f"The user is performing a '{gesture_label}' gesture."
            except Exception as e:
                self.get_logger().debug(f"Classifier prediction failed (likely non-JSON input): {e}")

        with self.lock:
            self.latest_input = input_data
            
        if not self.is_processing:
            threading.Thread(target=self.process_llm).start()

    def process_llm(self):
        self.is_processing = True
        
        while True:
            current_input = None
            with self.lock:
                if self.latest_input is None:
                    break
                current_input = self.latest_input
                self.latest_input = None
            
            # Construct a better prompt for Qwen
            prompt = (
                f"You are a robot controller for a Unitree Go2. "
                f"Input from sensor: {current_input} "
                f"Respond with a short command or sequence of commands separated by commas. "
                f"Valid commands are: 'stop', 'go forward', 'go back', 'rotate left', 'rotate right'. "
                f"Examples: 'stop', 'rotate left', 'go back', 'stop, rotate left, go forward'."
            )
            
            self.get_logger().info(f"Sending to LLM: {prompt}")
            
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
