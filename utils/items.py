from scrapy.item import Item, Field


class SessionItem(Item):
    # date = Field()
    starting_datetime = Field()
    starting_date = Field()
    starting_time = Field()
    track = Field()
    title = Field()
    time_location = Field()
    presiders = Field()
    presentations = Field()
    session_type = Field()
    zoom_link = Field()


class PresentationItem(SessionItem):
    presenters = Field()
