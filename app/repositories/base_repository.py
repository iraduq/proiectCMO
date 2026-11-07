from typing import Any, Generic, Optional, Sequence, TypeVar
from sqlalchemy import Select, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import Base
from app.exceptions.exceptions import DataIntegrityError

ModelT = TypeVar("ModelT", bound=Base)

def like_pattern(term: str) -> str:
    escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"

class BaseRepository(Generic[ModelT]):
    model: type[ModelT]
    detail_options: tuple[Any, ...] = ()

    async def get_by_id(self, db: AsyncSession, entity_id: int) -> Optional[ModelT]:
        result = await db.execute(select(self.model).where(self.model.id == entity_id))
        return result.scalars().first()

    async def get_detailed(self, db: AsyncSession, entity_id: int) -> Optional[ModelT]:
        stmt = (
            select(self.model)
            .where(self.model.id == entity_id)
            .options(*self.detail_options)
            .execution_options(populate_existing=True)
        )
        result = await db.execute(stmt)
        return result.unique().scalars().first()

    async def add(self, db: AsyncSession, entity: ModelT) -> ModelT:
        db.add(entity)
        await self.flush(db)
        return entity

    async def flush(self, db: AsyncSession) -> None:
        try:
            await db.flush()
        except IntegrityError as exc:
            raise DataIntegrityError() from exc

    async def delete(self, db: AsyncSession, entity: ModelT) -> None:
        await db.delete(entity)
        await self.flush(db)

    async def exists_unique(
        self,
        db: AsyncSession,
        column_name: str,
        value: str,
        exclude_id: Optional[int] = None,
        **scope: Any,
    ) -> bool:
        column = getattr(self.model, column_name)
        stmt = select(func.count()).select_from(self.model).where(func.lower(column) == value.lower())
        for key, scope_value in scope.items():
            stmt = stmt.where(getattr(self.model, key) == scope_value)
        if exclude_id is not None:
            stmt = stmt.where(self.model.id != exclude_id)
        result = await db.execute(stmt)
        return result.scalar_one() > 0

    async def count_where(self, db: AsyncSession, *conditions: Any) -> int:
        stmt = select(func.count()).select_from(self.model)
        for condition in conditions:
            stmt = stmt.where(condition)
        result = await db.execute(stmt)
        return result.scalar_one()

    async def paginate(
        self,
        db: AsyncSession,
        base_stmt: Select,
        order_by: Sequence[Any],
        skip: int,
        limit: int,
    ) -> tuple[list[ModelT], int]:
        count_stmt = select(func.count()).select_from(base_stmt.order_by(None).subquery())
        total = (await db.execute(count_stmt)).scalar_one()
        page_stmt = (
            base_stmt.options(*self.detail_options)
            .order_by(*order_by)
            .offset(skip)
            .limit(limit)
            .execution_options(populate_existing=True)
        )
        result = await db.execute(page_stmt)
        return list(result.unique().scalars().all()), total
