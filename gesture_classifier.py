import json
import os
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import train_test_split
import numpy as np
import joblib  # For saving the model
from sklearn.metrics import accuracy_score  # For evaluating performance

def load_gesture_data(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data['gestures']

def train_model(gesture_data):
    # Prepare feature and label arrays
    features = []
    labels = []
    
    for gesture in gesture_data:
        # Convert joint angles to a numpy array
        joint_angles = np.array(gesture['joint_angles'])
        
        # Flatten the array if needed (depending on your data structure)
        flattened_features = joint_angles.reshape(-1)
        
        features.append(flattened_features)
        labels.append(gesture['gesture'])
    
    # Convert lists to numpy arrays
    X = np.array(features)
    y = np.array(labels)
    
    # Split the dataset into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Initialize and train the classifier
    model = KNeighborsClassifier(n_neighbors=3)
    model.fit(X_train, y_train)
    
    # Save the trained model
    model_dir = 'models'
    if not os.path.exists(model_dir):
        os.makedirs(model_dir)
    model_path = os.path.join(model_dir, 'gesture_classifier.pkl')
    joblib.dump(model, model_path)
    
    print(f"Training accuracy: {model.score(X_train, y_train):.2f}")
    print(f"Testing accuracy: {model.score(X_test, y_test):.2f}")

if __name__ == '__main__':
    training_data_file = os.path.join('training_data', 'gesture_training_data.json')
    gestures = load_gesture_data(training_data_file)
    
    # Train the model
    train_model(gestures)
