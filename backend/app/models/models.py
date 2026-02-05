from typing import Annotated, List, Optional
from datetime import datetime
from enum import Enum
from beanie import Document, Link, Indexed
from pydantic import Field, BaseModel, EmailStr
from pymongo import IndexModel, ASCENDING, DESCENDING

# ================= ENUMS =================

class UserRole(str, Enum):
    CUSTOMER = "customer"
    ADMIN = "admin"

class UserStatus(str, Enum):
    ACTIVE = "active"
    BLOCKED = "blocked"

class AuthType(str, Enum):
    LOCAL = "local"
    GOOGLE = "google"

class DiscountType(str, Enum):
    PERCENTAGE = "percentage"
    FIXED = "fixed"

class PromotionStatus(str, Enum):
    UPCOMING = "upcoming"
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"

class OrderStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class PaymentMethod(str, Enum):
    COD = "COD"
    BANKING = "Banking"

class ReviewStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    HIDDEN = "hidden"

class PostCategory(str, Enum):
    PHOI_DO = "Phối đồ"
    XU_HUONG = "Xu hướng"
    REVIEW = "Review"

class PostStatus(str, Enum):
    ACTIVE = "active"
    HIDDEN = "hidden"

# ================= SHARED SCHEMAS =================

class ImageInfo(BaseModel):
    url: Optional[str] = None
    public_id: Optional[str] = None

# ================= MODELS =================

class User(Document):
    username: str = Field(lowercase=True, strip_whitespace=True)
    hashed_password: str = ""
    email: Annotated[EmailStr, Indexed(unique=True)]
    display_name: str = ""
    role: UserRole = UserRole.CUSTOMER
    avatar: Optional[ImageInfo] = None
    status: UserStatus = UserStatus.ACTIVE
    bio: Optional[str] = Field(None, max_length=500)
    phone: str = ""
    auth_type: AuthType = AuthType.LOCAL
    reset_password_token: Optional[str] = None
    reset_password_expires: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "users"

class Session(Document):
    user_id: Annotated[Link[User], Indexed()]
    refresh_token: Annotated[str, Indexed(unique=True)]
    expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "sessions"
        indexes = [
            IndexModel([("expires_at", ASCENDING)], expireAfterSeconds=0)
        ]

class Address(Document):
    is_default: bool
    street: str
    ward: str
    district: str
    city: str
    country: str
    user_id: Link[User]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "addresses"

class Category(Document):
    name: str = Field(strip_whitespace=True)
    slug: Annotated[str, Indexed(unique=True)]
    parent_id: Optional[Link["Category"]] = None

    class Settings:
        name = "categories"

class Product(Document):
    code: Annotated[str, Indexed(unique=True)]
    title: str = Field(strip_whitespace=True)
    slug: Annotated[str, Indexed(unique=True)]
    description: str = ""
    tag: List[str] = []
    category_id: Link[Category]
    avatar: ImageInfo
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "products"

class ProductVariantImage(Document):
    color: str
    product_id: Link[Product]
    avatar: Optional[ImageInfo] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "product_variant_images"

class ProductVariant(Document):
    sku: Optional[str] = None
    price: float = Field(default=0.0, ge=0)
    stock: int = Field(default=0, ge=0)
    # FIX: Bỏ unique=True ở color/size lẻ, chỉ dùng compound index bên dưới
    color: str 
    size: str 
    product_id: Link[Product]
    product_variant_image_id: Optional[Link[ProductVariantImage]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "product_variants"
        indexes = [
            IndexModel(
                [("sku", ASCENDING)],
                unique=True,
                sparse=True
            ),
            IndexModel(
                [("color", ASCENDING), ("size", ASCENDING), ("product_id", ASCENDING)],
                unique=True,
                partialFilterExpression={"sku": {"$ne": None}}
            )
        ]

class Promotion(Document):
    code: Annotated[str, Indexed(unique=True)]
    description: str = ""
    discount_type: DiscountType
    discount_amount: float
    stock: int
    min_order_amount: float
    active: PromotionStatus
    expired_at: datetime
    started_at: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "promotions"

class Order(Document):
    order_number: Annotated[str, Indexed(unique=True)]
    status: OrderStatus = OrderStatus.PENDING
    shipping_fee: float = 30.0
    total: float
    name: str
    phone: str
    address: str
    note: Optional[str] = None
    paid_at: Optional[datetime] = None
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    promotion_id: Optional[Link[Promotion]] = None
    user_id: Link[User]
    payment_method: PaymentMethod = PaymentMethod.COD
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "orders"
        indexes = [
            IndexModel(
                [("user_id", ASCENDING), ("promotion_id", ASCENDING)],
                unique=True,
                partialFilterExpression={
                    "promotion_id": {"$exists": True},
                    "status": {"$in": ["pending", "paid", "processing", "shipped", "delivered"]}
                }
            )
        ]

class OrderItem(Document):
    order_id: Link[Order] 
    variant_id: Link[ProductVariant]
    quantity: int = Field(gt=0)
    price: float
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "order_items"
        indexes = [
            # Unique kết hợp: Trong 1 order, mỗi variant chỉ xuất hiện 1 dòng
            IndexModel([("order_id", ASCENDING), ("variant_id", ASCENDING)], unique=True)
        ]

class Review(Document):
    user_id: Link[User]
    product_id: Link[Product]
    order_item_id: Annotated[Link[OrderItem], Indexed(unique=True)]
    rating: int = Field(ge=1, le=5)
    content: str = ""
    color: Optional[str] = None
    size: Optional[str] = None
    likes: int = 0
    status: ReviewStatus = ReviewStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "reviews"
        indexes = [
            IndexModel([("product_id", ASCENDING), ("created_at", DESCENDING)])
        ]

class CartItem(Document):
    variant_id: Link[ProductVariant]
    quantity: int = Field(gt=0)
    user_id: Link[User]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "cart_items"
        indexes = [
            IndexModel([("user_id", ASCENDING), ("variant_id", ASCENDING)], unique=True)
        ]

class Favourite(Document):
    product_id: Link[Product]
    user_id: Link[User]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "favourites"
        indexes = [
            IndexModel([("user_id", ASCENDING), ("product_id", ASCENDING)], unique=True)
        ]

class Post(Document):
    title: str = Field(strip_whitespace=True)
    slug: Annotated[str, Indexed(unique=True)]
    content: str
    author: str = Field(strip_whitespace=True)
    category: PostCategory = PostCategory.PHOI_DO
    status: PostStatus = PostStatus.ACTIVE
    thumbnail: ImageInfo
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "posts"

class Contact(Document):
    first_name: str = Field(strip_whitespace=True)
    last_name: str = Field(strip_whitespace=True)
    phone: str = Field(strip_whitespace=True)
    email: EmailStr
    message: str
    admin_note: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "contacts"
        indexes = [
            IndexModel([("email", ASCENDING), ("created_at", DESCENDING)])
        ]