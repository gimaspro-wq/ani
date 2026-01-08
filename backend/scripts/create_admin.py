"""Script to create the first admin user."""
import asyncio
import os
import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.db.models import AdminUser
from app.services.admin import hash_password
from app.core.config import settings


async def create_first_admin():
    """Create the first admin user from environment variables."""
    # Get admin credentials from environment
    admin_email = os.getenv("ADMIN_EMAIL")
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_password = os.getenv("ADMIN_PASSWORD")
    
    if not admin_email or not admin_password:
        print("Error: ADMIN_EMAIL and ADMIN_PASSWORD environment variables must be set")
        print("Example:")
        print("  export ADMIN_EMAIL=admin@example.com")
        print("  export ADMIN_USERNAME=admin")
        print("  export ADMIN_PASSWORD=securepassword123")
        sys.exit(1)
    
    # Create async engine and session
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        # Check if admin user already exists
        from sqlalchemy import select
        result = await session.execute(
            select(AdminUser).filter(AdminUser.email == admin_email)
        )
        existing_admin = result.scalar_one_or_none()
        
        if existing_admin:
            print(f"Admin user with email {admin_email} already exists")
            return
        
        # Create admin user
        admin = AdminUser(
            email=admin_email,
            username=admin_username,
            hashed_password=hash_password(admin_password),
            is_active=True
        )
        
        session.add(admin)
        await session.commit()
        
        print(f"✓ Admin user created successfully!")
        print(f"  Email: {admin_email}")
        print(f"  Username: {admin_username}")
        print(f"\nYou can now login to the admin panel with these credentials.")
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(create_first_admin())
