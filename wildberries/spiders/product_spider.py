import scrapy
import wildberries.items as items
import logging
from wildberries.moscow_headers import headers, cookies
from typing import Optional

logger = logging.getLogger(__name__)


def url_to_article(url: str) -> str:
    splited = url.split('/')
    assert splited[3] == 'catalog'
    return splited[4]


def price_to_float(price_raw) -> Optional[float]:
    return float("".join(price_raw.split()[:-1]))


def common_request(url, callback, meta=None):
    scrapy.Request(url=url, callback=callback, headers=headers, cookies=cookies, meta=meta)


class QuotesSpider(scrapy.Spider):
    name = "products"

    def start_requests(self):
        yield common_request(url='https://www.wildberries.ru/catalog/obuv/zhenskaya/sabo-i-myuli/myuli',
                             callback=self.parse)

    def parse_product_card(self, response: scrapy.http.Response, **kwargs):
        url = response.request.url
        article = url_to_article(url)

        # title
        brand_and_name = response.css("div.brand-and-name.j-product-title")
        brand = brand_and_name.css("span.brand::text").get()
        name = brand_and_name.css("span.name::text").get()
        colors = response.css("div.color.j-color-name-container").css("span.color::text").get()
        if colors:
            title = f"{brand} / {name}, {colors}"
        else:
            title = f"{brand} / {name}"
            colors = ""

        # price
        current_price_raw: str = response.css("span.final-cost::text").get()
        original_price_raw: str = response.css("del.c-text-base::text").get()
        current_price = price_to_float(current_price_raw)
        if original_price_raw is not None:
            original_price = price_to_float(original_price_raw)
            ratio = current_price / original_price
            sale = 1 - ratio
            sale_tag = f"Скидка {int(100 * sale)}%"
        else:
            original_price = current_price
            sale_tag = ""
        price_data = items.Price(current=current_price, original=original_price, sale_tag=sale_tag)

        # build metadata
        metadata = {}

        card_add_info = response.css("div.card-add-info")
        description = card_add_info.css("span.j-composition.collapsable-content.j-toogle-height-instance::text").get()
        metadata["__description"] = description

        params = card_add_info.css("div.pp")
        for param in params:
            metadata[param.css("b::text").get()] = param.css("span::text").get()

        yield items.Product(
            RPC=article,
            url=url,
            title=title,
            marketing_tags=response.css("li.about-advantages-item::text").getall(),
            brand=brand,
            section=response.meta["section"],
            price_data=price_data,
            stock=items.Stock(
                in_stock=True,
                count=100500,
            ),
            assets=items.Assets(
                main_image="",
                set_images="",
                view360=None,
                video=None
            ),
            metadata=metadata,
            variants=len(colors.split())
        )

    def parse(self, response: scrapy.http.Response, **kwargs):
        section: list = response.css("ul.bread-crumbs").css("span::text").getall()
        logger.debug("SECTIONS: " + str(section))
        for i, product in enumerate(response.css('div.dtList.i-dtList.j-card-item')):
            product_ref = product.css("a.ref_goods_n_p.j-open-full-product-card::attr(href)").get()
            prod_card_url = response.urljoin(product_ref)
            yield common_request(url=prod_card_url, callback=self.parse_product_card, meta={'section': section})

        next_page_ref = response.css("a.pagination-next::attr(href)").get()
        if next_page_ref is not None:
            next_page_url = response.urljoin(next_page_ref)
            yield common_request(url=next_page_url, callback=self.parse_product_card, meta={'section': section})
