#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseArray
from std_msgs.msg import String
import os
import numpy as np
from collections import deque
import pickle

# Try importing ML libraries
try:
    import joblib
    HAS_JOBLIB = True
except ImportError:
    HAS_JOBLIB = False

try:
    import torch
    import torch.nn as nn
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

# Definizione del modello basato su LSTM (da train_model.py)
if HAS_TORCH:
    class GestureLSTM(nn.Module):
        def __init__(self, input_size=147, hidden_size=64, num_layers=1, num_classes=5):
            super(GestureLSTM, self).__init__()
            self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
            self.fc = nn.Linear(hidden_size, num_classes)
            
        def forward(self, x):
            out, _ = self.lstm(x)
            out = out[:, -1, :] 
            out = self.fc(out)
            return out

class GestureClassifierNode(Node):
    def __init__(self):
        super().__init__('gesture_classifier_node')
        self.get_logger().info("Gesture Classifier Node Started.")
        
        # Parameters
        self.declare_parameter('classifier_type', 'knn')
        self.classifier_type = self.get_parameter('classifier_type').get_parameter_value().string_value
        
        self.classifier = None
        self.label_encoder = None
        self.frame_buffer = deque(maxlen=10) # For LSTM sequence
        
        if self.classifier_type == 'lstm':
            self.model_path = 'gesture2.pth'
            self.le_path = 'gesture2_classes.pkl'
            
            if HAS_TORCH and os.path.exists(self.model_path) and os.path.exists(self.le_path):
                try:
                    # Load label encoder
                    with open(self.le_path, 'rb') as f:
                        self.label_encoder = pickle.load(f)
                    num_classes = len(self.label_encoder.classes_)
                    
                    # Load PyTorch model
                    self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
                    self.classifier = GestureLSTM(input_size=147, hidden_size=64, num_layers=1, num_classes=num_classes)
                    self.classifier.load_state_dict(torch.load(self.model_path, map_location=self.device, weights_only=True))
                    self.classifier.to(self.device)
                    self.classifier.eval()
                    
                    self.get_logger().info(f"Loaded LSTM classifier from {self.model_path}")
                except Exception as e:
                    self.get_logger().error(f"Failed to load PyTorch classifier: {e}")
            else:
                self.get_logger().warning(f"PyTorch not found or model files missing. Prediction bypassed.")
                
        else:
            self.model_path = 'gestures'
            if HAS_JOBLIB and os.path.exists(self.model_path):
                try:
                    self.classifier = joblib.load(self.model_path)
                    self.get_logger().info(f"Loaded KNN classifier from {self.model_path}")
                except Exception as e:
                    self.get_logger().error(f"Failed to load Scikit-Learn classifier: {e}")
            else:
                self.get_logger().warning(f"Joblib not found or model files missing. Prediction bypassed.")

        # Publisher for the gesture label to the LLM node
        self.publisher = self.create_publisher(
            String,
            'predicted_gesture',
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
            self.get_logger().warning(f"Received empty PoseArray for {hand_name} Hand!")
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
                if self.classifier_type == 'lstm':
                    self.frame_buffer.append(features)
                    if len(self.frame_buffer) == 10:
                        # LSTM prediction
                        X_seq = np.array([self.frame_buffer]) # Shape: (1, 10, 147)
                        X_tensor = torch.tensor(X_seq, dtype=torch.float32).to(self.device)
                        with torch.no_grad():
                            outputs = self.classifier(X_tensor)
                            _, predicted_idx = torch.max(outputs.data, 1)
                        gesture_label = self.label_encoder.inverse_transform([predicted_idx.item()])[0]
                else:
                    # KNN prediction
                    features_arr = np.array(features).reshape(1, -1)
                    prediction = self.classifier.predict(features_arr)
                    gesture_label = str(prediction[0])
            except Exception as e:
                self.get_logger().error(f"Prediction failed: {e}")

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
