import numpy as np


def train(model, train_loader, lr=0.001):
    total_loss = 0
    for features, labels in train_loader:
        predictions = model.forward(features)
        labels = labels.reshape(-1, 1)
        loss = np.mean((predictions - labels) ** 2)
        
        model.backward(features, labels, predictions, lr=lr)

        total_loss += loss

    return total_loss / len(train_loader)