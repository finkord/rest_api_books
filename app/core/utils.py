import urllib.parse
from fastapi import Request
from typing import Optional, Dict

def generate_pagination_links(request: Request, total: int, limit: int, offset: int) -> dict[str, Optional[str]]:
    """Helper utility for generating next and previous pagination links."""
    base_url = str(request.url.replace(query=""))
    query_params = dict(request.query_params)
    
    next_page = None
    if offset + limit < total:
        next_params = {**query_params, "limit": limit, "offset": offset + limit}
        next_page = f"{base_url}?{urllib.parse.urlencode(next_params)}"

    prev_page = None
    if offset > 0:
        prev_offset = max(0, offset - limit)
        prev_params = {**query_params, "limit": limit, "offset": prev_offset}
        prev_page = f"{base_url}?{urllib.parse.urlencode(prev_params)}"
        
    return {
        "next_page": next_page,
        "prev_page": prev_page
    }
