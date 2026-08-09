"""Dataset scale definitions and deterministic generation settings."""

from dataclasses import dataclass
from datetime import date
from enum import StrEnum

from scripts.dataset.master_data import BRAND_NAMES, CATEGORIES, LOCATIONS


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
    dataset_start_date: date = date(2024, 1, 1)
    dataset_end_date: date = date(2026, 7, 31)


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


def validate_config_capacity(config: DatasetConfig) -> None:
    """Ensure a scale can be created from the available static vocabularies."""
    if config.categories > len(CATEGORIES):
        raise ValueError(f"Scale {config.scale} requires more categories than are available.")
    if config.brands > len(BRAND_NAMES):
        raise ValueError(f"Scale {config.scale} requires more brands than are available.")
    if (config.stores > 0 or config.warehouses > 0) and not LOCATIONS:
        raise ValueError("Stores and warehouses require at least one location.")


def validate_all_configurations() -> None:
    """Preflight every profile without generating any rows."""
    for config in CONFIGURATIONS.values():
        validate_config_capacity(config)
