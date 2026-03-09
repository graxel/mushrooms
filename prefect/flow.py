import os
import subprocess
from prefect import flow, task
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))

DBT_PROJECT_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../dbt_project")
)
DBT_PROFILE = os.environ.get("DBT_PROFILE", "mushrooms")
DBT_TARGET = os.environ.get("DBT_TARGET", "dev")  # dev | qa | prod


def run_dbt(select: str) -> None:
    result = subprocess.run(
        ["uv", "run", "dbt", "run", "--select", select,
         "--profiles-dir", DBT_PROJECT_DIR,
         "--project-dir", DBT_PROJECT_DIR,
         "--target", DBT_TARGET],
        cwd=DBT_PROJECT_DIR,
        capture_output=False,
        check=True,
    )
    return result


@task(name="dbt: raw + intermediate")
def task_dbt_feature_engineering():
    print(f"Running dbt feature engineering (target: {DBT_TARGET})...")
    run_dbt("raw intermediate")


@task(name="batch inference")
def task_inference():
    print("Running batch inference...")
    # Import and run inline so Prefect captures logs
    from inference import main
    main()


@task(name="dbt: consumption")
def task_dbt_consumption():
    print("Running dbt consumption views...")
    run_dbt("consumption")


@flow(name="mushrooms-inference-pipeline")
def mushrooms_pipeline():
    fe = task_dbt_feature_engineering()
    inf = task_inference(wait_for=[fe])
    task_dbt_consumption(wait_for=[inf])


if __name__ == "__main__":
    mushrooms_pipeline()