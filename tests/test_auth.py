from src.auth import hash_password, verify_password


def test_password_hash_and_verify():
    password_hash = hash_password("Password123!")
    assert verify_password("Password123!", password_hash)
    assert not verify_password("wrong", password_hash)
