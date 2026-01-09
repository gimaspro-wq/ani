"""Library repository implementation."""
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import UserLibraryItem, LibraryStatus, normalize_library_status
from app.domain.entities import UserLibraryItem as DomainLibraryItem
from app.domain.enums import LibraryStatus as DomainLibraryStatus
from app.domain.interfaces.repositories import ILibraryRepository


class LibraryRepository(ILibraryRepository):
    """Library repository implementation."""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def _to_library_status(
        status: LibraryStatus | DomainLibraryStatus | str | None,
    ) -> DomainLibraryStatus:
        if isinstance(status, DomainLibraryStatus):
            return status
        if isinstance(status, LibraryStatus):
            return DomainLibraryStatus(status.value)
        if status is None:
            raise ValueError("Library status cannot be None")
        return DomainLibraryStatus(status)

    def _to_library_domain(self, item: UserLibraryItem | None) -> DomainLibraryItem | None:
        if item is None:
            return None
        return DomainLibraryItem(
            id=item.id,
            user_id=item.user_id,
            provider=item.provider,
            title_id=item.title_id,
            status=self._to_library_status(item.status),
            is_favorite=item.is_favorite,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )

    async def get_user_library(
        self,
        user_id: int,
        provider: str = "rpc",
        status_filter: Optional[DomainLibraryStatus] = None,
        favorites_only: bool = False
    ) -> List[DomainLibraryItem]:
        """Get user's library items."""
        query = select(UserLibraryItem).where(
            and_(
                UserLibraryItem.user_id == user_id,
                UserLibraryItem.provider == provider
            )
        )
        
        if status_filter:
            query = query.where(UserLibraryItem.status == status_filter.value)
        
        if favorites_only:
            query = query.where(UserLibraryItem.is_favorite == True)
        
        query = query.order_by(UserLibraryItem.updated_at.desc())
        result = await self.db.execute(query)
        items = result.scalars().all()
        return [item for item in (self._to_library_domain(obj) for obj in items) if item is not None]
    
    async def get_library_item(
        self,
        user_id: int,
        title_id: str,
        provider: str = "rpc"
    ) -> Optional[DomainLibraryItem]:
        """Get specific library item."""
        model = await self._get_library_model(user_id, title_id, provider)
        return self._to_library_domain(model)

    async def _get_library_model(
        self,
        user_id: int,
        title_id: str,
        provider: str = "rpc"
    ) -> UserLibraryItem | None:
        query = select(UserLibraryItem).where(
            and_(
                UserLibraryItem.user_id == user_id,
                UserLibraryItem.provider == provider,
                UserLibraryItem.title_id == title_id,
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def upsert_library_item(
        self,
        user_id: int,
        title_id: str,
        status: Optional[DomainLibraryStatus] = None,
        is_favorite: Optional[bool] = None,
        provider: str = "rpc"
    ) -> DomainLibraryItem:
        """Create or update library item."""
        item = await self._get_library_model(user_id, title_id, provider)
        
        if item:
            # Update existing
            if status is not None:
                item.status = normalize_library_status(status.value)
            if is_favorite is not None:
                item.is_favorite = is_favorite
            item.updated_at = datetime.now(timezone.utc)
        else:
            # Create new
            item = UserLibraryItem(
                user_id=user_id,
                provider=provider,
                title_id=title_id,
                status=normalize_library_status(
                    status.value if status else DomainLibraryStatus.WATCHING.value
                ),
                is_favorite=is_favorite or False
            )
            self.db.add(item)
        
        await self.db.commit()
        await self.db.refresh(item)
        domain_item = self._to_library_domain(item)
        assert domain_item is not None
        return domain_item
    
    async def delete_library_item(
        self,
        user_id: int,
        title_id: str,
        provider: str = "rpc"
    ) -> bool:
        """Delete library item."""
        item = await self._get_library_model(user_id, title_id, provider)
        if item:
            await self.db.delete(item)
            await self.db.commit()
            return True
        return False
