import scrapy
import logging
import wildberries.items as item
from typing import Optional, Dict
import urllib.request
from http.client import HTTPResponse
import re

logger = logging.getLogger(__name__)


def url_to_article(url: str) -> str:
    splited = url.split('/')
    assert splited[3] == 'catalog'
    return splited[4]


def form_product(response: scrapy.http.Response) -> item.Product:
    url = response.request.url
    article = url_to_article(url)

    title, colors, brand = form_title_colors_brand(response)

    price = form_price(response)

    assets = form_assets(response)

    metadata = form_metadata(response)

    return item.Product(
        RPC=article,
        url=url,
        title=title,
        marketing_tags=response.css("li.about-advantages-item::text").getall(),
        brand=brand,
        section=response.meta["section"],
        price_data=price,
        stock=item.Stock(
            in_stock=True,
            count=100500,
        ),
        assets=assets,
        metadata=metadata,
        variants=len(colors.split())
    )


def form_title_colors_brand(response: scrapy.http.Response):
    brand_and_name = response.css("div.brand-and-name.j-product-title")
    brand = brand_and_name.css("span.brand::text").get()
    name = brand_and_name.css("span.name::text").get()
    colors = response.css("div.color.j-color-name-container").css("span.color::text").get()
    if colors:
        title = f"{brand} / {name}, {colors}"
    else:
        title = f"{brand} / {name}"
        colors = ""
    return title, colors, brand


def price_to_float(price_raw) -> Optional[float]:
    return float("".join(price_raw.split()[:-1]))


def form_price(response: scrapy.http.Response) -> item.Price:
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
    return item.Price(current=current_price, original=original_price, sale_tag=sale_tag)


def check_url(url):
    try:
        resp: HTTPResponse = urllib.request.urlopen(url)
        code = resp.getcode()
        if code < 400:
            return True
        else:
            return False
    except:
        return False


def view360(response: scrapy.http.Response):
    view_3d_base_raw = response.css("div.j-3d-container.three-d-container::attr(data-path)").get()
    view_3d_list = []
    if view_3d_base_raw:
        view_3d_base_url = re.match(r'^/*(.*)$', view_3d_base_raw).group(1)  # remove slashes from left

        i = 1
        while True:
            url = ''.join([view_3d_base_url, '/', str(i), '.jpg'])
            if check_url(url):
                view_3d_list.append(url)
            else:
                break
    return view_3d_list


def form_assets(response: scrapy.http.Response):
    # assets
    zoomed_image = response.css("img.MagicZoomFullSizeImage::attr(src)").get()
    images_set = response.css("a.j-carousel-image::attr(href)").getall()
    view_3d_base_raw = response.css("div.j-3d-container.three-d-container::attr(data-path)").get()
    view_3d_list = []

    if view_3d_base_raw:
        i = 1
        while True:
            url = ''.join(['http:', view_3d_base_raw, '/', str(i), '.jpg'])
            if check_url(url):
                view_3d_list.append(url)
            else:
                break
            i += 1

    return item.Assets(
        main_image=zoomed_image,
        set_images=images_set,
        view360=view_3d_list,
        video=[]
    )


def form_metadata(response: scrapy.http.Response) -> Dict[str, str]:
    metadata = {}

    card_add_info = response.css("div.card-add-info")
    description = card_add_info.css("span.j-composition::text").get()
    metadata["__description"] = description

    params = card_add_info.css("div.pp")
    for param in params:
        metadata[param.css("b::text").get()] = param.css("span::text").get()

    return metadata
