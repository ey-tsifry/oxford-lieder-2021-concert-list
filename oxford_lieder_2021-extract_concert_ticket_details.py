#!/usr/bin/env python
# coding: utf-8


# In[ ]:
import os
import unicodedata
from datetime import datetime
from typing import Dict, List, Tuple, Union
from urllib.parse import parse_qs

import pandas as pd
from bs4 import BeautifulSoup, element

# In[ ]:
TICKET_METADATA_COLUMNS: Dict = {
    "ticket_type": "ticket_type",
    "venue_type": "venue_type",
    "is_streaming": "is_streaming",
    "ticket_price_gbp": "ticket_price_gbp",
}
ALL_COLUMNS: List[str] = (
    ["date", "time", "title", "artists", "description", "venue"]
    + list(TICKET_METADATA_COLUMNS)
    + ["interested", "categories", "short_url", "long_url"]
)
EVENT_METADATA_COLUMNS: Dict = {
    column: column for column in ALL_COLUMNS if column not in list(TICKET_METADATA_COLUMNS)
}


# In[ ]:
def load_html(html_file: str) -> BeautifulSoup:
    """
    Import Oxford Lieder Festival HTML file contents.

    :param html_file: Local HTML copy of Oxford Lieder Festival website page
    :return: BeautifulSoup object representing the HTML contents
    """
    soup: BeautifulSoup
    try:
        with open(html_file, "r", encoding="utf-8") as in_file:
            soup = BeautifulSoup(in_file, "lxml")
    except OSError as e:
        print(e)
    else:
        return soup


def extract_all_event_items(soup: BeautifulSoup) -> List[element.Tag]:
    """
    Return list of all concert events. Each list element represents metadata for an individual concert.

    :param soup: BeautifulSoup object representing the HTML contents
    :return: List of concert events
    """
    event_list: List[element.Tag] = soup.find_all("div", attrs={"class": "col-sm-9"})
    return event_list


def extract_all_ticket_items(soup: BeautifulSoup) -> List[element.Tag]:
    """
    Return list of concert events with ticket details (price, access options).

    :param soup: BeautifulSoup object representing the HTML contents
    :return: List of ticket details per concert
    """
    ticket_detail_list: List[element.Tag] = []
    single_ticket_table = soup.find(
        "div", attrs={"id": "single", "class": "ticketing-section"}
    ).tbody
    ticket_detail_list = single_ticket_table.find_all("tr")
    return ticket_detail_list


# In[ ]:
def get_event_artist_list(event_item: element.Tag) -> List[str]:
    """
    Return list of event artists.

    :param event_item: Metadata item for a single concert
    :return: List of artists
    """
    artist_list: List[str] = []
    ul_items = event_item.find("ul", attrs={"class": "artistlist"}).find_all("li")
    artist_list = [artist.text.strip() for artist in ul_items]
    return artist_list


def get_event_categories(event_item: element.Tag) -> List[str]:
    """
    Return list of event category tags.

    :param event_item: Metadata item for a single concert
    :return: List of event categories
    """
    category_list: List[str] = []
    category_hrefs = event_item.find_all("a", attrs={"class": "btn btn-xs btn-primary"})
    category_list_values = [
        parse_qs(category["href"])["?category"][0] for category in category_hrefs
    ]
    return category_list_values


def get_event_date_and_time(event_item: element.Tag) -> Tuple[str, str]:
    """
    Return event date and time.

    :param event_item: Metadata for a single concert
    :return: Date and time strings
    """
    event_datetime = datetime.strptime(
        str(event_item.find("i", attrs={"class": "glyphicon glyphicon-time"}).next_element).strip(),
        "%d %b %Y %H:%M",
    )
    event_date: str = event_datetime.date().strftime("%Y-%m-%d")
    event_time: str = event_datetime.time().strftime("%H:%M")
    return event_date, event_time


def get_event_description_blurb(event_item: element.Tag) -> str:
    """
    Return event description blurb.

    :param event_item: Metadata item for a single concert
    :return: Event description blurb
    """
    event_blurb_text = str(event_item.find_all("p")[-1].next_sibling.strip())
    return unicodedata.normalize("NFKC", event_blurb_text)


def get_event_title_and_urls(event_item: element.Tag) -> Tuple[str, str, str]:
    """
    Return event title, short URL, and long URL.

    :param event_item: Metadata item for a single concert
    :return: Event title, short URL and long URL
    """
    event_href = event_item.find("h4")
    event_short_url = event_href.a["href"]
    event_long_url = "https://www.oxfordlieder.co.uk" + event_short_url
    event_title = event_href.text.strip()
    return event_title, event_short_url, event_long_url


def get_event_venue(event_item: element.Tag) -> str:
    """
    Return event venue.

    :param event_item: Metadata item for a single concert
    :return: Event venue string
    """
    event_venue = (
        event_item.find("small", attrs={"class": "text-muted"}).next_sibling.rsplit("|")[-1].strip()
    )
    return event_venue


def return_if_venue_has_streaming(venue_type: str) -> bool:
    """
    Return whether venue type includes a streaming option.

    Known venue type strings:
    In-person & Streaming (Digital Concert Hall)
    In-person only
    Digital Concert Hall - Live stream only
    SongPaths - including £5 donation to Oxfordshire Mind
    Under 35s: Digital Concert Hall - Live stream only

    :param venue_type: Venue type string
    :return: True or False
    """
    return any(venue in venue_type.lower() for venue in ["stream"])


# In[ ]:
def extract_ticket_price_options(
    ticket_detail_list: List[element.Tag], ticket_fields: Dict = TICKET_METADATA_COLUMNS
) -> Dict:
    """
    Return ticket prices and access options (in-person, streaming) for each event.

    :param ticket_detail_list: List of ticket details per concert
    :param ticket_fields: Ticket metadata fields
    :return: Dictionary of ticket metadata for each event
    """
    ticket_details: Dict = {}
    last_event_url_key: str = ""

    for row in ticket_detail_list:
        event_url_key = row.select_one('a[href^="/event"]')
        table_columns = row.find_all("td")[2:4]
        ticket_data = {}
        (ticket_data[ticket_fields["ticket_type"]], ticket_data[ticket_fields["venue_type"]]) = (
            table_columns[0].text.strip().split("\n")[0:2]
        )
        ticket_data[ticket_fields["is_streaming"]] = return_if_venue_has_streaming(
            ticket_data[ticket_fields["venue_type"]]
        )
        ticket_data[ticket_fields["ticket_price_gbp"]] = int(
            float(table_columns[1].text.strip().replace("£", ""))
        )
        if event_url_key:
            event_url_key = event_url_key["href"]
            last_event_url_key = event_url_key
            if event_url_key not in ticket_details:
                ticket_details[event_url_key] = {}
                for ticket_attr in ticket_fields:
                    ticket_details[event_url_key][ticket_attr] = [ticket_data[ticket_attr]]
            else:
                continue
        else:
            for ticket_attr in ticket_fields:
                ticket_details[last_event_url_key][ticket_attr].append(ticket_data[ticket_attr])
    return ticket_details


# In[ ]:
def extract_event_metadata(
    event_list: List[element.Tag], event_fields: Dict = EVENT_METADATA_COLUMNS
) -> List[Dict]:
    """
    Extract event metadata such as date/time, title, description.

    :param event_list: List of concert details
    :param event_fields: Event metadata fields
    :return: List of structured event metadata
    """
    event_metadata_list: List[Dict] = []

    for event in event_list:
        event_record: Dict[str, Union[int, str]] = dict.fromkeys(list(event_fields))
        (
            event_record[event_fields["date"]],
            event_record[event_fields["time"]],
        ) = get_event_date_and_time(event)
        (
            event_record[event_fields["title"]],
            event_record[event_fields["short_url"]],
            event_record[event_fields["long_url"]],
        ) = get_event_title_and_urls(event)
        event_record[event_fields["description"]] = get_event_description_blurb(event)
        event_record[event_fields["venue"]] = get_event_venue(event)
        event_record[event_fields["artists"]] = "\n".join(get_event_artist_list(event))
        event_record[event_fields["categories"]] = "\n".join(get_event_categories(event))
        event_record[event_fields["interested"]] = 0
        event_metadata_list.append(event_record)
    return event_metadata_list


# In[ ]:
def generate_event_html_content(merged_event_ticket_df: pd.DataFrame) -> str:
    """
    Return HTML header code for the export HTML file.

    :param merged_event_ticket_df: Merged event and ticket dataframe
    :return: HTML string
    """
    table_id = "oxford_lieder_2021"

    html_header = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Oxford Lieder 2021 - Concerts and Ticket Details</title>
<link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/1.10.25/css/jquery.dataTables.min.css">
<script src="https://code.jquery.com/jquery-3.6.0.min.js" integrity="sha256-/xUj+3OJU5yExlq6GSYGSHk7tPXikynS7ogEvDej/m4=" crossorigin="anonymous"></script>
<script type="text/javascript" charset="utf8" src="https://cdn.datatables.net/1.10.25/js/jquery.dataTables.min.js"></script>
<script type="text/javascript" language="javascript" class="init">
$(document).ready( function () {
    $('#oxford_lieder_2021').DataTable(
        {
            "pageLength": 50
        }
    );
} );
</script>
</head>
<body>"""

    html_footer = """
</body>
</html>"""
    html_body = merged_event_ticket_df.to_html(
        classes=["display", "compact"], table_id=table_id, escape=False, render_links=True
    )
    return html_header + html_body + html_footer


# In[ ]:
def generate_event_html_df(
    merged_event_ticket_df: pd.DataFrame, event_fields: Dict = EVENT_METADATA_COLUMNS
) -> pd.DataFrame:
    """
    Return HTML-friendly version of the merged event and ticket dataframe.

    :param merged_event_ticket_df: Merged event and ticket dataframe
    :param event_fields: Event metadata fields
    :return: Dataframe ready for HTML export
    """
    html_df = merged_event_ticket_df.copy()
    for field_name in ["artists", "categories", "description"]:
        html_df[event_fields[field_name]] = html_df[event_fields[field_name]].apply(
            lambda text: text.replace("\n", "<br>")
        )
    html_df = html_df.drop(event_fields["interested"], axis=1)
    return html_df


# In[ ]:
def main():
    """Run main program."""
    # base name of export file
    EXPORT_FILE_BASE = "oxford_lieder-2021-ticket_list"

    # load event list
    # source: https://www.oxfordlieder.co.uk/events/forthcoming?PageSpeed=noscript
    event_soup = load_html("oxford_lieder_2021.html")
    event_list = extract_all_event_items(event_soup)
    # load ticket list
    # source: https://www.oxfordlieder.co.uk/tickets/?PageSpeed=noscript
    ticket_soup = load_html("oxford_lieder_2021_ticket_prices.html")
    ticket_detail_list = extract_all_ticket_items(ticket_soup)

    # create base event and ticket dataframes
    event_key = EVENT_METADATA_COLUMNS["short_url"]
    event_df = pd.DataFrame(extract_event_metadata(event_list)).sort_values(
        by=[EVENT_METADATA_COLUMNS["title"]]
    )
    ticket_df = (
        pd.DataFrame.from_dict(extract_ticket_price_options(ticket_detail_list), orient="index")
        .reset_index()
        .rename(columns={"index": event_key})
    )
    ticket_df = ticket_df.set_index(event_key).apply(pd.Series.explode).reset_index()

    # join event and ticket data
    merged_df = pd.merge(event_df, ticket_df, left_on=event_key, right_on=event_key, how="inner")[
        ALL_COLUMNS
    ]
    merged_df[TICKET_METADATA_COLUMNS["is_streaming"]] = merged_df[
        TICKET_METADATA_COLUMNS["is_streaming"]
    ].apply(lambda value: 1 if value else 0)
    merged_df = merged_df.rename(columns={EVENT_METADATA_COLUMNS["time"]: "time (UTC+1)"})
    num_rows, num_cols = merged_df.shape

    # export to CSV and HTML
    try:
        export_csv = EXPORT_FILE_BASE + ".csv"
        merged_df.to_csv(export_csv, index=False)
        export_html = EXPORT_FILE_BASE + ".html"
        html_content = generate_event_html_content(generate_event_html_df(merged_df))
        with open(export_html, "w", encoding="utf-8") as out_file:
            out_file.write(html_content)
    except OSError as e:
        print(f"There was an error exporting {export_csv}: {e}")
    else:
        print(
            " ".join(
                [
                    f"CSV export succeeded [{num_rows} rows, {num_cols} columns]:",
                    os.path.abspath(export_csv),
                ]
            )
        )
        print(
            " ".join(
                [
                    f"HTML export succeeded [{num_rows} rows, {num_cols} columns]:",
                    os.path.abspath(export_html),
                ]
            )
        )


# In[ ]:
if __name__ == "__main__":
    main()
