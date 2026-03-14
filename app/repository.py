from typing import List, Optional, Dict, Any
from bson import ObjectId
from app.models import books_collection

class Repository:
    def __init__(self, db=None):
        pass

    async def get_all(
        self,
        status: Optional[str] = None,
        author: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
        limit: int = 10,
        offset: int = 0
    ) -> tuple[List[Dict[str, Any]], int]:
        filter_query = {}
        if status:
            filter_query["status"] = status
        if author:
            filter_query["author"] = author

        sort_criteria = None
        if sort_by in ["title", "year_published"]:
            sort_direction = -1 if sort_order == "desc" else 1
            sort_criteria = [(sort_by, sort_direction)]

        total_count = await books_collection.count_documents(filter_query)
        
        cursor = books_collection.find(filter_query)
        if sort_criteria:
            cursor = cursor.sort(sort_criteria)
            
        cursor = cursor.skip(offset).limit(limit)
        
        docs = await cursor.to_list(length=limit)
        
        # map _id to id as string
        for doc in docs:
            doc["id"] = str(doc.pop("_id"))
            
        return docs, total_count

    async def get_by_id(self, book_id: str) -> Optional[Dict[str, Any]]:
        try:
            obj_id = ObjectId(book_id)
        except Exception:
            return None
            
        doc = await books_collection.find_one({"_id": obj_id})
        if doc:
            doc["id"] = str(doc.pop("_id"))
        return doc

    async def create(self, book_dict: Dict[str, Any]) -> Dict[str, Any]:
        result = await books_collection.insert_one(book_dict)
        book_dict["id"] = str(result.inserted_id)
        if "_id" in book_dict:
            del book_dict["_id"]
        return book_dict

    async def delete(self, book_id: str) -> bool:
        try:
            obj_id = ObjectId(book_id)
        except Exception:
            return False
            
        result = await books_collection.delete_one({"_id": obj_id})
        return result.deleted_count > 0
