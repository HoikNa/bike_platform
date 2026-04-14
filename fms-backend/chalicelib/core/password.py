import hashlib

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return get_password_hash(plain_password) == hashed_password

def get_password_hash(password: str) -> str:
    # Use simple sha256 for prototype to avoid chalice local thread/fork issues with bcrypt C++ extensions
    return hashlib.sha256(password.encode("utf-8")).hexdigest()
