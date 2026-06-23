import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from sklearn.preprocessing import LabelEncoder
import pickle
import os

# Parametri di configurazione
CSV_FILE = "manus_left_joints.csv"
MODEL_SAVE_PATH = "gesture2.pth"
LABEL_ENCODER_PATH = "gesture2_classes.pkl"

SEQUENCE_LENGTH = 10  # Numero di fotogrammi consecutivi (finestra temporale)
BATCH_SIZE = 32
EPOCHS = 20
LEARNING_RATE = 0.001

def load_and_preprocess_data(csv_file, seq_length):
    print("Lettura del CSV in corso...")
    df = pd.read_csv(csv_file)
    
    # Raggruppiamo per timestamp per ricostruire il vettore da 147 feature (21 giunti * 7 valori)
    grouped = df.groupby('timestamp')
    
    X_frames = []
    y_labels = []
    
    for timestamp, group in grouped:
        # Assicuriamoci che ogni frame abbia esattamente 21 giunti
        if len(group) != 21:
            continue
            
        features = []
        for _, row in group.iterrows():
            features.extend([
                row['pos_x'], row['pos_y'], row['pos_z'],
                row['rot_x'], row['rot_y'], row['rot_z'], row['rot_w']
            ])
            
        X_frames.append(features)
        # Prendiamo il comando come etichetta
        y_labels.append(group.iloc[0]['command'])
        
    X_frames = np.array(X_frames)
    y_labels = np.array(y_labels)
    
    print(f"Fotogrammi totali estratti: {len(X_frames)}")
    
    # Codifica delle stringhe (es. 'STOP') in interi
    le = LabelEncoder()
    y_encoded = le.fit_transform(y_labels)
    
    # Creazione delle sequenze temporali
    X_seq = []
    y_seq = []
    for i in range(len(X_frames) - seq_length + 1):
        X_seq.append(X_frames[i : i + seq_length])
        # L'etichetta associata alla sequenza è il comando dell'ultimo fotogramma della finestra
        y_seq.append(y_encoded[i + seq_length - 1])
        
    return np.array(X_seq), np.array(y_seq), le

class GestureDataset(Dataset):
    def __init__(self, X, y):
        self.X = torch.tensor(X, dtype=torch.float32)
        self.y = torch.tensor(y, dtype=torch.long)
        
    def __len__(self):
        return len(self.X)
        
    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]

# Definizione del modello basato su LSTM
class GestureLSTM(nn.Module):
    def __init__(self, input_size=147, hidden_size=64, num_layers=1, num_classes=5):
        super(GestureLSTM, self).__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, num_classes)
        
    def forward(self, x):
        # x ha dimensione: (batch, seq_len, input_size)
        out, _ = self.lstm(x)
        # Prendiamo solo l'output dell'ultimo step temporale
        out = out[:, -1, :] 
        out = self.fc(out)
        return out

def main():
    if not os.path.exists(CSV_FILE):
        print(f"Errore: Il file {CSV_FILE} non è stato trovato!")
        return

    X, y, label_encoder = load_and_preprocess_data(CSV_FILE, SEQUENCE_LENGTH)
    num_classes = len(label_encoder.classes_)
    
    print(f"Generate {len(X)} sequenze temporali da {SEQUENCE_LENGTH} frame.")
    print(f"Classi trovate ({num_classes}): {label_encoder.classes_}")
    
    # Salvataggio del LabelEncoder per poter decodificare i risultati nel nodo ROS2
    with open(LABEL_ENCODER_PATH, 'wb') as f:
        pickle.dump(label_encoder, f)
        print(f"LabelEncoder salvato in {LABEL_ENCODER_PATH}")
        
    dataset = GestureDataset(X, y)
    dataloader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True)
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Uso il dispositivo: {device}")
    
    model = GestureLSTM(input_size=147, hidden_size=64, num_layers=1, num_classes=num_classes).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)
    
    print("\nInizio addestramento...")
    for epoch in range(EPOCHS):
        model.train()
        total_loss = 0
        correct = 0
        total = 0
        
        for batch_X, batch_y in dataloader:
            batch_X, batch_y = batch_X.to(device), batch_y.to(device)
            
            optimizer.zero_grad()
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)
            
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            _, predicted = torch.max(outputs.data, 1)
            total += batch_y.size(0)
            correct += (predicted == batch_y).sum().item()
            
        accuracy = 100 * correct / total
        print(f"Epoca [{epoch+1}/{EPOCHS}], Loss: {total_loss/len(dataloader):.4f}, Accuratezza: {accuracy:.2f}%")
        
    print(f"\nAddestramento completato. Salvataggio del modello in {MODEL_SAVE_PATH}...")
    torch.save(model.state_dict(), MODEL_SAVE_PATH)
    print("Salvato con successo. Ora puoi usarlo in ROS2!")

if __name__ == '__main__':
    main()
