import os
import sys
import fire

from tqdm import tqdm

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time

import wandb
from dotenv import load_dotenv

from dataset.data_loader import SimpleDataLoader
from dataset.watch_log import get_datasets
from evaluate.evaluate import evaluate
from model.movie_predictor import model_save
from train.train import train
from utils.utils import init_seed, auto_increment_run_suffix
from utils.factory import ModelFactory
from alive_progress import alive_it


init_seed()
load_dotenv() 

def get_runs(project_name):
    return wandb.Api().runs(path=project_name, order="-created_at")

def get_latest_run(project_name):
    runs = get_runs(project_name)
    if not runs:
        return f"{project_name}-000"
    return runs[0].name


def run_train(
    model_name,
    num_epochs=10,
    batch_size=64,
    hidden_dim=64,
    lr=0.001,
):
    """
    this is run_train definition.
    """
    api_key = os.environ.get("WANDB_API_KEY")
    wandb.login(key=api_key)

    project_name = model_name.replace("_","-")
    run_name = get_latest_run(project_name)
    next_run_name = auto_increment_run_suffix(run_name)

    wandb.init(
        project=project_name,
        id=next_run_name,
        name=next_run_name,
        notes="content-based movie recommend model",
        tags=["content-based", "movie-recommend","movie", "recommend", "model"],
        config=locals()
    )

    train_dataset, val_dataset, test_dataset = get_datasets()
    train_loader = SimpleDataLoader(
        train_dataset.features, train_dataset.labels, batch_size=batch_size, shuffle=True
    )
    val_loader = SimpleDataLoader(
        val_dataset.features, val_dataset.labels, batch_size=batch_size, shuffle=False
    )
    test_loader = SimpleDataLoader(
        test_dataset.features, test_dataset.labels, batch_size=batch_size, shuffle=False
    )

    # 모델 초기화    
    model_params = {
        "input_dim": train_dataset.features_dim,
        "num_classes": train_dataset.num_classes,
        "hidden_dim": hidden_dim,

    }
    # model = MoviePredictor(**model_params)
    model = ModelFactory.create(model_name, **model_params)


    # 학습 루프
    # num_epochs = 10
    

    for epoch in alive_it(range(num_epochs), title="Training"):
        time.sleep(.2)
        train_loss = train(model, train_loader, lr=lr)
        val_loss, _ = evaluate(model, val_loader)

        wandb.log({"Loss/Train":train_loss})
        wandb.log({"Loss/Val":val_loss})

        print(
            f"Epoch {epoch +1}/{num_epochs}, "
            f"Train Loss: {train_loss:.4f}, "
            f"Val Loss: {val_loss:.4f}, "
            f"Val-Train Loss: {val_loss - train_loss:.4f}",
        )
        model_save(
            model=model,
            model_params=model_params,
            epoch=epoch,
            loss=train_loss,
            scaler=train_dataset.scaler,
            label_encoder=train_dataset.label_encoder,
        )

    # 테스트
    # test_loss, predictions = evaluate(model, test_loader)
    # print(f"Test Loss : {test_loss:.4f}")
    # print([train_dataset.decode_content_id(idx) for idx in predictions])
    # ic(test_loss)
    # ic([train_dataset.decode_content_id(idx) for idx in predictions])
    
    
    model_save(
        model=model,
        model_params=model_params,
        epoch=num_epochs,
        loss=train_loss,
        scaler=train_dataset.scaler,
        label_encoder=train_dataset.label_encoder,
    )

    wandb.finish()



if __name__ == "__main__":
    fire.Fire({
        "train":run_train,
    })