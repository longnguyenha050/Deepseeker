from typing import Annotated, List, Optional
from datetime import datetime
from enum import Enum

# Import ConfigDict và to_camel để xử lý mapping tự động
from pydantic import Field, BaseModel, EmailStr, ConfigDict
from pydantic.alias_generators import to_camel

from beanie import Document, Link, Indexed, PydanticObjectId
from pymongo import IndexModel, ASCENDING, DESCENDING

# ================= CONFIGURATION =================

# Tạo một class cấu hình chung để tái sử dụng
class BaseConfig:
    """
    Cấu hình này giúp Pydantic tự động map:
    - Code Python: snake_case (created_at)
    - MongoDB: camelCase (createdAt)
    """
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True  # Cho phép dùng tên snake_case khi khởi tạo object
    )

# ================= ENUMS =================
# (Giữ nguyên phần Enum của bạn)

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

# Kế thừa BaseConfig để ImageInfo cũng map public_id -> publicId
class ImageInfo(BaseModel, BaseConfig):
    url: Optional[str] = None
    public_id: Optional[str] = None

# ================= MODELS =================

# Tạo class cha cho Document để không phải viết lại config nhiều lần
class BaseDocument(Document, BaseConfig):
    # Các field chung cho mọi document
    id: Optional[PydanticObjectId] = Field(None, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        # Nếu muốn Beanie tự động bỏ qua field null khi save để tiết kiệm dung lượng
        keep_nulls = False

class User(BaseDocument):
    username: str = Field(lowercase=True, strip_whitespace=True)
    hashed_password: str = ""
    email: Annotated[str, Indexed(unique=True)]
    display_name: str = ""
    role: UserRole = UserRole.CUSTOMER
    avatar: Optional[ImageInfo] = None
    status: UserStatus = UserStatus.ACTIVE
    bio: Optional[str] = Field(None, max_length=500)
    phone: str = ""
    auth_type: AuthType = AuthType.LOCAL
    reset_password_token: Optional[str] = None
    reset_password_expires: Optional[datetime] = None
    # created_at, updated_at đã có trong BaseDocument

    class Settings:
        name = "users"

class Session(BaseDocument):
    user_id: Annotated[Link[User], Indexed()]
    refresh_token: Annotated[str, Indexed(unique=True)]
    expires_at: datetime

    class Settings:
        name = "sessions"
        indexes = [
            # LƯU Ý: Trong IndexModel phải dùng tên field camelCase (tên trong DB)
            IndexModel([("expiresAt", ASCENDING)], expireAfterSeconds=0)
        ]

class Address(BaseDocument):
    is_default: bool
    street: str
    ward: str
    district: str
    city: str
    country: str
    user_id: Link[User]

    class Settings:
        name = "addresses"

class Category(BaseDocument):
    name: str = Field(strip_whitespace=True)
    slug: Annotated[str, Indexed(unique=True)]
    parent_id: Optional[Link["Category"]] = None

    class Settings:
        name = "categories"

class Product(BaseDocument):
    code: Annotated[str, Indexed(unique=True)]
    title: str = Field(strip_whitespace=True)
    slug: Annotated[str, Indexed(unique=True)]
    description: str = ""
    tag: List[str] = []
    category_id: Link[Category]
    avatar: ImageInfo

    class Settings:
        name = "products"

class ProductVariantImage(BaseDocument):
    color: str
    product_id: Link[Product]
    avatar: Optional[ImageInfo] = None

    class Settings:
        name = "product_variant_images"

class ProductVariant(BaseDocument):
    sku: Optional[str] = None
    price: float = Field(default=0.0, ge=0)
    stock: int = Field(default=0, ge=0)
    color: str 
    size: str 
    product_id: Link[Product]
    product_variant_image_id: Optional[Link[ProductVariantImage]] = None

    class Settings:
        name = "product_variants"
        indexes = [
            IndexModel(
                [("sku", ASCENDING)],
                unique=True,
                sparse=True
            ),
            # Field name trong index phải là camelCase: productId, productVariantImageId...
            IndexModel(
                [("color", ASCENDING), ("size", ASCENDING), ("productId", ASCENDING)],
                unique=True,
                partialFilterExpression={"sku": {"$exists": True}}
            )
        ]

class Promotion(BaseDocument):
    code: Annotated[str, Indexed(unique=True)]
    description: str = ""
    discount_type: DiscountType
    discount_amount: float
    stock: int
    min_order_amount: float
    active: PromotionStatus
    expired_at: datetime
    started_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "promotions"

class Order(BaseDocument):
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

    class Settings:
        name = "orders"
        indexes = [
            # userId, promotionId (camelCase)
            IndexModel(
                [("userId", ASCENDING), ("promotionId", ASCENDING)],
                unique=True,
                partialFilterExpression={
                    "promotionId": {"$gt": None},
                    "status": {"$in": ["pending", "paid", "processing", "shipped", "delivered"]}
                }
            )
        ]

class OrderItem(BaseDocument):
    order_id: Link[Order] 
    variant_id: Link[ProductVariant]
    quantity: int = Field(gt=0)
    price: float

    class Settings:
        name = "order_items"
        indexes = [
            # orderId, variantId (camelCase)
            IndexModel([("orderId", ASCENDING), ("variantId", ASCENDING)], unique=True)
        ]

class Review(BaseDocument):
    user_id: Link[User]
    product_id: Link[Product]
    order_item_id: Annotated[Link[OrderItem], Indexed(unique=True)]
    rating: int = Field(ge=1, le=5)
    content: str = ""
    color: Optional[str] = None
    size: Optional[str] = None
    likes: int = 0
    status: ReviewStatus = ReviewStatus.PENDING

    class Settings:
        name = "reviews"
        indexes = [
            # productId, createdAt (camelCase)
            IndexModel([("productId", ASCENDING), ("createdAt", DESCENDING)])
        ]

class CartItem(BaseDocument):
    variant_id: Link[ProductVariant]
    quantity: int = Field(gt=0)
    user_id: Link[User]

    class Settings:
        name = "cart_items"
        indexes = [
            # userId, variantId (camelCase)
            IndexModel([("userId", ASCENDING), ("variantId", ASCENDING)], unique=True)
        ]

class Favourite(BaseDocument):
    product_id: Link[Product]
    user_id: Link[User]

    class Settings:
        name = "favourites"
        indexes = [
             # userId, productId (camelCase)
            IndexModel([("userId", ASCENDING), ("productId", ASCENDING)], unique=True)
        ]

class Post(BaseDocument):
    title: str = Field(strip_whitespace=True)
    slug: Annotated[str, Indexed(unique=True)]
    content: str
    author: str = Field(strip_whitespace=True)
    category: PostCategory = PostCategory.PHOI_DO
    status: PostStatus = PostStatus.ACTIVE
    thumbnail: ImageInfo

    class Settings:
        name = "posts"

class Contact(BaseDocument):
    first_name: str = Field(strip_whitespace=True)
    last_name: str = Field(strip_whitespace=True)
    phone: str = Field(strip_whitespace=True)
    email: EmailStr
    message: str
    admin_note: str = ""

    class Settings:
        name = "contacts"
        indexes = [
            # createdAt (camelCase)
            IndexModel([("email", ASCENDING), ("createdAt", DESCENDING)])
        ]