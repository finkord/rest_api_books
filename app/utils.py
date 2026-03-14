import base64
import json
import uuid
import binascii
from typing import Tuple, Optional, Any, Dict

def decode_cursor(cursor: str) -> Tuple[Optional[str], Optional[uuid.UUID]]:
    """Decode a base64 encoded cursor into value and UUID components."""
    try:
        decoded = base64.b64decode(cursor).decode("utf-8")
        cursor_data = json.loads(decoded)
        
        cursor_val = cursor_data.get("val")
        cursor_id = None
        
        if "id" in cursor_data:
            cursor_id = uuid.UUID(cursor_data["id"])
            
        return cursor_val, cursor_id
    except (binascii.Error, json.JSONDecodeError, KeyError, ValueError, UnicodeDecodeError):
        return None, None

def encode_cursor(book_id: uuid.UUID, sort_by: Optional[str] = None, sort_val: Any = None) -> str:
    """Encode a UUID and optional sort value into a base64 cursor."""
    cursor_dict: Dict[str, Any] = {"id": str(book_id)}
    
    if sort_by and sort_val is not None:
        cursor_dict["val"] = sort_val
        
    cursor_json = json.dumps(cursor_dict)
    return base64.b64encode(cursor_json.encode("utf-8")).decode("utf-8")
