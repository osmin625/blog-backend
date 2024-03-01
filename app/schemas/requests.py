from pydantic import BaseModel, validator, HttpUrl
from typing import Optional

class UserRequest(BaseModel):
    user_id: str

class InteractionRequest(BaseModel):
    interaction_id: int

class PageRequest(BaseModel):
    page_id: int

class OutputRequest(UserRequest):
    pass

class ITRCReadtimeRequest(InteractionRequest):
    read_time: int

class ITRCScrollToRequest(InteractionRequest):
    scroll_to: int

class ITRCUpvoteRequest(InteractionRequest):
    upvote: int

class PGUpvoteRequest(PageRequest):
    upvote_cnt: int

class URFunnelRequest(UserRequest):
    funnel: HttpUrl
