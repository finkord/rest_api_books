from typing import Optional

def build_pagination_links(
    base_url: str,
    limit: int,
    offset: int,
    total: int,
    status: Optional[str] = None,
    author: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_order: str = "asc"
) -> tuple[Optional[str], Optional[str]]:
    """Builds next and prev page links for limit-offset pagination."""
    params = []
    if status: params.append(f"status={status}")
    if author: params.append(f"author={author}")
    if sort_by: params.append(f"sort_by={sort_by}")
    params.append(f"sort_order={sort_order}")
    
    base_query = "&".join(params)
    base_query = f"?{base_query}&" if base_query else "?"

    next_page = None
    if offset + limit < total:
        next_page = f"{base_url}{base_query}limit={limit}&offset={offset + limit}"

    prev_page = None
    if offset > 0:
        prev_offset = max(0, offset - limit)
        prev_page = f"{base_url}{base_query}limit={limit}&offset={prev_offset}"
        
    return next_page, prev_page
