from fastapi import FastAPI, Depends, Request, Body
from sqlalchemy.orm import Session
from model import ReviewTable, UserTable, StoreTable, MenuTable, OrderTable
from db import session
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
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

store.add_middleware(SessionMiddleware, secret_key="your-secret-key")

def get_db():
    db = session()
    try:
        yield db
    finally:
        db.close()

#로그인 상태 확인, 로그인 중인 유저 아이디 반환
@store.get("/check_login/")
async def check_login(request: Request):
    # 세션에서 사용자 정보 확인
    if "user_id" not in request.session:
        return False
    
    return {"user_id": f"{request.session['user_id']}"}

#가게 아이디로 모든 메뉴 아이디 반환
@store.get("/menu_ids/{store_id}")
async def get_menu_ids(store_id: int, db: Session = Depends(get_db)):
    menu_ids = db.query(MenuTable.menu_id).filter(MenuTable.store_id == store_id).all()
    
    return {"menu_ids": [menu_id[0] for menu_id in menu_ids]}

#is_completed가 false인 order들의 order_id를 리스트로 반환
@store.get("/order/active_order_ids/{user_id}")
async def get_active_order_ids(user_id: str, db: Session = Depends(get_db)):
    order_ids = db.query(OrderTable.order_id).filter(OrderTable.user_id == user_id, OrderTable.is_completed == False).all()
    
    return {"order_ids": [order_id[0] for order_id in order_ids]}

#가게 별점 반환
@store.get("/rating/{store_id}")
async def average_rating(store_id: int, db: Session = Depends(get_db)):
    reviews = db.query(ReviewTable).filter(ReviewTable.store_id == store_id).all()
    ratings = [row.rating for row in reviews]
    average = sum(ratings) / len(ratings)
    return round(average, 1)

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

# 장바구니 +버튼 처리, 새로운 주문의 order_id반환
@store.post("/order/increase/")
async def increase_order_quantity(user_id: str = Body(...), menu_id: int = Body(...), store_id: int = Body(...), db: Session = Depends(get_db)):
    order = db.query(OrderTable).filter(OrderTable.user_id == user_id).first()
    
    if order:
        order.quantity += 1
        db.commit()
        db.refresh(order)
        return {"order_id": order.order_id}

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
        return {"order_id": new_order.order_id}

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