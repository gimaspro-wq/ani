"""Library repository implementation."""
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import UserLibraryItem, LibraryStatus, normalize_library_status
from app.domain.interfaces.repositories import ILibraryRepository


class LibraryRepository(ILibraryRepository):
    """Library repository implementation."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_user_library(
        self,
        user_id: int,
        provider: str = "rpc",
        status_filter: Optional[LibraryStatus] = None,
        favorites_only: bool = False
    ) -> List[UserLibraryItem]:
        """Get user's library items."""
        query = select(UserLibraryItem).where(
            and_(
                UserLibraryItem.user_id == user_id,
                UserLibraryItem.provider == provider
            )
        )
        
        if status_filter:
            query = query.where(UserLibraryItem.status == status_filter)
        
        if favorites_only:
            query = query.where(UserLibraryItem.is_favorite == True)
        
        query = query.order_by(UserLibraryItem.updated_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_library_item(
        self,
        user_id: int,
        title_id: str,
        provider: str = "rpc"
    ) -> Optional[UserLibraryItem]:
        """Get specific library item."""
        query = select(UserLibraryItem).where(
            and_(
                UserLibraryItem.user_id == user_id,
                UserLibraryItem.provider == provider,
                UserLibraryItem.title_id == title_id
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def upsert_library_item(
        self,
        user_id: int,
        title_id: str,
        status: Optional[LibraryStatus] = None,
        is_favorite: Optional[bool] = None,
        provider: str = "rpc"
    ) -> UserLibraryItem:
        """Create or update library item."""
        item = await self.get_library_item(user_id, title_id, provider)
        
        if item:
            # Update existing
            if status is not None:
                item.status = normalize_library_status(status)
            if is_favorite is not None:
                item.is_favorite = is_favorite
            item.updated_at = datetime.now(timezone.utc)
        else:
            # Create new
            item = UserLibraryItem(
                user_id=user_id,
                provider=provider,
                title_id=title_id,
                status=normalize_library_status(status) or LibraryStatus.WATCHING.value,
                is_favorite=is_favorite or False
            )
            self.db.add(item)
        
        await self.db.commit()
        await self.db.refresh(item)
        return item
    
    async def delete_library_item(
        self,
        user_id: int,
        title_id: str,
        provider: str = "rpc"
    ) -> bool:
        """Delete library item."""
        item = await self.get_library_item(user_id, title_id, provider)
        if item:
            await self.db.delete(item)
            await self.db.commit()
            return True
        return False
