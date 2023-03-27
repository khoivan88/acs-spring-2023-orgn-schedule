import pandas as pd
from pathlib import Path, PurePath

from scrapy.crawler import CrawlerProcess
from acs_spring2023_scrape_orgn import ACSSpring2023Orgn

CURRENT_FILEPATH = Path(__file__).resolve().parent
DATA_FOLDER = CURRENT_FILEPATH.parent / 'src' / '_data'
SCRAPY_LOG_FILE = CURRENT_FILEPATH / 'scrapy-for-summary.log'
SUMMARY_FILE = CURRENT_FILEPATH / 'sessions_grouped_by_datetime.csv'

DATA_FOLDER.mkdir(exist_ok=True)
THIS_SPIDER_RESULT_FILE = DATA_FOLDER / 'acs_spring2023_orgn_for_summary.json'


def scrape():
    settings = {
        'USER_AGENT': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.96 Safari/537.36',
        # 'HTTPCACHE_ENABLED': True,
        # 'DEFAULT_REQUEST_HEADERS': {
        #   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        #   'Accept-Language': 'en'
        # },
        # 'CSV_EXPORT_FILE': THIS_SPIDER_RESULT_FILE,
        # 'ITEM_PIPELINES': {
            # '__main__.RemoveIgnoredKeywordsPipeline': 100,
            # },
        # 'FEEDS': {'data.json': {'format': 'json'}},
        'FEEDS': {
            THIS_SPIDER_RESULT_FILE.relative_to(CURRENT_FILEPATH.parent): {    # fix for running on Windows
            # THIS_SPIDER_RESULT_FILE.as_uri(): {
                'format': 'json',
                'encoding': 'utf8',
                'indent': 2,
                # 'fields': FIELDS_TO_EXPORT,
                'fields': None,
                'overwrite': True,
                'store_empty': False,
                'item_export_kwargs': {
                    'export_empty_fields': True,
                },
            },
        },
        'LOG_LEVEL': 'INFO',
        'LOG_FILE': SCRAPY_LOG_FILE.relative_to(CURRENT_FILEPATH.parent),
        'LOG_FILE_APPEND': False,    # overwrite existing log file instead of appending
        # 'ROBOTSTXT_OBEY': False,
    }
    process = CrawlerProcess(settings=settings)
    process.crawl(ACSSpring2023Orgn)
    process.start()


def main():
    # Scrape:
    scrape()

    # Process scrape file
    df = pd.read_json(THIS_SPIDER_RESULT_FILE)
    # breakpoint()
    grouped_df = df.groupby(['starting_date', 'am_or_pm'], sort=True, group_keys=True)['starting_date', 'am_or_pm', 'title', 'location', 'session_type', 'time_location'].apply(lambda x: x)
    grouped_df.to_csv(SUMMARY_FILE, index=False)


if __name__ == '__main__':
    main()