"""Evaluation endpoints."""

from fastapi import APIRouter, HTTPException
from backend.services.evaluation_service import run_evaluation, get_last_evaluation_results
from backend.utils.logger import get_logger

logger = get_logger("api.evaluation")
router = APIRouter(prefix="/api/evaluation", tags=["Evaluation"])


@router.post("/run")
def run_eval():
    """Run the full evaluation suite against test cases."""
    logger.info("Starting evaluation run...")
    results = run_evaluation()
    logger.info(f"Evaluation complete: {results['correct']}/{results['total']} correct ({results['accuracy']*100:.1f}%)")
    return results


@router.get("/results")
def get_eval_results():
    """Get the most recent evaluation results."""
    results = get_last_evaluation_results()
    if results is None:
        raise HTTPException(
            status_code=404,
            detail="No evaluation results yet. Run POST /api/evaluation/run first.",
        )
    return results
