"""Dataset scale definitions and deterministic generation settings."""

from dataclasses import dataclass
from enum import StrEnum


class DatasetScale(StrEnum):
    DEMO = "demo"
    PORTFOLIO = "portfolio"
    STRESS = "stress"


@dataclass(frozen=True)
class DatasetConfig:
    scale: DatasetScale
    stores: int
    warehouses: int
    employees: int
    categories: int
    brands: int
    products: int
    suppliers: int
    customers: int
    reference_date: str = "2026-01-01"


CONFIGURATIONS = {
    DatasetScale.DEMO: DatasetConfig(DatasetScale.DEMO, 8, 4, 40, 10, 20, 150, 30, 2_000),
    DatasetScale.PORTFOLIO: DatasetConfig(
        DatasetScale.PORTFOLIO, 20, 6, 120, 12, 40, 500, 60, 10_000
    ),
    DatasetScale.STRESS: DatasetConfig(DatasetScale.STRESS, 35, 10, 250, 15, 70, 1_000, 120, 50_000),
}


def get_dataset_config(scale: DatasetScale | str) -> DatasetConfig:
    """Return the immutable configuration for a named scale."""
    return CONFIGURATIONS[DatasetScale(scale)]
