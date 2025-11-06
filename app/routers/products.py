from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.users import User as UserModel
from app.auth import get_current_seller
from app.models.products import Product as ProductModel
from app.models.categories import Category as CategoryModel
from app.schemas import ProductCreate, Product as ProductSchema
from app.db_depends import AsyncSessionDep, get_async_db

router = APIRouter(
    prefix="/products",
    tags=["products"],
)


@router.get("/", response_model=list[ProductSchema], status_code=200)
async def get_all_products(db: AsyncSessionDep):
    """
    Возвращает список всех товаров.
    """
    return (
        await db.scalars(select(ProductModel).where(ProductModel.is_active == True))
    ).all()


@router.get(
    "/category/{category_id}", status_code=200, response_model=list[ProductSchema]
)
async def get_products_by_category(category_id: int, db: AsyncSessionDep):
    """
    Возвращает список товаров в указанной категории по её ID.
    """
    category = await db.scalar(
        select(CategoryModel).where(
            CategoryModel.id == category_id, CategoryModel.is_active == True
        )
    )
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    return (
        await db.scalars(
            select(ProductModel).where(
                ProductModel.category_id == category_id, ProductModel.is_active == True
            )
        )
    ).all()


@router.get("/{product_id}", response_model=ProductSchema, status_code=200)
async def get_product(product_id: int, db: AsyncSessionDep):
    """
    Возвращает детальную информацию о товаре по его ID.
    """
    product = await db.scalar(
        select(ProductModel).where(
            ProductModel.id == product_id, ProductModel.is_active == True
        )
    )
    if not product:
        raise HTTPException(status_code=404, detail="Product not found or inactive")
    category = await db.scalar(
        select(CategoryModel).where(
            CategoryModel.id == product.category_id, CategoryModel.is_active == True
        )
    )
    if not category:
        raise HTTPException(status_code=400, detail="Category not found or inactive")
    return product


@router.post("/", response_model=ProductSchema, status_code=201)
async def create_product(
    product: ProductCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_seller),
):
    """
    Создаёт новый товар, привязанный к текущему продавцу (только для 'seller').
    """
    category_result = await db.scalars(
        select(CategoryModel).where(
            CategoryModel.id == product.category_id, CategoryModel.is_active == True
        )
    )
    if not category_result.first():
        raise HTTPException(status_code=400, detail="Category not found or inactive")
    db_product = ProductModel(**product.model_dump(), seller_id=current_user.id)
    db.add(db_product)
    await db.commit()
    await db.refresh(db_product)
    return db_product


@router.put("/{product_id}", response_model=ProductSchema)
async def update_product(
    product_id: int,
    product: ProductCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_seller),
):
    """
    Обновляет товар, если он принадлежит текущему продавцу (только для 'seller').
    """
    result = await db.scalars(select(ProductModel).where(ProductModel.id == product_id))
    db_product = result.first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    if db_product.seller_id != current_user.id:
        raise HTTPException(
            status_code=404, detail="You can only update your own products"
        )
    category_result = await db.scalars(
        select(CategoryModel).where(
            CategoryModel.id == product.category_id, CategoryModel.is_active == True
        )
    )
    if not category_result.first():
        raise HTTPException(status_code=400, detail="Category not found or inactive")
    await db.execute(
        update(ProductModel)
        .where(ProductModel.id == product_id)
        .values(**product.model_dump())
    )
    await db.commit()
    await db.refresh(db_product)
    return db_product


@router.delete("/{product_id}", response_model=ProductSchema)
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_seller),
):
    """
    Выполняет мягкое удаление товара, если он принадлежит текущему продавцу (только для 'seller').
    """
    result = await db.scalars(
        select(ProductModel).where(
            ProductModel.id == product_id, ProductModel.is_active == True
        )
    )
    product = result.first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found or inactive")
    if product.seller_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="You can only delete your own products"
        )
    await db.execute(
        update(ProductModel)
        .where(ProductModel.id == product_id)
        .values(is_active=False)
    )
    await db.commit()
    await db.refresh(product)
    return product
