import os
import random

import numpy as np


def init_seed():
    np.random.seed(0)
    random.seed(0)


def project_path():
    return os.path.join(
        os.path.dirname(
            os.path.abspath(__file__)
        ),
        "..",
        ".."
    )


def model_dir(model_name: str) -> str:
    return os.path.join(
        project_path(),
        "models",
        model_name
    )

def auto_increment_run_suffix(name: str, pad: int = 3) -> str:
    suffix = name.split("-")[-1]
    next_suffix = str(int(suffix) + 1).zfill(pad)
    return name.replace(suffix, next_suffix)