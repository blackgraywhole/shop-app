from fastapi import APIRouter, HTTPException
from sqlalchemy import select, update

from app.db_depends import SessionDep
from app.models.products import Product as ProductModel
from app.models.categories import Category as CategoryModel
from app.schemas import ProductCreate, Product as ProductSchema

router = APIRouter(
    prefix="/products",
    tags=["products"],
)


@router.get("/", response_model=list[ProductSchema], status_code=200)
async def get_all_products(db: SessionDep):
    """
    Возвращает список всех товаров.
    """
    products = db.scalars(
        select(ProductModel).where(ProductModel.is_active == True)
    ).all()
    return products


@router.post("/", response_model=ProductSchema, status_code=201)
async def create_product(product: ProductCreate, db: SessionDep):
    """
    Создаёт новый товар.
    """
    category = db.scalars(
        select(CategoryModel).where(
            CategoryModel.id == product.category_id, CategoryModel.is_active == True
        )
    ).first()
    if not category:
        raise HTTPException(status_code=400, detail="Category not found or inactive")

    db_product = ProductModel(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


@router.get(
    "/category/{category_id}", status_code=200, response_model=list[ProductSchema]
)
async def get_products_by_category(category_id: int, db: SessionDep):
    """
    Возвращает список товаров в указанной категории по её ID.
    """
    category = db.scalars(
        select(CategoryModel).where(
            CategoryModel.id == category_id, CategoryModel.is_active == True
        )
    ).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    products = db.scalars(
        select(ProductModel).where(
            ProductModel.category_id == category_id, ProductModel.is_active == True
        )
    ).all()
    return products


@router.get("/{product_id}", response_model=ProductSchema, status_code=200)
async def get_product(product_id: int, db: SessionDep):
    """
    Возвращает детальную информацию о товаре по его ID.
    """
    product = db.scalars(
        select(ProductModel).where(
            ProductModel.id == product_id, ProductModel.is_active == True
        )
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found or inactive")
    category = db.scalars(
        select(CategoryModel).where(
            CategoryModel.id == product.category_id, CategoryModel.is_active == True
        )
    ).first()
    if not category:
        raise HTTPException(status_code=400, detail="Category not found or inactive")
    return product


@router.put("/{product_id}", response_model=ProductSchema, status_code=200)
async def update_product(product_id: int, product: ProductCreate, db: SessionDep):
    """
    Обновляет товар по его ID.
    """
    category = db.scalars(
        select(CategoryModel).where(
            CategoryModel.id == product.category_id, CategoryModel.is_active == True
        )
    ).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found or inactive")
    product_db = db.scalars(
        select(ProductModel).where(
            ProductModel.id == product_id, ProductModel.is_active == True
        )
    ).first()

    if not product_db:
        raise HTTPException(status_code=404, detail="Product not found or inactive")

    db.execute(
        update(ProductModel)
        .where(ProductModel.id == product_id)
        .values(**product.model_dump())
    )
    db.commit()
    db.refresh(product_db)
    return product_db


@router.delete("/{product_id}")
async def delete_product(product_id: int, db: SessionDep):
    """
    Удаляет товар по его ID.
    """
    product = db.scalars(
        select(ProductModel).where(
            ProductModel.id == product_id, ProductModel.is_active == True
        )
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found or inactive")
    product.is_active = False
    db.commit()

    return {"status": "success", "message": "Product marked as inactive"}
