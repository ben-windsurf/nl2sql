import os

# Hard-coded default model
DEFAULT_OPENAI_MODEL = "gpt-4"

# DB path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "sample.db")

# Max rows returned
MAX_ROWS = 1000
