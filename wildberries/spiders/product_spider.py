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


class QuotesSpider(scrapy.Spider):
    name = "products"

    def start_requests(self):
        yield scrapy.Request(url='https://www.wildberries.ru/catalog/obuv/zhenskaya/sabo-i-myuli/myuli',
                             callback=self.parse, headers=headers, cookies=cookies)

    def parse_product_card(self, response: scrapy.http.Response, **kwargs):
        url = response.request.url
        article = url_to_article(url)

        # title
        brand_and_name = response.css("div.brand-and-name.j-product-title")
        brand = brand_and_name.css("span.brand::text").get()
        name = brand_and_name.css("span.name::text").get()
        colors = response.css("div.color.j-color-name-container").css("span.color::text").get()
        title = f"{brand} / {name}, {colors}" if colors else f"{brand} / {name}"

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
        # yield {
        #     "timestamp": location,  # time.time(),  # Текущее время в формате timestamp
        #     "RPC": article,  # {str} Уникальный код товара
        #     "url": response.request.url,  # {str} Ссылка на страницу товара
        #     "title": f"{brand} / {name}, {colors}",
        #     # {str} Заголовок/название товара (если в карточке     товара указан цвет или объем, необходимо добавить их в title     в формате: "{название}, {цвет}")
        #     "marketing_tags": advantages,
        #     # {list of str} Список тэгов, например:     ['Популярный', 'Акция', 'Подарок'], если тэг представлен в     виде изображения собирать его не нужно
        #     "brand": brand,  # {str} Брэнд товара
        #     "section": response.meta["section"],
        #     # {list of str} Иерархия разделов, например:     ['Игрушки', 'Развивающие и интерактивные игрушки',     'Интерактивные игрушки']
        #
        #     "price_data": {
        #         "current": 0.,  # {float} Цена со скидкой, если     скидки нет то = original
        #         "original": 0.,  # {float} Оригинальная цена
        #         "sale_tag": ""
        #         # {str} Если есть скидка на товар то     необходимо вычислить процент скидки и записать формате:     "Скидка {}%"
        #     },
        #     "stock": {
        #         "in_stock": True,  # {bool} Должно отражать наличие     товара в магазине
        #         "count": 0
        #         # {int} Если есть возможность получить     информацию о количестве оставшегося товара в наличии, иначе 0
        #     },
        #     "assets": {
        #         "main_image": "",  # {str} Ссылка на основное     изображение товара
        #         "set_images": [],  # {list of str} Список больших     изображений товара
        #         "view360": [],  # {list of str}
        #         "video": []  # {list of str}
        #     },
        #     "metadata": {
        #         "__description": "",  # {str} Описание товар
        #         # Ниже добавить все характеристики которые могут быть     на странице тоавара, такие как Артикул, Код товара, Цвет,     Объем, Страна производитель и т.д.
        #         # "АРТИКУЛ": "A88834",
        #         # "СТРАНА ПРОИЗВОДИТЕЛЬ": "Китай"
        #     },
        #     "variants": 1,
        #     # {int} Кол-во вариантов у товара в карточке (За     вариант считать только цвет или объем/масса. Размер у одежды     или обуви варинтами не считаются)
        # }

    def parse(self, response: scrapy.http.Response, **kwargs):
        section: list = response.css("ul.bread-crumbs").css("span::text").getall()
        logger.debug("SECTIONS: " + str(section))
        for i, product in enumerate(response.css('div.dtList.i-dtList.j-card-item')):
            product_ref = product.css("a.ref_goods_n_p.j-open-full-product-card::attr(href)").get()
            prod_card_url = response.urljoin(product_ref)
            yield scrapy.Request(url=prod_card_url, callback=self.parse_product_card, meta={'section': section},
                                 headers=headers, cookies=cookies)

        # next_page_ref = response.css("a.pagination-next::attr(href)").get()
        # if next_page_ref is not None:
        #     yield response.follow(next_page_ref)

        # next_page = response.css('li.next a::attr(href)').get()
        # if next_page is not None:
        #     next_page = response.urljoin(next_page)
        #     yield scrapy.Request(next_page, callback=self.parse)
