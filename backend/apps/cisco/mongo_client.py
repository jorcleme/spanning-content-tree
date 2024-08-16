import os
from typing import Union, List, Dict, Any
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from pymongo.collection import Collection
from pymongo.command_cursor import CommandCursor
from pymongo.typings import _Pipeline, _DocumentType
from bson.raw_bson import RawBSONDocument
from bson import ObjectId
from config import MONGODB_URI, MONGODB_USER, MONGODB_PASS


class MongoDbClient:

    # Database Name
    DB_NAME = "smb_documents"

    # Database Collections
    ARTICLES = "articles"
    ADMIN_GUIDES = "admin_guides"
    CLI_GUIDES = "cli_guides"
    DATASOURCE = "datasources"
    PRODUCT_FAMILIES = "product_families"
    VIDEOS = "videos"

    COLLECTION_NAMES = [
        ARTICLES,
        ADMIN_GUIDES,
        CLI_GUIDES,
        DATASOURCE,
        PRODUCT_FAMILIES,
        VIDEOS,
    ]

    # Database Search and Vector Indexes
    ATLAS_VECTOR_SEARCH_INDEX_NAME = "admin_guide_vector_search"
    ARTICLES_SEARCH_INDEX_NAME = "articles_search_index"
    VIDEOS_SEARCH_INDEX_NAME = "videos_search_index"

    def __init__(self):
        self.client = MongoClient(
            MONGODB_URI.replace("<username>", MONGODB_USER).replace(
                "<password>", MONGODB_PASS
            ),
            server_api=ServerApi("1"),
        )

        self.db = self.client[self.DB_NAME]
        self.collections = {name: self.db[name] for name in self.COLLECTION_NAMES}

    def _prepare_query(self, query: dict) -> dict:
        if "_id" in query and isinstance(query["_id"], str):
            query["_id"] = ObjectId(query["_id"])
        return query

    def aggregate(self, collection_name: str, pipeline: _Pipeline) -> CommandCursor:
        collection = self.collections[collection_name]
        return list(collection.aggregate(pipeline))

    def insert_one(
        self, collection_name: str, document: Union[_DocumentType, RawBSONDocument]
    ):
        collection = self.collections[collection_name]
        result = collection.insert_one(document)
        return str(result.inserted_id)

    def find(self, collection_name: str, query: dict) -> List[Dict[str, Any]]:
        query = self._prepare_query(query)
        collection = self.collections[collection_name]
        return list(collection.find(query))

    def update_one(self, collection_name: str, query: dict, update: dict):
        query = self._prepare_query(query)
        collection = self.collections[collection_name]
        result = collection.update_one(query, {"$set": update})
        return result.modified_count > 0

    def delete_one(self, collection_name: str, query: dict):
        query = self._prepare_query(query)
        collection = self.collections[collection_name]
        result = collection.delete_one(query)
        return result.deleted_count > 0
