"""Reusable non-temporal business profiles for master-data generation."""

SEGMENT_WEIGHTS = (70, 20, 7, 3)
EMPLOYEE_ROLES = (("Seller", 75), ("Senior Seller", 18), ("Store Manager", 7))
SUPPLIER_PROFILES = ((0.92, 10), (1.00, 5), (1.06, 3))


def weighted_role(random_source):
    """Choose an employee role from the configured weights."""
    roles, weights = zip(*EMPLOYEE_ROLES, strict=True)
    return random_source.choices(roles, weights=weights, k=1)[0]
