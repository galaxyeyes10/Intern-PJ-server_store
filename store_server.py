from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from model import ReviewTable, UserTable, StoreTable, MenuTable
from db import session
from fastapi.middleware.cors import CORSMiddleware
import os
import uvicorn

store = FastAPI()

store.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False, 
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = session()
    try:
        yield db
    finally:
        db.close()

#가게 별점 반환
@store.get("/rating/{store_id}")
async def read_rating(store_id: str, db: Session = Depends(get_db)):
    store = db.query(StoreTable).filter(StoreTable.store_id == store_id).first()
    
    return store.average_rating

#메뉴 사진, 메뉴 이름, 메뉴 설명, 가격 딕셔너리 반환
@store.get("/menus/{store_id}")
async def read_review_history(store_id: str, db: Session = Depends(get_db)):
    menus = db.query(
                        MenuTable.menu_img,
                        MenuTable.menu_name,
                        MenuTable.description,
                        MenuTable.price
                    ).join(StoreTable, MenuTable.store_id == StoreTable.store_id).filter(MenuTable.store_id == store_id, MenuTable.is_main == "true").all()
    
    menu_info = [
        {
            "menu_img": menu.menu_img,
            "menu_name": menu.menu_name,
            "description": menu.description,
            "price": menu.price,
        }
        for menu in menus
    ]

    return menu_info

if __name__ == "__store__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port)