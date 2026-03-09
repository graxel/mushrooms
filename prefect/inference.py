import os
import yaml
import mlflow
import pandas as pd
import sqlalchemy
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))


MLFLOW_TRACKING_URI = os.environ["MLFLOW_TRACKING_URI"]


DBT_TARGET = os.environ.get("DBT_TARGET")

if DBT_TARGET == "dev":
    DBT_SCHEMA = os.environ.get("USER") + "_intermediate"
    DBT_PRED_SCHEMA = os.environ.get("USER") + "_consumption"
else:
    DBT_SCHEMA = "intermediate"
    DBT_PRED_SCHEMA = "consumption"


PG_HOST = os.getenv("PG_HOST")
PG_PORT = os.getenv("PG_PORT")
PG_USER = os.getenv("PG_USER")
PG_PASS = os.getenv("PG_PASS")
PG_DB = os.getenv("PG_DB")
DB_URL = f"postgresql://{PG_USER}:{PG_PASS}@{PG_HOST}:{PG_PORT}/{PG_DB}"

MODELS_YAML = os.path.join(os.path.dirname(__file__), "models.yml")

CREATE_TABLE_SQL = f"""
CREATE TABLE IF NOT EXISTS {DBT_PRED_SCHEMA}.predictions (
    prediction_id     SERIAL PRIMARY KEY,
    model_name        TEXT NOT NULL,
    model_version     TEXT NOT NULL,
    mlflow_run_id     TEXT,
    mushroom_id       INTEGER NOT NULL,
    dataset           TEXT NOT NULL,
    deployed_at       TIMESTAMP NOT NULL,
    predicted_label   INTEGER NOT NULL,
    probability       FLOAT,
    ground_truth      INTEGER,
    correct           BOOLEAN GENERATED ALWAYS AS (predicted_label = ground_truth) STORED
);
"""


def load_config() -> list[dict]:
    with open(MODELS_YAML) as f:
        return yaml.safe_load(f)["models"]


def get_engine() -> sqlalchemy.Engine:
    return sqlalchemy.create_engine(DB_URL)


def load_features(engine: sqlalchemy.Engine, table: str) -> pd.DataFrame:
    return pd.read_sql(
        f"SELECT * FROM {DBT_SCHEMA}.{table}",
        engine
    )


def resolve_model_version(model_name: str, version: str) -> tuple[str, str]:
    """Returns (model_uri, resolved_version_number)"""
    client = mlflow.MlflowClient()
    if version == "latest":
        versions = client.get_latest_versions(model_name)
        resolved = max(versions, key=lambda v: int(v.version))
        return f"models:/{model_name}/{resolved.version}", resolved.version
    return f"models:/{model_name}/{version}", version


def run_inference(
    model,
    model_uri: str,
    run_id: str,
    model_name: str,
    model_version: str,
    df: pd.DataFrame,
    dataset: str,
    deployed_at: datetime,
) -> pd.DataFrame:
    feature_cols = [c for c in df.columns if c not in ("mushroom_id", "label_encoded")]
    X = df[feature_cols]

    preds = model.predict(X)
    if isinstance(preds, pd.DataFrame):
        preds = preds.iloc[:, 0].values

    # Try to get probabilities via pyfunc params (MLflow 2.x)
    try:
        xgb_model = mlflow.xgboost.load_model(model_uri)
        probability = xgb_model.predict_proba(X)[:, 1].tolist()  # P(edible)
    except Exception as e:
        print(f"  ⚠ predict_proba unavailable ({e}), storing None")
        probability = None

    return pd.DataFrame({
        "model_name": model_name,
        "model_version": model_version,
        "mlflow_run_id": run_id,
        "mushroom_id": df["mushroom_id"].values,
        "dataset": dataset,
        "deployed_at": deployed_at,
        "predicted_label": preds.astype(int),
        "probability": probability,
        "ground_truth": df["label_encoded"].values if "label_encoded" in df.columns else None,
    })


def write_predictions(engine: sqlalchemy.Engine, df: pd.DataFrame) -> None:
    with engine.begin() as conn:
        conn.execute(sqlalchemy.text(f"CREATE SCHEMA IF NOT EXISTS {DBT_PRED_SCHEMA}"))
        conn.execute(sqlalchemy.text(CREATE_TABLE_SQL))
    df.to_sql("predictions", engine, if_exists="append", index=False, schema=DBT_PRED_SCHEMA)


def main():
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    engine = get_engine()
    config = load_config()
    deployed_at = datetime.now(timezone.utc)

    pre_df = load_features(engine, "mushrooms_encoded_for_xgb_pre")
    post_df = load_features(engine, "mushrooms_encoded_for_xgb_post")

    all_predictions = []

    for model_cfg in config:
        model_name = model_cfg["name"]
        model_uri, model_version = resolve_model_version(model_name, model_cfg["version"])

        print(f"Loading {model_name} v{model_version} from MLflow...")
        model = mlflow.pyfunc.load_model(model_uri)
        run_id = model.metadata.run_id

        for df, dataset in [(pre_df, "pre"), (post_df, "post")]:
            preds_df = run_inference(
                model, model_uri, run_id, model_name, model_version, df, dataset, deployed_at
            )
            all_predictions.append(preds_df)
            print(f"  → {dataset}: {len(preds_df)} predictions")

    final_df = pd.concat(all_predictions, ignore_index=True)
    write_predictions(engine, final_df)
    print(f"Wrote {len(final_df)} total predictions to Postgres.")


if __name__ == "__main__":
    main()