from fastapi import APIRouter, Request, Depends, BackgroundTasks, Body, status
from schemas.responses import BaseResponse
from schemas.requests import UserRequest, UserCollection
from core.events import request_handler
from sqlalchemy.orm import Session
from database.db import db,collection

router = APIRouter()


@router.post(
    '/id',
    response_description="Add new user",
    response_model=BaseResponse,
    status_code=status.HTTP_201_CREATED,
)
async def post_user_id(user: UserRequest = Body(...)):
    new_user = await collection.insert_one(
        user.model_dump(by_alias=True, exclude=["id"])
    )
    created_user = await collection.find_one(
        {"_id": new_user.inserted_id}
    )
    return created_user
    # background_tasks.add_task(save_user_info, user_id, db)
    # return BaseResponse