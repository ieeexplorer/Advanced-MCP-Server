from functools import wraps
from loguru import logger


def performance_middleware(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        logger.debug(f"Running {func.__name__}")
        return await func(*args, **kwargs)

    return wrapper


def error_handler_middleware(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception:
            logger.exception("Unhandled error in middleware")
            raise

    return wrapper


def auth_middleware(required_role: str = "user"):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)

        return wrapper

    return decorator
