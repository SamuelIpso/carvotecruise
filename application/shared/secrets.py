from pathlib import Path
from json import loads


ROOT_DIR = Path(__file__).resolve().parent.parent.parent

secrets = dict()

# Reading secret files
with open(f'{ROOT_DIR}/secrets.json', 'r') as file:
    secrets = loads(file.read())
