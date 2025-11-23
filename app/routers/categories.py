from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select, update

from app.models.categories import Category as CategoryModel
from app.schemas import Category as CategorySchema, CategoryCreate

from app.db_depends import AsyncSessionDep

router = APIRouter(
    prefix="/categories",
    tags=["categories"],
)


@router.get("/", response_model=list[CategorySchema])
async def get_all_categories(db: AsyncSessionDep):
    """
    Возвращает список всех активных категорий.
    """
    return (
        await db.scalars(select(CategoryModel).where(CategoryModel.is_active == True))
    ).all()


@router.post("/", response_model=CategorySchema, status_code=status.HTTP_201_CREATED)
async def create_category(category: CategoryCreate, db: AsyncSessionDep):
    """
    Создаёт новую категорию.
    """
    if category.parent_id is not None:
        parent = await db.scalar(
            select(CategoryModel).where(
                CategoryModel.id == category.parent_id, CategoryModel.is_active == True
            )
        )
        if parent is None:
            raise HTTPException(status_code=400, detail="Parent category not found")

    db_category = CategoryModel(**category.model_dump())
    db.add(db_category)
    await db.commit()
    await db.refresh(db_category)
    return db_category


@router.put("/{category_id}", response_model=CategorySchema)
async def update_category(
    category_id: int, category: CategoryCreate, db: AsyncSessionDep
):
    """
    Обновляет категорию по её ID.
    """
    db_category = await db.scalar(
        select(CategoryModel).where(
            CategoryModel.id == category_id, CategoryModel.is_active == True
        )
    )

    if db_category is None:
        raise HTTPException(status_code=404, detail="Category not found")

    if category.parent_id is not None:
        parent = await db.scalar(
            select(CategoryModel).where(
                CategoryModel.id == category.parent_id,
                CategoryModel.is_active == True,
            )
        )

        if parent is None:
            raise HTTPException(status_code=404, detail="Parent category not found")
    await db.execute(
        update(CategoryModel)
        .where(CategoryModel.id == category_id)
        .values(**category.model_dump(exclude_unset=True))
    )
    await db.commit()
    await db.refresh(db_category)
    return db_category


@router.delete("/{category_id}", status_code=status.HTTP_200_OK)
async def delete_category(category_id: int, db: AsyncSessionDep):
    """
    Логически удаляет категорию по её ID, устанавливая is_active=False.
    """
    category = await db.scalar(
        select(CategoryModel).where(
            CategoryModel.id == category_id, CategoryModel.is_active == True
        )
    )

    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")

    category.is_active = False
    await db.commit()

    return category
