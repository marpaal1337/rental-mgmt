from typing import Optional

from fastapi import Header, HTTPException, status

from app.config import API_KEY


async def verify_api_key(
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
) -> None:
    if x_api_key is None or x_api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing API key",
        )
