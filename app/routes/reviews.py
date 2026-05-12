from fastapi import APIRouter, HTTPException

from app.schemas import ReviewCreateRequest, ReviewResponse, ReviewUpdateRequest
from app.services import reviews as reviewer_service

router = APIRouter()


@router.post("/", response_model=ReviewResponse)
async def create_review(request: ReviewCreateRequest):
    """Create a review from a set of completed extractions, then run LLM analysis."""
    try:
        review = await reviewer_service.create_review(request.extraction_ids)
    except reviewer_service.ExtractionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from None
    except reviewer_service.ExtractionNotCompletedError as e:
        raise HTTPException(status_code=400, detail=str(e)) from None
    return ReviewResponse.from_orm_with_json(review)


@router.get("/{review_id}", response_model=ReviewResponse)
async def get_review(review_id: int):
    """Get a review by ID."""
    review = await reviewer_service.get_review(review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    return ReviewResponse.from_orm_with_json(review)


@router.patch("/{review_id}", response_model=ReviewResponse)
async def update_review(review_id: int, request: ReviewUpdateRequest):
    """Approve or reject a review (human-in-the-loop decision)."""
    try:
        review = await reviewer_service.update_review(
            review_id, request.decision, request.reviewer_notes
        )
    except reviewer_service.ReviewNotFoundError:
        raise HTTPException(status_code=404, detail="Review not found") from None
    except reviewer_service.ReviewNotReadyError as e:
        raise HTTPException(status_code=400, detail=str(e)) from None
    return ReviewResponse.from_orm_with_json(review)


@router.get("/", response_model=list[ReviewResponse])
async def list_reviews():
    """List all reviews."""
    reviews = await reviewer_service.get_all_reviews()
    return [ReviewResponse.from_orm_with_json(r) for r in reviews]
