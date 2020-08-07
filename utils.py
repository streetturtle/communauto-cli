from xml.etree.ElementTree import parse
from bs4 import BeautifulSoup

CITY_NAME_TO_CITY_ID = {
    'Montreal': '59',
    'Sherbrooke': '89',
    'Quebec': '90',
    'Gatineau': '94',
    'Kingston': '97',
    'Ottawa': '93',
    'SW Ontario': '103'
}


STATUS_NAME_TO_STATUS_ID = {
    'Ongoing': '0',
    'Upcoming': '1',
    'Past': '2',
    'Cancelled': '3',
    'All': '4'
}


def get_station_by_id(station_id):
    """
    :param station_id: the id of the station to look in the communauto list
    :return: the station dict with all attributes
    """
    document = parse('ListStations.asp.xml')
    station = document.find(f'Station[@StationID="{station_id}"]')
    station.attrib['name'] = station.text
    return station.attrib


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
