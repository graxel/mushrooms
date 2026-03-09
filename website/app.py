import os
import yaml
import numpy as np
import pandas as pd
import sqlalchemy
from flask import Flask, Blueprint, jsonify, render_template, request
from flask_cors import CORS
from sklearn.metrics import (
    confusion_matrix,
    precision_score,
    recall_score,
    f1_score,
    fbeta_score,
    roc_curve,
    auc,
    precision_recall_curve,
)
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))

app = Flask(__name__)
CORS(app, origins=[
    "https://graxel.github.io",
    "https://kevingrazel.com",
    "http://localhost:8080"
])
bp = Blueprint("mushrooms", __name__)

# --- Config ---
DBT_TARGET = os.environ.get("DBT_TARGET", "dev")
_user = os.environ.get("USER", "")
PRED_SCHEMA = f"{_user}_consumption" if DBT_TARGET == "dev" else "consumption"

PG_HOST = os.getenv("PG_HOST")
PG_PORT = os.getenv("PG_PORT")
PG_USER = os.getenv("PG_USER")
PG_PASS = os.getenv("PG_PASS")
PG_DB = os.getenv("PG_DB")
DB_URL = f"postgresql://{PG_USER}:{PG_PASS}@{PG_HOST}:{PG_PORT}/{PG_DB}"

MODELS_YAML = os.path.join(os.path.dirname(__file__), "../prefect/models.yml")
F_BETA = 32


def get_engine():
    return sqlalchemy.create_engine(DB_URL)


def load_models_config() -> list[dict]:
    with open(MODELS_YAML) as f:
        return yaml.safe_load(f)["models"]


def load_predictions(model_name: str) -> pd.DataFrame:
    engine = get_engine()
    return pd.read_sql(
        f"""
        SELECT * FROM {PRED_SCHEMA}.predictions
        WHERE model_name = %(model_name)s
        AND ground_truth IS NOT NULL
        ORDER BY mushroom_id
        """,
        engine,
        params={"model_name": model_name},
    )


def compute_metrics(df: pd.DataFrame, dataset: str) -> dict:
    sub = df[df["dataset"] == dataset]
    if sub.empty:
        return None

    y_true = sub["ground_truth"].values
    y_pred = sub["predicted_label"].values
    y_prob = sub["probability"].values if sub["probability"].notna().any() else None

    cm = confusion_matrix(y_true, y_pred).tolist()

    # Scalar metrics
    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    f_beta = fbeta_score(y_true, y_pred, beta=F_BETA, zero_division=0)
    accuracy = float((y_true == y_pred).mean())

    # ROC curve — fall back to predicted label as score if no probability
    scores = y_prob if y_prob is not None else y_pred.astype(float)
    fpr, tpr, _ = roc_curve(y_true, scores)
    roc_auc = auc(fpr, tpr)

    # Precision-Recall curve
    prec_curve, rec_curve, _ = precision_recall_curve(y_true, scores)

    return {
        "n": int(len(sub)),
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        f"f{F_BETA}": round(f_beta, 4),
        "confusion_matrix": cm,
        "roc": {
            "fpr": fpr.tolist(),
            "tpr": tpr.tolist(),
            "auc": round(roc_auc, 4),
        },
        "pr_curve": {
            "precision": prec_curve.tolist(),
            "recall": rec_curve.tolist(),
        },
    }


# --- Routes ---

@bp.route("/api/models")
def api_models():
    return jsonify(load_models_config())


@bp.route("/api/metrics/<model_name>")
def api_metrics(model_name):
    version = request.args.get("version")
    df = load_predictions(model_name)
    if df.empty:
        return jsonify({"error": "No predictions found"}), 404
    if version:
        df = df[df["model_version"] == version]

    deployed_at = str(df["deployed_at"].max())
    version = str(df["model_version"].iloc[0])

    return jsonify({
        "model_name": model_name,
        "model_version": version,
        "deployed_at": deployed_at,
        "pre": compute_metrics(df, "pre"),
        "post": compute_metrics(df, "post"),
    })


app.register_blueprint(bp, url_prefix="/mushrooms")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8003)