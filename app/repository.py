from typing import List, Optional, Dict, Any
from bson import ObjectId
from app.schemas import BookQueryParams

class Repository:
    def __init__(self, collection):
        self.collection = collection

    async def get_all(self, params: BookQueryParams) -> tuple[List[Dict[str, Any]], int]:
        filter_query = {}
        if params.status:
            filter_query["status"] = params.status
        if params.author:
            filter_query["author"] = params.author

        sort_criteria = None
        if params.sort_by in ["title", "year_published"]:
            sort_direction = -1 if params.sort_order == "desc" else 1
            sort_criteria = [(params.sort_by, sort_direction)]

        total_count = await self.collection.count_documents(filter_query)
        
        cursor = self.collection.find(filter_query)
        if sort_criteria:
            cursor = cursor.sort(sort_criteria)
            
        cursor = cursor.skip(params.offset).limit(params.limit)
        
        docs = await cursor.to_list(length=params.limit)
        
        # map _id to id as string
        for doc in docs:
            doc["id"] = str(doc.pop("_id"))
            
        return docs, total_count

    async def get_by_id(self, book_id: str) -> Optional[Dict[str, Any]]:
        try:
            obj_id = ObjectId(book_id)
        except Exception:
            return None
            
        doc = await self.collection.find_one({"_id": obj_id})
        if doc:
            doc["id"] = str(doc.pop("_id"))
        return doc

    async def create_many(self, books_dicts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not books_dicts:
            return []
        result = await self.collection.insert_many(books_dicts)
        for doc, _id in zip(books_dicts, result.inserted_ids):
            doc["id"] = str(_id)
            if "_id" in doc:
                del doc["_id"]
        return books_dicts

    async def delete(self, book_id: str) -> bool:
        try:
            obj_id = ObjectId(book_id)
        except Exception:
            return False
            
        result = await self.collection.delete_one({"_id": obj_id})
        return result.deleted_count > 0
