import os
import sys
import pandas as pd
import mlflow
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()


required_vars = [
    "PG_HOST",
    "PG_PORT",
    "PG_DB",
    "PG_USER",
    "PG_PASS",
]

missing = [var for var in required_vars if var not in os.environ]
if missing:

    print(f"Missing environment variables: {', '.join(missing)}")
    sys.exit(1)


PG_HOST = os.getenv("PG_HOST")
PG_PORT = os.getenv("PG_PORT")
PG_DB = os.getenv("PG_DB")
PG_USER = os.getenv("PG_USER")
PG_PASS = os.getenv("PG_PASS")

mlflow.set_tracking_uri("http://192.168.0.100:5000")

db_url = f"postgresql+psycopg2://{PG_USER}:{PG_PASS}@{PG_HOST}:{PG_PORT}/{PG_DB}"

