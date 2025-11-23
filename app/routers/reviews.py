from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from app.models.reviews import Review as ReviewModel
from app.schemas import ReviewCreate, Review as ReviewSchema
from app.db_depends import AsyncSessionDep
from app.models.products import Product as ProductModel
from app.models.users import User as UserModel

from app.auth import get_current_buyer, get_current_admin

router = APIRouter(tags=["reviews"])


async def update_product_rating(db: AsyncSession, product_id: int):
    result = await db.execute(
        select(func.avg(ReviewModel.grade)).where(
            ReviewModel.product_id == product_id, ReviewModel.is_active == True
        )
    )
    avg_rating = result.scalar() or 0.0
    product = await db.get(ProductModel, product_id)
    product.rating = avg_rating
    await db.commit()


@router.get("/reviews/", response_model=list[ReviewSchema], status_code=200)
async def get_reviews(db: AsyncSessionDep):
    return (
        await db.scalars(select(ReviewModel).where(ReviewModel.is_active == True))
    ).all()


@router.get(
    "/products/{product_id}/reviews/",
    response_model=list[ReviewSchema],
    status_code=200,
)
async def get_reviews_product(product_id: int, db: AsyncSessionDep):
    product = await db.scalar(
        select(ProductModel).where(
            ProductModel.id == product_id, ProductModel.is_active == True
        )
    )
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    reviews = (
        await db.scalars(
            select(ReviewModel).where(
                ReviewModel.product_id == product_id, ReviewModel.is_active == True
            )
        )
    ).all()

    return reviews


@router.post("/reviews/", response_model=ReviewSchema, status_code=201)
async def create_review(
    review: ReviewCreate,
    db: AsyncSessionDep,
    buyer: UserModel = Depends(get_current_buyer),
):

    product_db = await db.scalar(
        select(ProductModel).where(
            ProductModel.id == review.product_id, ProductModel.is_active == True
        )
    )
    if not product_db:
        raise HTTPException(status_code=404, detail="Product not found")
    existing_review = await db.scalar(
        select(ReviewModel).where(
            ReviewModel.user_id == buyer.id, ReviewModel.product_id == review.product_id
        )
    )
    if existing_review:
        raise HTTPException(
            status_code=400, detail="You have already reviewed this product"
        )
    review_db = ReviewModel(
        user_id=buyer.id,
        product_id=review.product_id,
        comment=review.comment,
        grade=review.grade,
    )
    db.add(review_db)
    await db.commit()
    await db.refresh(review_db)
    await update_product_rating(db, review.product_id)
    return review_db


@router.delete("/reviews/{review_id}")
async def delete_review(
    review_id: int, db: AsyncSessionDep, admin: UserModel = Depends(get_current_admin)
):
    review = await db.scalar(
        select(ReviewModel).where(
            ReviewModel.id == review_id, ReviewModel.is_active == True
        )
    )
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    product_id = review.product_id
    review.is_active = False
    await db.commit()
    await update_product_rating(db, product_id)
    return {"message": "Review deleted"}
