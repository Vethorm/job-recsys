# jobmatch_scraper/items.py
import scrapy


class JobItem(scrapy.Item):
    url = scrapy.Field()
    title = scrapy.Field()
    company = scrapy.Field()
    location = scrapy.Field()
    description = scrapy.Field()
    department = scrapy.Field()
    requirements = scrapy.Field()
    benefits = scrapy.Field()

    raw_html = scrapy.Field()

    source_url = scrapy.Field()
