from typing import List, Optional

from pydantic import BaseModel


class SequenceRecommendRequest(BaseModel):
    """Sequence item_id tam thoi dung cho demo goi y realtime."""

    sequence: List[int]
    top_k: Optional[int] = 12


class RecommendRequest(BaseModel):
    """Request legacy cho frontend cu gui lich su item_id."""

    sequence_history: List[int]
    top_k: Optional[int] = 10

