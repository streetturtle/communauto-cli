#!/usr/bin/env python3

from http import cookiejar
from xml.etree.ElementTree import parse

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
@click.option('--username', help='Membership number / Email address or env variable = ca_user', envvar='ca_user', required=True)
@click.option('--password', help='Password or env variable = ca_password', envvar='ca_password', prompt=True, hide_input=True)
@click.option('--city', type=click.Choice(['Montreal', 'Sherbrooke', 'Quebec', 'Gatineau', 'Kingston', 'Ottawa', 'SW Ontario'], case_sensitive=False), default='Montreal')
@click.option('--output', help='Output type', type=click.Choice(['table', 'json'], case_sensitive=False), default='table')
def search(start_date, end_date, lang, username, password, city, output):
    """Searches for available communauto cars for the given period"""
    browser = authorize(username, password)
    city_name_to_city_id = {
        'Montreal': '59',
        'Sherbrooke': '89',
        'Quebec': '90',
        'Gatineau': '94',
        'Kingston': '97',
        'Ottawa': '93',
        'SW Ontario': '103'
    }

    book_url = "https://www.reservauto.net/Scripts/client/ReservationDisponibility.asp" \
               "?IgnoreError=False" \
               "&CityID=" + city_name_to_city_id[city] + \
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

    str_date_begin = f"{start_date.day}/{start_date.month}/{start_date.year} {start_date.hour}:{start_date.minute}"
    str_date_end = f"{end_date.day}/{end_date.month}/{end_date.year} {end_date.hour}:{end_date.minute}"
    id_slot = f"{str_date_begin} - {str_date_end}"

    browser.open(book_url)

    soup = BeautifulSoup(browser.response().read().decode("utf-8"), features="lxml")
    soup = soup.find('table')
    soup_stations = soup.select("a[href*=InfoStation]")
    soup_coords = soup.select("a[href*=BillingRulesAcpt]")
    soup_descs = soup.find_all('td', {'align': "center", "width": "420"})[1:]
    assert len(soup_stations) == len(soup_coords) == len(soup_descs)

    cars = []
    if len(soup_stations) > 0:
        for car_idx in range(0, len(soup_stations)):
            station_name = soup_stations[car_idx].text.strip()
            station_id = soup_stations[car_idx].attrs['href'].strip()
            station_id = station_id.partition("StationID=")[2].partition("\'")[0]
            station_stored_info = get_station_from_id(station_id)
            user_coords = soup_coords[car_idx].attrs['href'].strip()
            user_coords = user_coords.partition("false, ")[2].partition(");")[0].split(",")[0:2]
            car_desc = soup_descs[car_idx].get_text(' ').strip().split(' - ')
            distance = geopy.distance.distance((user_coords[1], user_coords[0]),
                                               (station_stored_info['Latitude'], station_stored_info['Longitude'])).km
            car = {'station_name': station_name,
                   'distance': distance,
                   'car_name': " ".join(car_desc[:2]),
                   'car_features': " ".join(car_desc[2:])}
            cars.append(car)

    if output == 'table':
        print(f"Date range: {id_slot}")
        print(tabulate(cars, headers={'station_name': 'Station Name', 'distance': 'Distance', 'car_name': 'Car', 'car_features': 'Features'}, tablefmt="psql", floatfmt=".1f"))
        print(f"Link: {book_url}")
    else:
        print(json.dumps({'cars': cars, 'date_range': id_slot, 'link': book_url}))


@main.command()
@click.option('--username', help='Membership number / Email address (env variable = ca_user)', envvar='ca_user', required=True)
@click.option('--password', help='Password (env variable = ca_password)', envvar='ca_password', prompt=True, hide_input=True)
@click.option('--lang', help='Preferred language', type=click.Choice(['en', 'fr'], case_sensitive=False), default='en')
@click.option('--status', help='Reservation Status', type=click.Choice(['Ongoing', 'Upcoming', 'Past', 'Cancelled', 'All'], case_sensitive=False), default='Upcoming')
@click.option('--output', help='Output type', type=click.Choice(['table', 'json'], case_sensitive=False), default='table')
def list_reservations(username, password, lang, status, output):
    """List existing reservations"""

    status_name_to_status_id = {
        'Ongoing': '0',
        'Upcoming': '1',
        'Past': '2',
        'Cancelled': '3',
        'All': '4'
    }
    browser = authorize(username, password)

    reservations_url = 'https://www.reservauto.net/Scripts/client/ReservationList.asp' \
                       '?OrderBy=1' \
                       '&ReservationStatus=' + status_name_to_status_id[status] + \
                       '&CurrentLanguageID=' + ("2" if lang == 'en' else "1")

    print(reservations_url)
    browser.open(reservations_url)

    reservations = []
    bs = BeautifulSoup(browser.response().read().decode("utf-8"), features="lxml")
    table = bs.find("table", {"class": "tblReservations"})
    rows = table.findChildren(['tr'])[1:]
    for row in rows:
        cells = row.findChildren('td')
        reservation = {'id': cells[0].text.strip(),
                       'car': get_car_by_id(browser, cells[2].find('a').attrs['href'].partition('CarID=')[2].partition('&')[0], ("2" if lang == 'en' else "1"))['car_name'],
                       'from': cells[3].text.strip(),
                       'to': cells[4].text.strip(),
                       'station': cells[9].text.strip()
                       }
        reservations.append(reservation)

    if output == 'table':
        print(tabulate(reservations, headers={'id': 'id', 'car': 'Car', 'from': 'From', 'to': 'To', 'station': 'Station'}, tablefmt="psql"))
    else:
        print(json.dumps({'reservations': reservations}))


def get_car_by_id(browser, car_id, lang_id):
    """
    Returns a car by given id
    :param browser: authenticated browser
    :param car_id: car id
    :param lang_id: preferred language id
    :return: dict with car name and car features
    """

    car_desc_url = 'https://www.reservauto.net/Scripts/client/CarDescription.asp' \
                   '?CurrentLanguageID=' + lang_id + \
                   '&CarID=' + car_id

    browser.open(car_desc_url)
    bs = BeautifulSoup(browser.response().read().decode("utf-8"), features="lxml")

    desc = bs.find_all('font', {'face': 'Arial, Helvetica, sans-serif'})[0].text.strip().split(' - ')

    return {'car_name': ' '.join(desc[0:3]), 'car_features': desc[3:]}


def get_station_from_id(station_id):
    """
    :param station_id: the id of the station to look in the communauto list
    :return: the station dict with all attributes
    """
    document = parse('ListStations.asp.xml')
    station = document.find(f'Station[@StationID="{station_id}"]')
    station.attrib['name'] = station.text
    return station.attrib


def authorize(username, password):
    cj = cookiejar.CookieJar()
    browser = mechanize.Browser()
    browser.set_cookiejar(cj)
    browser.addheaders = [('User-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:78.0) Gecko/20100101 Firefox/78.0')]
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
