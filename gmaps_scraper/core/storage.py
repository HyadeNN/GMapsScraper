import json
import os
from datetime import datetime
from pathlib import Path
from pymongo import MongoClient

# Handle both direct execution and package imports
try:
    from ..utils.logger import logger
    from ..config.settings import (
        STORAGE_TYPE,
        MONGODB_URI,
        MONGODB_DB,
        MONGODB_COLLECTION,
        DATA_DIR
    )
except ImportError:
    from utils.logger import logger
    from config.settings import (
        STORAGE_TYPE,
        MONGODB_URI,
        MONGODB_DB,
        MONGODB_COLLECTION,
        DATA_DIR
    )


class BaseStorage:
    def save(self, data, **kwargs):
        raise NotImplementedError("Storage classes must implement save method")

    def load(self, **kwargs):
        raise NotImplementedError("Storage classes must implement load method")


class JSONStorage(BaseStorage):
    def __init__(self, data_dir=None):
        self.data_dir = data_dir if data_dir else DATA_DIR
        os.makedirs(self.data_dir, exist_ok=True)

    def save(self, data, filename=None, city=None, search_term=None):
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            city_str = f"{city}_" if city else ""
            search_str = f"{search_term.replace(' ', '_')}_" if search_term else ""
            filename = f"{city_str}{search_str}{timestamp}.json"

        file_path = self.data_dir / filename
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"Data saved to {file_path}")
            return str(file_path)
        except Exception as e:
            logger.error(f"Error saving data to JSON: {str(e)}")
            raise

    def load(self, filename):
        file_path = self.data_dir / filename
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading data from JSON: {str(e)}")
            raise


class MongoDBStorage(BaseStorage):
    def __init__(self, uri=MONGODB_URI, db_name=MONGODB_DB, collection_name=MONGODB_COLLECTION):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    def save(self, data, **kwargs):
        try:
            if isinstance(data, list):
                if data:
                    result = self.collection.insert_many(data)
                    logger.info(f"Inserted {len(result.inserted_ids)} documents into MongoDB")
                    return result.inserted_ids
                return []
            else:
                result = self.collection.insert_one(data)
                logger.info(f"Inserted document with ID {result.inserted_id} into MongoDB")
                return result.inserted_id
        except Exception as e:
            logger.error(f"Error saving data to MongoDB: {str(e)}")
            raise

    def load(self, query=None, limit=None):
        try:
            if query is None:
                query = {}

            cursor = self.collection.find(query)

            if limit:
                cursor = cursor.limit(limit)

            return list(cursor)
        except Exception as e:
            logger.error(f"Error loading data from MongoDB: {str(e)}")
            raise


def get_storage():
    if STORAGE_TYPE.lower() == 'mongodb':
        return MongoDBStorage()
    else:
        return JSONStorage()