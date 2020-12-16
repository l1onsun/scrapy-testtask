# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from dataclasses import dataclass, field
import time
from typing import Any


@dataclass
class Price:
    current: float
    original: float
    sale_tag: str


@dataclass
class Stock:
    in_stock: bool
    count: int


@dataclass
class Assets:
    main_image: str
    set_images: list[str]
    view360: list[str]
    video: list[str]


@dataclass
class Product:
    RPC: str
    url: str
    title: str
    marketing_tags: list[str]
    brand: str
    section: list[str]
    price_data: Price
    stock: Stock
    assets: Assets
    metadata: dict[str, str]
    variants: int
    timestamp: float = field(default_factory=time.time)
