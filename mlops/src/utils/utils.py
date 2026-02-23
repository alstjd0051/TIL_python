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


def model_dir(model_name):
    return os.path.join(
        project_path(),
        "models",
        model_name
    )