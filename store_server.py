from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from model import ReviewTable, UserTable, StoreTable, MenuTable, OrderTable
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
                    ).join(StoreTable, MenuTable.store_id == StoreTable.store_id).filter(MenuTable.store_id == store_id, MenuTable.is_main == True).all()
    
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

# 총 수량 반환
@store.get("/total_count/{user_id}")
async def read_total_count(user_id: str, db: Session = Depends(get_db)):
    orders = db.query(
                        OrderTable.quantity,
                        OrderTable.is_completed,
                        UserTable.user_id
                    ).join(UserTable, UserTable.user_id == OrderTable.user_id).filter(OrderTable.user_id == user_id, OrderTable.is_completed == False).all()
    
    counts = [row[0] for row in orders] 
    total = sum(counts)
    
    return total

# 장바구니 +버튼 처리
@store.put("/order/increase/{user_id}/{store_id}/{menu_id}")
async def increase_order_quantity(user_id: str, menu_id: int, store_id: int, db: Session = Depends(get_db)):
    order = db.query(OrderTable).filter(OrderTable.user_id == user_id).first()
    
    if order:
        order.quantity += 1
        db.commit()
        db.refresh(order)

    else:
        new_order = OrderTable(
            user_id=user_id,
            store_id = store_id,
            menu_id=menu_id,
            quantity=1,
            is_completed=False,
        )
        db.add(new_order)
        db.commit()
        db.refresh(new_order)

#장바구니 -버튼 처리
@store.put("/order/decrease/{order_id}")
async def decrease_order_quantity(order_id: int, db: Session = Depends(get_db)):
    order = db.query(OrderTable).filter(OrderTable.order_id == order_id, OrderTable.is_completed == False).first()
    
    if order:
        order.quantity -= 1
        
        if order.quantity <= 0:
            db.delete(order)
    
        db.commit()
        db.refresh(order)

if __name__ == "__store__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port)