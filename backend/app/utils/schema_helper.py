from typing import Type
from beanie import Document

def get_model_schema(model_class: Type[Document]) -> str:
    """
    Chuyển đổi Beanie Model thành chuỗi mô tả schema đơn giản
    để tiết kiệm token cho LLM.
    """
    schema_desc = f"Collection: {model_class.get_collection_name()}\nFields:\n"
    
    # Lấy thông tin fields từ Pydantic model
    for name, field in model_class.model_fields.items():
        # Lấy tên field (ưu tiên alias nếu có vì DB lưu alias camelCase)
        field_name = field.alias if field.alias else name
        field_type = str(field.annotation).replace("typing.", "").replace("<class '", "").replace("'>", "")
        
        # Mô tả thêm nếu cần (ví dụ enum values)
        schema_desc += f"- {field_name} ({field_type})\n"
        
    return schema_desc

# Hàm tổng hợp toàn bộ Schema
def get_all_schemas():
    from app.models.models import User, Order, Product
    # Import hết các model cần query
    
    models = [User, Order, Product]
    full_context = ""
    for model in models:
        full_context += get_model_schema(model) + "\n"
    return full_context