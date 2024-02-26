import json
import csv
import scrapy
from urllib.parse import urljoin

class AmazonscraperSpider(scrapy.Spider):
    name = "amazonscraper"
    scraped_count = 0
    keyword = None
    file_format = None
    file_extension = ""
    scraped_data = []

    def start_requests(self):
        if not self.keyword:
            self.keyword = input("Enter the name of product you want to scrape: ")
            self.num_products = int(input("Enter the number of products to scrape: "))
        self.file_format = input("File format (json/csv): ")
        if self.file_format == "json":
            self.file_extension = "json"
        elif self.file_format == "csv":
            self.file_extension = "csv"
        else:
            raise ValueError("Invalid file format. Please choose 'json' or 'csv'.")

        amazon_search_url = f'https://www.amazon.com/s?k={self.keyword}'
        print(f"Scraping {amazon_search_url}")
        yield scrapy.Request(url=amazon_search_url, callback=self.discover_product_urls)

    def discover_product_urls(self, response):
        search_products = response.css("div.s-result-item[data-component-type=s-search-result]")
        for product in search_products:
            relative_url = product.css("h2>a::attr(href)").get()
            product_url = urljoin('https://www.amazon.com/', relative_url)
            print(f"Product URL: {product_url[:50]} ...")
            yield scrapy.Request(url=product_url, callback=self.parse_product_data)

        next_page_url = response.css('a.s-pagination-item.s-pagination-next.s-pagination-button.s-pagination-separator ::attr(href)').get()
        if next_page_url and self.scraped_count < self.num_products:
            next_page_url = urljoin('https://www.amazon.com/', next_page_url)
            print(f"Next page URL: {next_page_url}")
            yield scrapy.Request(url=next_page_url, callback=self.discover_product_urls)

    def parse_product_data(self, response):
        image_url = response.css('#imgTagWrapperId img ::attr(src)').get()
        if not image_url:
            image_url = "N/A"
        name = response.css("#productTitle::text").get()
        if name:
            name = name.strip()
        else:
            name = "N/A"

        price = response.css('.a-price .a-offscreen ::text').get("")
        
        if not price:
            price = "N/A"

        stars = response.css("i[data-hook=average-star-rating] ::text").get()  
        if not stars:
            stars = "N/A"

        rating_count = response.css("#acrCustomerReviewText ::text").get()
        if not rating_count:
            rating_count = "N/A" 

        sale = response.css('#social-proofing-faceout-title-tk_bought span ::text').get()
        if sale:
            sale = sale.strip()

        else:
            sale = "N/A"
        item = {
            "name": name,
            "price": price,
            "stars": stars,
            "rating_count": rating_count,
            "image_url": image_url,
            "sale": sale,
        }
        self.scraped_data.append(item)
        self.scraped_count += 1
        print(f"Scraped {self.scraped_count} products")

        self.write_data_to_file()  

        if self.scraped_count >= self.num_products:
            raise scrapy.exceptions.CloseSpider(reason='Scraping completed')  

    def write_data_to_file(self):
        if self.file_extension == "json":
            with open('scraped_data.json', 'w') as outfile:
                json.dump(self.scraped_data, outfile, indent=4)
        elif self.file_extension == "csv":
            keys = self.scraped_data[0].keys() if self.scraped_data else []
            with open('scraped_data.csv', 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=keys)
                writer.writeheader()
                writer.writerows(self.scraped_data)

    def closed(self, reason):
        print(f"Total number of products scraped: {len(self.scraped_data)}")
