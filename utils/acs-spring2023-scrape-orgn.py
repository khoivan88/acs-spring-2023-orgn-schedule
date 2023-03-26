import re
from datetime import datetime
from pathlib import Path, PurePath
# from urllib.parse import urlparse, parse_qs, urlencode
from furl import furl

import scrapy

from scrapy.crawler import CrawlerProcess
# from scrapy.exceptions import DropItem
# from scrapy.exporters import CsvItemExporter

from items import SessionItem, PresentationItem

CURRENT_FILEPATH = Path(__file__).resolve().parent
DATA_FOLDER = CURRENT_FILEPATH.parent / 'src' / '_data'
DATA_FOLDER.mkdir(exist_ok=True)
THIS_SPIDER_RESULT_FILE = DATA_FOLDER / 'acs_spring2023_orgn.json'
# THIS_SPIDER_RESULT_FILE.touch()


def convert_date(date_str: str) -> str:
    date = datetime.strptime(date_str, '%Y-%m-%d')
    return date.strftime('%m-%d-%Y').replace('-', '%2F')


class ACSSpring2023Orgn(scrapy.Spider):
    dates = ['2023-03-25',
            #  '2023-03-21', '2023-03-22', '2023-03-23', '2023-03-24'
             ]
    dates = [convert_date(date) for date in dates]
    name = 'asc-spring2023-orgn'
    allowed_domains = ['acs.digitellinc.com']
    start_urls = [furl(f'https://acs.digitellinc.com/acs/live/29/page/940/1?eventSearchInput=&eventSearchDateTimeStart={date}+12%3A00+AM&eventSearchDateTimeEnd=&eventSearchTrack%5B%5D=171').url
                  for date in dates]
    base_url = 'https://acs.digitellinc.com/'
    # handle_httpstatus_list = [301, 302]

    def parse(self, response):
        # date = parse_qs(urlparse(response.url).query)['eventSearchDate'][0]
        # date += 'T00:00:00-0500'
        # breakpoint()
        track = '[ORGN] Division of Organic Chemistry'
        # Get all the sessions listing
        # sessions = response.css('.panel.panel-default.panel-session')
        # sessions = response.xpath('//div[@id="event-content"]/div/div[contains(@class, "panel") and contains(@class, "panel-default") and contains(@class, "panel-session")]')
        sessions = response.xpath('//div[contains(@class, "panel") and contains(@class, "panel-default") and contains(@class, "panel-session")]')

        for session in sessions:
            session_id = session.css('.panel-heading').xpath('@id').get()
            id_num = re.search(r'\D*(\d+)', session_id)
            zoom_link = f'https://acs.digitellinc.com/acs/events/{id_num[1]}/attend'
            info = session.css('.panel-heading .panel-title .session-panel-title')
            title = info.css('a::text').get().strip()
            datetime_info = ' '.join(info.css('.session-panel-heading')[0].css('::text').getall()).strip()
            datetime_info = re.sub(r'\s+', ' ', datetime_info)    # Remove extra spaces
            datetime_string, location = datetime_info.split('|')
            datetime_string = datetime_string.strip()
            location = location.strip()
            # breakpoint()
            # Get the date string and convert to yyyy-mm-ddThh:mm:ss-07:00
            date_string = re.search(r'.*(\b\w+\s+\d\d,\s+2023)', datetime_string)[1]
            start_time = re.search(r'(\d{2}:\d{2}\s*\w{2})', datetime_string)[1]
            date_obj = datetime.strptime(f'{date_string} {start_time}', '%B %d, %Y %I:%M%p')
            starting_datetime = date_obj.strftime('%Y-%m-%dT%H:%M:%S-07:00')
            starting_date = date_obj.strftime('%Y-%m-%dT00:00:00-07:00')
            starting_time = date_obj.strftime('%H:%M:%S')
            # breakpoint()
            # date += 'T00:00:00-0700'    # Add timezone for 11ty build

            presiders_info = info.css('.session-panel-heading')[1].css('::text').getall()
            presiders_info = re.sub(r'\s+', ' ', ''.join(presiders_info).strip())
            presiders = [presiders.strip() for presiders in presiders_info.split(';')]
            # presiders = [t for t in (s.strip() for s in presiders_info) if t and t != '|']
            session_type = ''.join(info.css('.session-panel-heading')[3].css('::text').getall()).strip()
            # print(f'{title=}')
            # breakpoint()

            presentations = []
            session_content = session.css('.panel-body .panel.panel-default.panel-session')
            for presentation in session_content:
                presentation_id = presentation.css('.panel-heading').xpath('@id').get()
                presentation_id_num = re.search(r'\D*(\d+)', presentation_id)
                presentation_zoom_link = f'https://acs.digitellinc.com/acs/events/{presentation_id_num[1]}/attend'

                presentation_info = presentation.css('.panel-heading .panel-title .session-panel-title')
                presentation_title = presentation_info.css('a::text').get().strip()
                presentation_datetime_info = presentation_info.css('.session-panel-heading')[0].css('::text').get().strip()
                presentation_datetime_info = re.sub(r'\s+', ' ', presentation_datetime_info)
                # presentation_datetime_string, presentation_location = datetime_info.split('|')
                # presentation_datetime_string = presentation_datetime_string.strip()
                # presentation_location = presentation_location.strip()
                presenters_info = presentation_info.css('.session-panel-heading')[1].css('::text').getall()
                presenters_info = re.sub(r'\s+', ' ', ''.join(presenters_info).strip())
                presenters = [presenter.strip() for presenter in presenters_info.split(';')]
                presentation_kwargs = {
                    'title': presentation_title,
                    'time_location': presentation_datetime_info,
                    'presenters': presenters,
                    'session_type': session_type,
                    # 'zoom_link': presentation_zoom_link,
                }
                if 'hybrid' in session_type.lower() or 'virtual' in session_type.lower():
                    presentation_kwargs['zoom_link'] = zoom_link
                presentations.append(PresentationItem(presentation_kwargs))
            # breakpoint()

            cb_kwargs = {
                'starting_datetime': starting_datetime,
                'starting_date': starting_date,
                'starting_time': starting_time,
                'title': title,
                'time_location': datetime_info,
                'presiders': presiders,
                'presentations': presentations,
                'track': track,
                'session_type': session_type,
                # 'zoom_link': zoom_link,
            }
            if 'hybrid' in session_type.lower() or 'virtual' in session_type.lower():
                cb_kwargs['zoom_link'] = zoom_link
            yield SessionItem(cb_kwargs)

        # Find next page url if exists:
        # breakpoint()
        next_page_url = response.css('.pagination.pagination-sm.pull-right')[0].css('li:nth-last-of-type(2) a').xpath('@href').get()
        # # print(f'{next_page_partial_url=}')
        if next_page_url:
            # next_page_url = response.urljoin(next_page_partial_url)
            # print(f'{next_page_url=}')
            # breakpoint()
            yield scrapy.Request(url=next_page_url, callback=self.parse)


if __name__ == '__main__':

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
            Path(THIS_SPIDER_RESULT_FILE): {
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
        # 'LOG_LEVEL': 'DEBUG',
        'LOG_FILE': 'log.log',
        # 'ROBOTSTXT_OBEY': False,
    }

    process = CrawlerProcess(settings=settings)
    process.crawl(ACSSpring2023Orgn)
    process.start()
