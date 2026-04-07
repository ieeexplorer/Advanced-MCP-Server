from decimal import Decimal, InvalidOperation
import math


async def add_with_precision(a: float, b: float) -> float:
    try:
        return float(Decimal(str(a)) + Decimal(str(b)))
    except InvalidOperation:
        return float(a + b)


async def evaluate_expression(expression: str) -> float:
    allowed_names = {
        "sqrt": math.sqrt,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "log": math.log,
        "log10": math.log10,
        "pi": math.pi,
        "e": math.e,
        "abs": abs,
        "pow": pow,
        "round": round,
    }
    expression = expression.replace("^", "**")
    return float(eval(expression, {"__builtins__": None}, allowed_names))
