from passlib.context import CryptContext
import bcrypt

print(f"Bcrypt version: {bcrypt.__version__}")
try:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    pw = "testpassword123"
    print(f"Hashing: {pw}")
    hashed = pwd_context.hash(pw)
    print(f"Result: {hashed}")
except Exception as e:
    print(f"Error: {e}")
