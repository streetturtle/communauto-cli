#!/usr/bin/env python3

import os
from http import cookiejar
from xml.etree.ElementTree import parse

import click
import geopy.distance
import mechanize
from bs4 import BeautifulSoup
from tabulate import tabulate


@click.command()
@click.option('--start_date', help='Start date of the reservation', type=click.DateTime(formats=["%d/%m/%y %H:%M"]))
@click.option('--end_date', help='End date of the reservation', type=click.DateTime(formats=["%d/%m/%y %H:%M"]))
@click.option('--lang', type=click.Choice(['en', 'fr'], case_sensitive=False), default='en')
def search(start_date, end_date, lang):

    cj = cookiejar.CookieJar()
    browser = mechanize.Browser()
    browser.set_cookiejar(cj)
    browser.addheaders = [('User-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:78.0) Gecko/20100101 Firefox/78.0')]

    book_url = "https://www.reservauto.net/Scripts/client/ReservationDisponibility.asp" \
               "?IgnoreError=False" \
               "&CityID=59" \
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
               "&CurrentLanguageID=" + "2" if lang == 'en' else "1"
    login_url = "https://www.communauto.com/en/my-account.html"

    # submit the first form to choose "communauto québec"
    browser.open(login_url)
    browser.select_form(nr=0)
    browser.submit()
    # submit the login form with user credentials
    browser.select_form(nr=0)
    browser.form['Username'] = os.environ['communauto_user']
    browser.form['Password'] = os.environ['communauto_pwd']
    browser.submit()

    # validate again the form to choose "communauto Québec" for accessing the booking
    browser.select_form(nr=0)
    browser.submit()

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

            cars += [[station_name, distance, " ".join(car_desc[:2]), " ".join(car_desc[2:])]]

    print(f"Date range: {id_slot}")
    print(f"Link: {book_url}")
    print(tabulate(cars, headers=["Station", "Distance, km", "Car", "Features"],  tablefmt="psql", floatfmt=".1f"))


def get_station_from_id(station_id):
    """
    :param station_id: the id of the station to look in the communauto list
    :return: the station dict with all attributes
    """
    document = parse('ListStations.asp.xml')
    station = document.find(f'Station[@StationID="{station_id}"]')
    station.attrib['name'] = station.text
    return station.attrib


if __name__ == "__main__":
    search()
