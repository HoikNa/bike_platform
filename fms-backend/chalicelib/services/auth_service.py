from chalicelib.models.user import User, UserRole
from chalicelib.core.password import verify_password, get_password_hash
from chalicelib.core.jwt_helper import create_access_token
from chalicelib.core.exceptions import UnauthorizedException
from sqlmodel import Session, select
from datetime import timedelta

class AuthService:
    @staticmethod
    def seed_test_users(session: Session):
        admin = session.exec(select(User).where(User.email == "admin@fms.io")).first()
        if not admin:
            admin = User(
                email="admin@fms.io",
                hashed_password=get_password_hash("admin123"),
                full_name="System Admin",
                role=UserRole.ADMIN
            )
            session.add(admin)
            
        driver = session.exec(select(User).where(User.email == "driver@fms.io")).first()
        if not driver:
            driver = User(
                email="driver@fms.io",
                hashed_password=get_password_hash("driver123"),
                full_name="Test Driver",
                role=UserRole.DRIVER
            )
            session.add(driver)
            
        session.commit()

    @staticmethod
    def authenticate_user(session: Session, email: str, password: str):
        user = session.exec(select(User).where(User.email == email)).first()
        
        if not user or not verify_password(password, user.hashed_password):
            raise UnauthorizedException("Incorrect email or password")
        
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email, "role": user.role},
            expires_delta=timedelta(minutes=60*24)
        )
        
        return {
            "access_token": access_token,
            "user": {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role
            }
        }
