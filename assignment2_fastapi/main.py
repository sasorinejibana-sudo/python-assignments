from fastapi import FastAPI, Depends, HTTPException, status, Header, Response
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Any, List, Union

from db import Base, engine, get_db
from models import Product
from schemas import LoginRequest, LoginResponse, ProductCreate, ProductOut
from auth import authenticate, create_token, require_auth_header

app = FastAPI(title="ProductService (FastAPI)")

# Create tables on startup (simple for assignment)
Base.metadata.create_all(bind=engine)


@app.post("/api/auth/login", response_model=LoginResponse)
def login(req: LoginRequest):
    user = authenticate(req.username, req.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")

    token, expires = create_token(user["username"], user["role"])
    return {
        "token": token,
        "expiresAt": expires,
        "username": user["username"],
        "role": user["role"]
    }


# ----------- Products -----------

@app.get("/api/products")
def get_products(
    db: Session = Depends(get_db),
    authorization: str | None = Header(default=None)
):
    # Anonymous users: error with relevant status code/message
    user = require_auth_header(authorization)

    # Only Admin or PrivilegedUser
    if user["role"] not in ("Admin", "PrivilegedUser"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    products = db.query(Product).order_by(Product.id).all()

    if len(products) == 0:
        return {"message": "aye, there are no products here"}

    return [ProductOut.model_validate(p).model_dump() for p in products]


@app.get("/api/products/{product_id}")
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    authorization: str | None = Header(default=None)
):
    # Anonymous users: error with relevant status code/message
    user = require_auth_header(authorization)

    if user["role"] not in ("Admin", "PrivilegedUser"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="aye, there is no such product here!")

    return ProductOut.model_validate(product).model_dump()


@app.post("/api/products")
def add_product(
    req: ProductCreate,
    db: Session = Depends(get_db),
    authorization: str | None = Header(default=None)
):
    # Special rule: Anonymous calling AddProduct -> no message body at all
    if not authorization or not authorization.startswith("Bearer "):
        return Response(status_code=status.HTTP_401_UNAUTHORIZED)

    user = require_auth_header(authorization)

    # Non-admins: access denied with status code + message
    if user["role"] != "Admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    p = Product(name=req.name.strip(), description=req.description, price=req.price)
    db.add(p)

    try:
        db.commit()
        db.refresh(p)
    except IntegrityError:
        db.rollback()
        # Unique name rule
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Product name must be unique")

    return {
        "message": "product added successfully",
        "product": ProductOut.model_validate(p).model_dump()
    }
