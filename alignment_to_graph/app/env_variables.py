import os
from dotenv import load_dotenv

load_dotenv()

URI = os.environ["NEO4J_URI"]
USER_NAME = os.environ["USER_NAME"]
PASSWORD = os.environ["PASSWORD"]