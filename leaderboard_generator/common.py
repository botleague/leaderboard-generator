from botleague_helpers.config import blconfig
from botleague_helpers.db import get_db


def get_botleague_db():
    return get_db(blconfig.botleague_collection_name)
