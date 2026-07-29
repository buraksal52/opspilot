"""Deterministic, sequential identifier formatting for generated records."""


def customer_id(i: int) -> str:
    return f"CUST-{i:05d}"


def product_id(i: int) -> str:
    return f"PROD-{i:04d}"


def order_id(i: int) -> str:
    return f"ORD-{i:06d}"


def refund_id(i: int) -> str:
    return f"REF-{i:05d}"


def ticket_id(i: int) -> str:
    return f"TCK-{i:05d}"
