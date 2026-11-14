"""AI order insights endpoint (customers only)."""
from fastapi import APIRouter, Depends
from openai import OpenAI
from sqlalchemy.orm import Session

from ..constants import Role
from ..database import get_db
from ..models import User
from ..schemas import AIAnswer, AIQuery
from ..security import require_roles
from ..services.ai import (
    NO_ORDERS_ANSWER,
    ask_openai,
    build_order_context,
    enforce_user_rate_limit,
    get_ai_client,
)

router = APIRouter(prefix="/ai", tags=["AI insights"])


@router.post("/insights", response_model=AIAnswer)
def order_insights(
    payload: AIQuery,
    db: Session = Depends(get_db),
    customer: User = Depends(require_roles(Role.CUSTOMER)),
):
    # 1. Throttle per customer (before doing any work or spending any tokens)
    enforce_user_rate_limit(customer.id)

    # 2. Load ONLY this customer's orders (id comes from the JWT, not the request)
    context, order_count = build_order_context(db, customer.id, payload.tz_offset)
    if order_count == 0:
        return AIAnswer(answer=NO_ORDERS_ANSWER, orders_considered=0)

    # 3. Ask OpenAI (resolved lazily so a missing key only affects customers with orders)
    client: OpenAI = get_ai_client()
    answer = ask_openai(client, context, payload.question.strip())
    return AIAnswer(answer=answer, orders_considered=order_count)
