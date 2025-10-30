from fastapi import APIRouter, HTTPException
from sqlalchemy import select, update

from app.models.products import Product as ProductModel
from app.models.categories import Category as CategoryModel
from app.schemas import ProductCreate, Product as ProductSchema
from app.db_depends import AsyncSessionDep

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


@router.post("/", response_model=ProductSchema, status_code=201)
async def create_product(product: ProductCreate, db: AsyncSessionDep):
    """
    Создаёт новый товар.
    """
    category = await db.scalar(
        select(CategoryModel).where(
            CategoryModel.id == product.category_id, CategoryModel.is_active == True
        )
    )
    if not category:
        raise HTTPException(status_code=400, detail="Category not found or inactive")

    db_product = ProductModel(**product.model_dump())
    db.add(db_product)
    await db.commit()
    await db.refresh(db_product)
    return db_product


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


@router.put("/{product_id}", response_model=ProductSchema, status_code=200)
async def update_product(
    product_id: int, productupdate: ProductCreate, db: AsyncSessionDep
):
    """
    Обновляет товар по его ID.
    """
    category = await db.scalar(
        select(CategoryModel).where(
            CategoryModel.id == productupdate.category_id,
            CategoryModel.is_active == True,
        )
    )
    if not category:
        raise HTTPException(status_code=404, detail="Category not found or inactive")
    product = await db.scalar(
        select(ProductModel).where(
            ProductModel.id == product_id, ProductModel.is_active == True
        )
    )
    if not product:
        raise HTTPException(status_code=404, detail="Product not found or inactive")

    await db.execute(
        update(ProductModel)
        .where(ProductModel.id == product_id)
        .values(**productupdate.model_dump(exclude_unset=True))
    )
    await db.commit()
    await db.refresh(product)
    return product


@router.delete("/{product_id}")
async def delete_product(product_id: int, db: AsyncSessionDep):
    """
    Удаляет товар по его ID.
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
        raise HTTPException(status_code=404, detail="Category not found or inactive")
    product.is_active = False
    await db.commit()

    return product
