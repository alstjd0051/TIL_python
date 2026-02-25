import os
import sys
import glob # 모델 저장 파일 경로 조회
import pickle # 모델 저장 파일 로드
import pandas as pd
import numpy as np


from src.dataset.data_loader import SimpleDataLoader
from src.dataset.watch_log import WatchLogDataset,get_datasets
from src.evaluate.evaluate import evaluate
from src.utils.utils import model_dir
from src.model.movie_predictor import MoviePredictor



def load_checkpoint() -> dict:
    target_dir = model_dir(MoviePredictor.name)
    models_path = os.path.join(target_dir, "*.pkl")
    latest_model = glob.glob(models_path)[-1]

    with open(latest_model, "rb") as f:
        checkpoint = pickle.load(f)
        
    return checkpoint


def init_model(checkpoint: dict) -> tuple[MoviePredictor, dict, dict]:
    model = MoviePredictor(**checkpoint["model_params"])
    model.load_state_dict(checkpoint["model_state_dict"])
    scaler = checkpoint.get("scaler", None)
    label_encoder = checkpoint.get("label_encoder", None)
    return model, scaler, label_encoder

def make_inference_df(data:list[dict]) -> pd.DataFrame:
    columns = "user_id content_id watch_seconds rating popularity".split()
    return pd.DataFrame(
        data=[data],
        columns=columns
    )

def inference(model: MoviePredictor, scaler: dict, label_encoder: dict, data: np.array, batch_size=1) -> str:
    if data.size > 0: # real-time inference
        df = make_inference_df(data)
        dataset = WatchLogDataset(df, scaler=scaler, label_encoder=label_encoder)
    else: # batch inference
        _, _, dataset = get_datasets(scaler=scaler, label_encoder=label_encoder)

    dataloader = SimpleDataLoader(
		    dataset.features, dataset.labels, batch_size=batch_size, shuffle=False
		)
    loss, predictions = evaluate(model, dataloader)
    print(loss, predictions)
    return [dataset.decode_content_id(idx) for idx in predictions]

def recommend_to_df(recommend):
    return pd.DataFrame(
        data=recommend,
        columns="recommend_content_id".split()
    )

