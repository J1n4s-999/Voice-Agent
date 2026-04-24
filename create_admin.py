from sqlalchemy import text

from app.db import get_db
from app.security import hash_password

db = next(get_db())

username = "admin"
password = "123456"
tenant_id = "default"

password_hash = hash_password(password)

db.execute(
    text("""
        INSERT INTO admin_users (id, tenant_id, username, password_hash)
        VALUES (:id, :tenant_id, :username, :password_hash)
    """),
    {
        "id": "admin-1",
        "tenant_id": tenant_id,
        "username": username,
        "password_hash": password_hash,
    },
)

db.commit()

print("Admin user created")