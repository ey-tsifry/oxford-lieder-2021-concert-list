2021 Oxford Lieder Festival - Concert Spreadsheet
=========

[**oxford_lieder-2021-ticket_list.csv**](oxford_lieder-2021-ticket_list.csv) combines 2021 Oxford Lieder Festival [concert](https://www.oxfordlieder.co.uk/events/forthcoming) and [ticket details](https://www.oxfordlieder.co.uk/tickets) into a single spreadsheet, which is structured as follows:

date|time (UTC+1)|title|artists|description|venue| ticket_type|venue_type|is_streaming|ticket_price_gbp| interested|categories|short_url|long_url
--|--|--|--|--|--|--|--|--|--|--|--|--|--
2021-mm-dd|HH:MM|Concert Name|Artist 1 Artist 2|Concert description|Concert venue|\<Ticket Type\>|\<Venue type - in-person, streaming, or both\>|0 or 1|\<price in GBP\>|0 or 1|\<category tag\>|/event/xxxx|https://www.oxfordlieder.co.uk/event/xxxx

This spreadsheet is intended to be used to mark individual concerts of interest for ticket purchase.

Alternatively, a [festival pass](https://www.oxfordlieder.co.uk/tickets#festival) (multiple options available) may be a better option if the total cost of interesting concerts starts to exceed the cost of a festival pass. :)

## How to re-generate the CSV file <a name="howto_generate_csv"></a>

Pre-requisites:
* Python 3.8.x: https://www.python.org/downloads/
* Required Python libraries:
  * [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/)
  * [pandas](https://pandas.pydata.org)

Instructions:
1. Save https://www.oxfordlieder.co.uk/events/forthcoming?PageSpeed=noscript to `oxford_lieder_2021.html`
2. Save https://www.oxfordlieder.co.uk/tickets/?PageSpeed=noscript to `oxford_lieder_2021_ticket_prices.html`
3. Download and run 
[**oxford_lieder_2021-extract_concert_ticket_details.py**](oxford_lieder_2021-extract_concert_ticket_details.py):
    ```
    python oxford_lieder_2021-extract_concert_ticket_details.py
    ```