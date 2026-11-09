"""Stateful LSTM classifier, configured as in the original notebook.

One LSTM layer (stateful, batch size 1, one time step per sample, recurrent dropout),
a Dropout layer, and one sigmoid unit (He normal init, seed 1). Adam, binary cross entropy,
one epoch, no shuffling, states reset at the end of training. The original ran Keras 2.2 on
TensorFlow 1.x, where the LSTM gate activation defaulted to Keras 2's hard sigmoid
clip(0.2x + 0.5, 0, 1); that function is reproduced here because Keras 3 changed both the
default and the definition of hard_sigmoid.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")

import keras  # noqa: E402
import numpy as np  # noqa: E402
from keras import layers, ops  # noqa: E402
from sklearn.metrics import accuracy_score  # noqa: E402
from sklearn.preprocessing import StandardScaler  # noqa: E402


@dataclass(frozen=True)
class LSTMConfig:
    units: int
    dropout: float
    recurrent_dropout: float


# Per model settings from the notebook (units, dropout rate, recurrent dropout).
CONFIGS: dict[int, LSTMConfig] = {
    1: LSTMConfig(195, 0.1, 0.1),
    2: LSTMConfig(180, 0.0, 0.4),
    3: LSTMConfig(180, 0.0, 0.4),
    4: LSTMConfig(200, 0.0, 0.4),
    5: LSTMConfig(190, 0.0, 0.3),
    6: LSTMConfig(400, 0.0, 0.5),
    7: LSTMConfig(220, 0.0, 0.4),
}


def keras2_hard_sigmoid(x):
    """Keras 2.x hard sigmoid, the default LSTM gate activation in 2019."""
    return ops.clip(0.2 * x + 0.5, 0.0, 1.0)


def build(config: LSTMConfig, n_features: int, seed: int) -> keras.Model:
    keras.utils.set_random_seed(seed)
    inputs = keras.Input(batch_shape=(1, 1, n_features))
    x = layers.LSTM(
        config.units,
        stateful=True,
        recurrent_dropout=config.recurrent_dropout,
        recurrent_activation=keras2_hard_sigmoid,
        name="lstm",
    )(inputs)
    x = layers.Dropout(config.dropout)(x)
    outputs = layers.Dense(1, activation="sigmoid", kernel_initializer=keras.initializers.HeNormal(seed=1))(x)
    model = keras.Model(inputs, outputs)
    model.compile(loss="binary_crossentropy", optimizer="adam", metrics=["accuracy"])
    return model


def _as_sequence(X: np.ndarray) -> np.ndarray:
    return np.asarray(X, dtype="float32").reshape(len(X), 1, -1)


def fit_predict(
    config: LSTMConfig, X_train: np.ndarray, y_train: np.ndarray, X_eval: np.ndarray, seed: int, scale: bool
) -> np.ndarray:
    """Train for one epoch on X_train in time order, then return P(up) for X_eval in order.

    scale=False reproduces the original (raw features, so volume enters in the billions).
    scale=True standardizes with a scaler fitted on the training rows only.
    """
    if scale:
        scaler = StandardScaler().fit(X_train)
        X_train, X_eval = scaler.transform(X_train), scaler.transform(X_eval)
    model = build(config, X_train.shape[1], seed)
    model.fit(_as_sequence(X_train), np.asarray(y_train, dtype="float32"), batch_size=1, epochs=1, shuffle=False, verbose=0)
    model.get_layer("lstm").reset_state()  # the notebook's ModelStateReset callback
    proba = model.predict(_as_sequence(X_eval), batch_size=1, verbose=0).ravel()
    keras.backend.clear_session()
    return proba


def walk_forward_accuracy(config: LSTMConfig, X: np.ndarray, y: np.ndarray, folds, seed: int, scale: bool) -> float:
    """Mean validation accuracy over the folds (GridSearchCV best_score_ in the notebook)."""
    scores = []
    for train, valid in folds:
        proba = fit_predict(config, X[train], y[train], X[valid], seed, scale)
        scores.append(accuracy_score(y[valid], (proba > 0.5).astype(int)))
    return float(np.mean(scores))
