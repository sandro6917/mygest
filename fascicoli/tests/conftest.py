import pytest
from django.contrib.auth import get_user_model

from core.models import UserRole

User = get_user_model()


@pytest.fixture
def user(db):
    u = User.objects.create_user(
        username="testuser_fascicoli",
        email="testfascicoli@example.com",
        password="testpass123",
    )
    u.profile.role = UserRole.ADMIN
    u.profile.save()
    return u
