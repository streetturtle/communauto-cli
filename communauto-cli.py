#!/usr/bin/env python3

from http import cookiejar

import utils
import click
import geopy.distance
import mechanize
from bs4 import BeautifulSoup
import json
from tabulate import tabulate


@click.group()
def main():
    pass


@main.command()
@click.option('--start_date', help='Start date of the reservation', type=click.DateTime(formats=["%d/%m/%y %H:%M"]), required=True)
@click.option('--end_date', help='End date of the reservation', type=click.DateTime(formats=["%d/%m/%y %H:%M"]), required=True)
@click.option('--lang', help='Preferred language', type=click.Choice(['en', 'fr'], case_sensitive=False), default='en')
@click.option('--username', help='Membership number / Email address or env variable: ca_user', envvar='ca_user', required=True)
@click.option('--password', help='Password or env variable: ca_password', envvar='ca_password', prompt=True, hide_input=True)
@click.option('--city', type=click.Choice(['Montreal', 'Sherbrooke', 'Quebec', 'Gatineau', 'Kingston', 'Ottawa', 'SW Ontario'], case_sensitive=False), default='Montreal')
@click.option('--output', help='Output type', type=click.Choice(['table', 'json'], case_sensitive=False), default='table')
def search(start_date, end_date, lang, username, password, city, output):
    """Search for available cars"""
    browser = authorize(username, password)

    book_url = "https://www.reservauto.net/Scripts/client/ReservationDisponibility.asp" \
               "?IgnoreError=False" \
               "&CityID=" + utils.CITY_NAME_TO_CITY_ID[city] + \
               "&StationID=C" \
               "&CustomerLocalizationID=" \
               "&OrderBy=2" \
               "&Accessories=0" \
               "&Brand=" \
               "&ShowGrid=False" \
               "&ShowMap=False" \
               "&DestinationID=" \
               "&FeeType=80" \
               "&StartYear=" + str(start_date.year) + \
               "&StartMonth=" + str(start_date.month) + \
               "&StartDay=" + str(start_date.day) + \
               "&StartHour=" + str(start_date.hour) + \
               "&StartMinute=" + str(start_date.minute) + \
               "&EndYear=" + str(end_date.year) + \
               "&EndMonth=" + str(end_date.month) + \
               "&EndDay=" + str(end_date.day) + \
               "&EndHour=" + str(end_date.hour) + \
               "&EndMinute=" + str(end_date.minute) + \
               "&CurrentLanguageID=" + ("2" if lang == 'en' else "1")

    browser.open(book_url)

    bs = BeautifulSoup(browser.response().read().decode("utf-8"), features="lxml")
    table = bs.find('table')
    stations = table.select("a[href*=InfoStation]")
    coordinates = table.select("a[href*=BillingRulesAcpt]")
    descriptions = table.find_all('td', {'align': "center", "width": "420"})[1:]
    assert len(stations) == len(coordinates) == len(descriptions)

    cars = []
    if len(stations) > 0:
        for car_idx in range(0, len(stations)):
            station_name = stations[car_idx].text.strip()
            station_id = stations[car_idx].attrs['href'].strip()
            station_id = station_id.partition("StationID=")[2].partition("\'")[0]
            station_stored_info = utils.get_station_by_id(station_id)
            user_coords = coordinates[car_idx].attrs['href'].strip()
            user_coords = user_coords.partition("false, ")[2].partition(");")[0].split(",")[0:2]
            car_desc = descriptions[car_idx].get_text(' ').strip().split(' - ')
            distance = geopy.distance.distance((user_coords[1], user_coords[0]),
                                               (station_stored_info['Latitude'], station_stored_info['Longitude'])).km
            car = {'station_name': station_name,
                   'distance': distance,
                   'car_name': " ".join(car_desc[:2]),
                   'car_features': " ".join(car_desc[2:])}
            cars.append(car)

    str_date_begin = f"{start_date.day}/{start_date.month}/{start_date.year} {start_date.hour}:{start_date.minute}"
    str_date_end = f"{end_date.day}/{end_date.month}/{end_date.year} {end_date.hour}:{end_date.minute}"
    date_range = f"{str_date_begin} - {str_date_end}"

    if output == 'table':
        print(f"Date range: {date_range}")
        header_mapping = {'station_name': 'Station Name', 'distance': 'Distance', 'car_name': 'Car',
                          'car_features': 'Features'}
        print(tabulate(cars, headers=header_mapping, tablefmt="psql", floatfmt=".1f"))
        print(f"Link: {book_url}")
    else:
        print(json.dumps({'cars': cars, 'date_range': date_range, 'link': book_url}))


@main.command()
@click.option('--username', help='Membership number / Email address or env variable: ca_user', envvar='ca_user', required=True)
@click.option('--password', help='Password or env variable: ca_password', envvar='ca_password', prompt=True, hide_input=True)
@click.option('--lang', help='Preferred language', type=click.Choice(['en', 'fr'], case_sensitive=False), default='en')
@click.option('--status', help='Reservation Status', type=click.Choice(['Ongoing', 'Upcoming', 'Past', 'Cancelled', 'All'], case_sensitive=False), default='Upcoming')
@click.option('--output', help='Output type', type=click.Choice(['table', 'json'], case_sensitive=False), default='table')
def list_reservations(username, password, lang, status, output):
    """List existing reservations"""

    browser = authorize(username, password)

    reservations_url = 'https://www.reservauto.net/Scripts/client/ReservationList.asp' \
                       '?OrderBy=1' \
                       '&ReservationStatus=' + utils.STATUS_NAME_TO_STATUS_ID[status] + \
                       '&CurrentLanguageID=' + ("2" if lang == 'en' else "1")

    browser.open(reservations_url)

    reservations = []
    bs = BeautifulSoup(browser.response().read().decode("utf-8"), features="lxml")
    table = bs.find("table", {"class": "tblReservations"})
    rows = table.findChildren(['tr'])[1:]
    for row in rows:
        cells = row.findChildren('td')
        status = cells[5].text.strip()
        if status.startswith('VRE'):
            status = 'Early return'
        price = cells[6].text.strip().replace('\t', ' ').replace('\r', ' ').replace('\n', ' ').replace('show price', '-').split()
        reservation = {'id': cells[0].text.strip(),
                       'car': utils.get_car_by_id(browser, cells[2].find('a').attrs['href'].partition('CarID=')[2].partition('&')[0], ("2" if lang == 'en' else "1"))['car_name'],
                       'from': cells[3].text.strip(),
                       'to': cells[4].text.strip(),
                       'status': status,
                       'rate': ' '.join(price[:-1]),
                       'price': price[-1],
                       'station': cells[9].text.strip()}
        reservations.append(reservation)

    if output == 'table':
        header_mapping = {'id': 'id', 'car': 'Car', 'from': 'From', 'to': 'To', 'status': 'Status', 'rate': 'Rate', 'price': 'Price', 'station': 'Station'}
        print(tabulate(reservations, headers=header_mapping, tablefmt="psql"))
    else:
        print(json.dumps({'reservations': reservations}))


def authorize(username, password):
    cj = cookiejar.CookieJar()
    browser = mechanize.Browser()
    browser.set_cookiejar(cj)
    browser.addheaders = [{'User-Agent', 'Mozilla/5.0'}]
    login_url = "https://www.communauto.com/en/my-account.html"

    # submit the first form to choose "communauto québec"
    browser.open(login_url)
    browser.select_form(nr=0)
    browser.submit()
    # submit the login form with user credentials
    browser.select_form(nr=0)
    browser.form['Username'] = username
    browser.form['Password'] = password
    browser.submit()

    # validate again the form to choose "communauto Québec" for accessing the booking
    browser.select_form(nr=0)
    browser.submit()

    return browser


if __name__ == "__main__":
    main()
