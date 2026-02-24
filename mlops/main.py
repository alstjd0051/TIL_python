import os
import sys
import time
import fire

from alive_progress import alive_it
from icecream import ic

from src.utils.factory import ModelFactory

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.dataset.data_loader import SimpleDataLoader
from src.dataset.watch_log import get_datasets
from src.evaluate.evaluate import evaluate
from src.model.movie_predictor import MoviePredictor,  model_save
from src.train.train import train
from src.utils.utils import init_seed

init_seed()

def run_train(model_name, num_epochs=10):
    # ...
    # 데이터셋 생성 및 DataLoader 생성
    
    # 모델 초기화    
    model = ModelFactory.create(model_name, **model_params)
    
    # 학습 루프, 모델 저장, 예측, ...
    # num_epochs = 10 부분 삭제

if __name__ == "__main__":
    # 데이터셋 및 DataLoader 생성
    train_dataset, val_dataset, test_dataset = get_datasets()
    train_loader = SimpleDataLoader(
        train_dataset.features, train_dataset.labels, batch_size=64, shuffle=True
    )
    val_loader = SimpleDataLoader(
        val_dataset.features, val_dataset.labels, batch_size=64, shuffle=False
    )
    test_loader = SimpleDataLoader(
        test_dataset.features, test_dataset.labels, batch_size=64, shuffle=False
    )

    # 모델 초기화
    model_params = {
        "input_dim": train_dataset.features_dim,
        "num_classes": train_dataset.num_classes,
        "hidden_dim": 64,
    }
    model = MoviePredictor(**model_params)

    # 학습 루프
    num_epochs = 10
    for epoch in alive_it(range(num_epochs), title="Training"):
        time.sleep(0.5)
        train_loss = train(model, train_loader)
        val_loss, _ = evaluate(model, val_loader)
        ic(
            f"Epoch {epoch + 1}/{num_epochs}, "
            f"Train Loss: {train_loss:.4f}, "
            f"Val Loss: {val_loss:.4f}, "
            f"Val-Train Loss : {val_loss - train_loss:.4f}"
        )

    # 테스트
    test_loss, predictions = evaluate(model, test_loader)
    ic(f"Test Loss : {test_loss:.4f}")
    ic([train_dataset.decode_content_id(idx) for idx in predictions])
        
    model_save(
        model=model,
        model_params=model_params,
        epoch=num_epochs,
        loss=train_loss,
        scaler=train_dataset.scaler,
        label_encoder=train_dataset.label_encoder,
    )