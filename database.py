from sqlalchemy import (
    create_engine, Column, Integer, BigInteger, String,
    Boolean, DateTime, Date, ForeignKey, Text, Float, UniqueConstraint
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
from utils.time_utils import get_now

Base = declarative_base()
engine = create_engine("sqlite:///foodsave.db", echo=False)

# ⚠️ ВАЖНО: сервисы возвращают ORM-объекты после s.expunge() (отсоединённые
# от сессии). Никогда не обращайся к *связям* (relationship, например
# pkg.restaurant, rest.packages) на таком объекте вне блока Session() -
# это упадёт с DetachedInstanceError. Обычные колонки (pkg.name, pkg.price)
# читать безопасно, они уже загружены. Если нужны связанные данные - делай
# отдельный явный запрос/JOIN внутри Session(), как везде в этом проекте.
Session = sessionmaker(bind=engine)

# ─────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"
    id          = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    language    = Column(String(5), default="ru")
    role        = Column(String(20), default="buyer")   # buyer | owner | admin
    created_at  = Column(DateTime, default=get_now)

class Restaurant(Base):
    __tablename__ = "restaurants"
    id            = Column(Integer, primary_key=True, autoincrement=True)
    name          = Column(String(120), nullable=False)
    address       = Column(String(255), nullable=False)
    district      = Column(String(80),  nullable=False)
    owner_id      = Column(BigInteger, nullable=True, index=True)
    claim_code    = Column(String(10), nullable=True, unique=True)
    photo_file_id = Column(String(255), nullable=True)
    latitude      = Column(Float, nullable=True)
    longitude     = Column(Float, nullable=True)
    active        = Column(Boolean, default=True)
    packages      = relationship("Package", back_populates="restaurant")
    is_closed = Column(Boolean, default=False)

class Package(Base):
    __tablename__ = "packages"
    id            = Column(Integer, primary_key=True, autoincrement=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=False, index=True)
    name          = Column(String(120), nullable=False)
    photo_file_id = Column(String(255), nullable=True)
    price         = Column(Integer, nullable=False)   # in sum
    quantity      = Column(Integer, nullable=False)
    pickup_from   = Column(String(10), nullable=False)  
    pickup_to     = Column(String(10), nullable=False) 
    available_date = Column(Date, nullable=True, index=True)
    active        = Column(Boolean, default=True)
    created_at    = Column(DateTime, default=get_now)
    restaurant    = relationship("Restaurant", back_populates="packages")
    orders        = relationship("Order", back_populates="package")

class Order(Base):
    __tablename__ = "orders"
    id             = Column(Integer, primary_key=True, autoincrement=True)
    code           = Column(String(20), unique=True, nullable=False)
    package_id     = Column(Integer, ForeignKey("packages.id"), nullable=False, index=True)
    user_id        = Column(BigInteger, nullable=False, index=True)   # telegram_id покупателя
    username       = Column(String(80), nullable=True)
    status         = Column(String(20), default="reserved", index=True) 
    price          = Column(Integer, nullable=True)
    commission     = Column(Integer, nullable=True)
    reserved_until = Column(DateTime, nullable=True)
    created_at     = Column(DateTime, default=get_now)
    completed_at   = Column(DateTime, nullable=True)
    package        = relationship("Package", back_populates="orders")
    reminder_sent = Column(Boolean, default=False)

# ─── Analytics log ────────────────────────────────────────────────────────────
class AnalyticsEvent(Base):
    __tablename__ = "analytics"
    id         = Column(Integer, primary_key=True, autoincrement=True)
    event      = Column(String(50), nullable=False)   
    user_id    = Column(BigInteger, nullable=True)
    district   = Column(String(80), nullable=True)
    created_at = Column(DateTime, default=get_now)
    
class SupportTicket(Base):
    __tablename__ = "support_tickets"
    id          = Column(Integer, primary_key=True, autoincrement=True)
    user_id     = Column(BigInteger, nullable=False, index=True)
    username    = Column(String(80), nullable=True)
    message     = Column(Text, nullable=False)
    status      = Column(String(20), default="open")  # open|answered
    admin_id    = Column(BigInteger, nullable=True)
    reply_text  = Column(Text, nullable=True)
    created_at  = Column(DateTime, default=get_now)
    replied_at  = Column(DateTime, nullable=True)

class Favorite(Base):
    __tablename__ ="Favorites"
    id            = Column(Integer, primary_key=True, autoincrement=True)
    user_id       = Column(BigInteger, nullable=False, index=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=False)
    created_at    = Column(DateTime, default=get_now)

    __table_args__ = (UniqueConstraint("user_id", "restaurant_id", name="uq_favorite_user_rest"),)
    
class Subscription(Base):
    __tablename__ = "subscriptions"
    id            = Column(Integer, primary_key=True, autoincrement=True)
    user_id       = Column(BigInteger, nullable=False, index=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=True)
    district      = Column(String(80), nullable=True)
    created_at    = Column(DateTime, default=get_now)
    
class Review(Base):
    __tablename__ = "reviews"
    id            = Column(Integer, primary_key=True, autoincrement=True)
    user_id       = Column(BigInteger, nullable=False)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=False)
    order_code    = Column(String(20), nullable=False)
    rating        = Column(Integer, nullable=False)
    created_at    = Column(DateTime, default=get_now)

class PackageTemplate(Base):
    __tablename__ = "package_templates"
    id            = Column(Integer, primary_key=True, autoincrement=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=False)
    name          = Column(String(120), nullable=False)
    photo_file_id = Column(String(255), nullable=True)
    price         = Column(Integer, nullable=False)
    pickup_from   = Column(String(10), nullable=False)
    pickup_to     = Column(String(10), nullable=False)
    created_at    = Column(DateTime, default=get_now)
def init_db():
    Base.metadata.create_all(engine)
