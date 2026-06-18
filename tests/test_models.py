from src.models import User, Role


def test_user_model_fields():
    user = User(full_name="Test", email="test@example.com", password_hash="hash", role=Role.customer)
    assert user.email == "test@example.com"
    assert user.role == Role.customer
