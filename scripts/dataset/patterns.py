"""Reusable non-temporal business profiles for master-data generation."""

SEGMENT_WEIGHTS = (70, 20, 7, 3)
EMPLOYEE_ROLES = (("Seller", 80), ("Senior Seller", 20))
REGIONAL_WEIGHTS = (50, 10, 10, 8, 7, 8, 7)
SUPPLIER_PROFILES = {
    "VALUE": (0.90, (8, 12)),
    "BALANCED": (1.00, (5, 8)),
    "FAST": (1.08, (2, 4)),
}


def weighted_role(random_source):
    """Choose an employee role from the configured weights."""
    roles, weights = zip(*EMPLOYEE_ROLES, strict=True)
    return random_source.choices(roles, weights=weights, k=1)[0]


def supplier_profile(supplier_id: int) -> str:
    """Assign a stable sourcing profile to each supplier identifier."""
    return ("VALUE", "BALANCED", "FAST")[(supplier_id - 1) % 3]
