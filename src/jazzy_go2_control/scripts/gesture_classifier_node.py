#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseArray
from std_msgs.msg import String
import os
import numpy as np

# Try importing ML libraries
try:
    import joblib
    HAS_ML = True
except ImportError:
    HAS_ML = False

class GestureClassifierNode(Node):
    def __init__(self):
        super().__init__('gesture_classifier_node')
        self.get_logger().info("Gesture Classifier Node Started.")
        
        # Parameters
        self.declare_parameter('model_path', '/home/ertoto/Documenti/GitHub/COGAR_Assignment_2026/gestures')
        self.model_path = self.get_parameter('model_path').get_parameter_value().string_value
        
        # Load Classifier
        self.classifier = None
        if HAS_ML:
            if os.path.exists(self.model_path):
                try:
                    self.classifier = joblib.load(self.model_path)
                    self.get_logger().info(f"Loaded gesture classifier from {self.model_path}")
                except Exception as e:
                    self.get_logger().error(f"Failed to load classifier: {e}")
            else:
                self.get_logger().warning(f"Classifier not found at {self.model_path}. Prediction will be bypassed.")
        else:
            self.get_logger().warning("joblib/sklearn not found. Classifier disabled.")

        # Publisher for the gesture label to the LLM node
        self.publisher = self.create_publisher(
            String,
            'manus_data',
            10)

        # Subscriptions to the Manus gloves
        self.left_sub = self.create_subscription(
            PoseArray,
            'manus_left',
            self.left_glove_callback,
            10)

    def left_glove_callback(self, msg):
        self.process_glove_data(msg, "Left")

    def process_glove_data(self, msg, hand_name):
        poses = msg.poses
        if not poses:
            return

        # Expecting exactly 21 joints. Pad or truncate to ensure exactly 21.
        expected_joints = 21
        if len(poses) < expected_joints:
            # Pad with the wrist pose (first pose) or zero-poses
            padding_pose = poses[0] if len(poses) > 0 else None
            padded_poses = list(poses)
            while len(padded_poses) < expected_joints:
                if padding_pose:
                    padded_poses.append(padding_pose)
                else:
                    from geometry_msgs.msg import Pose
                    padded_poses.append(Pose())
            poses_to_process = padded_poses
        else:
            poses_to_process = poses[:expected_joints]

        # Extract features: position (x, y, z) and orientation (x, y, z, w) for all 21 joints
        features = []
        for pose in poses_to_process:
            features.extend([
                pose.position.x, pose.position.y, pose.position.z,
                pose.orientation.x, pose.orientation.y, pose.orientation.z, pose.orientation.w
            ])

        # Predict gesture
        gesture_label = "unknown"
        if self.classifier:
            try:
                features_arr = np.array(features).reshape(1, -1)
                prediction = self.classifier.predict(features_arr)
                gesture_label = str(prediction[0])
            except Exception as e:
                self.get_logger().error(f"Prediction failed: {e}")
        else:
            # If no classifier, send a dummy gesture label based on simple check
            gesture_label = "unknown"

        # Publish the predicted gesture label to the llm_node
        self.get_logger().info(f"[{hand_name} Hand] Predicted gesture: {gesture_label}")
        out_msg = String()
        out_msg.data = gesture_label
        self.publisher.publish(out_msg)

def main(args=None):
    rclpy.init(args=args)
    node = GestureClassifierNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()

if __name__ == '__main__':
    main()
