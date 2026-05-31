def test_sanity():
    """Sanity test to verify pytest is working."""
    assert True


def test_imports():
    """Test that basic imports work."""
    from fastapi import FastAPI
    from sqlmodel import SQLModel

    app = FastAPI()
    assert app is not None
    assert SQLModel is not None
