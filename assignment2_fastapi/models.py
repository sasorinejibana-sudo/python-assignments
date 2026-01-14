from sqlalchemy import Column, Integer, String, Numeric, Index
from db import Base

class Product(Base):
    __tablename__ = "Products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(String(1200), nullable=True)
    price = Column(Numeric(18, 2), nullable=False)

# Enforce unique product name
Index("IX_Products_Name_Unique", Product.name, unique=True)
