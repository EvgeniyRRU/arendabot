"""Root aiogram router for future bot features."""

from aiogram import Router


def create_router() -> Router:
    """Create the root feature router."""
    return Router(name="arendabot")
