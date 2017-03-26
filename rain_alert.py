#!/usr/bin/env python3

'''
This is a program that looks up the weather for current day and
emails me if I need to dress for rain

Uses OpenWeatherMap: http://openweathermap.org/forecast5

List of city ID city.list.json.gz can be downloaded here:
    http://bulk.openweathermap.org/sample/
'''

from datetime import datetime
import pprint
import configparser
import smtplib
import sys
from email.mime.text import MIMEText
import requests

def k2f(kelvins):
    '''
    Convert temperature in Kelvins to Farenheit
    '''
    return round(kelvins * 9 / 5 - 459.67)

def k2c(kelvins):
    '''
    Convert temperature in Kelvins to Celcius
    '''
    return round(kelvins - 273.15)

def format_date(timestamp):
    '''
    Returns string formatted as mm/dd/yy hh:mm
    '''
    return datetime.fromtimestamp(timestamp).strftime('%b %d, %Y %I:%M%p')

def get_date(timestamp):
    '''
    Returns string formatted as mm/dd/yy
    '''
    return datetime.fromtimestamp(timestamp).strftime('%b %d, %Y')

def get_time(timestamp):
    '''
    Returns string formatted as HH:MM:ss
    '''
    return datetime.fromtimestamp(timestamp).strftime('%I:%M%p')

def show_json(json):
    '''
    Print (fancily) the json structure
    '''
    pprint.pprint(json)

def alert(filename, mail_settings):
    '''
    Send email alert notifying Luke that it's going to rain today
    '''
    with open(filename, 'r') as weather_log:
        msg = MIMEText(weather_log.read())

    msg['Subject'] = "Today's forecast shows rain"
    msg['From'] = mail_settings['from']
    msg['To'] = mail_settings['to']

    server = smtplib.SMTP('localhost')
    server.send_message(msg)
    server.quit()

def get_api_key(filename):
    '''Get API key for OpenWeatherMaps from specified file so API key is not
    hard-coded in the code.

    Args:
        filename: string location of file containing API key (and only api key)

    Returns:
        API key in string format
    '''
    with open(filename, 'r') as f:
        api_key = f.read().rstrip()

    return api_key

def main():
    '''Query weather from openweathermap and log it.

    Send email if it's going to rain today
    '''
    url = 'http://api.openweathermap.org/data/2.5/forecast'
    icon_prefix = 'http://openweathermap.org/img/w/'

    config_file = '/home/luke/python/rainAlert/rainAlert.ini'

    #Read configuration and get options (mail settings, log file, api key, etc.)
    config = configparser.ConfigParser()
    config.read(config_file)

    api_file = config.get('API Key', 'KeyFile')
    logfile = config.get('Log File', 'LogFile')

    mail_settings = {}
    mail_settings['from'] = config.get('Mail Settings', 'From')
    mail_settings['to'] = config.get('Mail Settings', 'To')

    #Payload
    city_id = config.get('Location', 'CityID')
    appid = get_api_key(api_file)

    payload = {'id': city_id, 'appid': appid}
    response = requests.get(url, params=payload)

    rain_flag = False

    output_list = []

    for item in response.json()['list']:
        if datetime.now().day == datetime.fromtimestamp(item['dt']).day:
            #Weather codes from open weather map
            #http://openweathermap.org/weather-conditions

            #Weather ID = int(item['weather'][0]['id'])

            #Group 2xx: Thunderstorm || Group 3xx: Drizzle
            #Group 5xx: Rain ||  Group 6xx: Snow

            if int(item['weather'][0]['id']) < 700:
                rain_flag = True

            descr = item['weather'][0]['description']
            temperature = k2f(item['main']['temp'])
            icon = item['weather'][0]['icon'] + '.png'

            output_list.append('{}: {}, {} degrees'.format(
                get_time(item['dt']), descr, temperature))

    with open(logfile, 'w') as log_file:
        log_file.write('{} Weather: {}\n\n{}\n'.format(
            response.json()['city']['name'],
            icon_prefix + icon, get_date(item['dt'])))

        log_file.write('\n'.join(output_list))
        log_file.write('\n')

    if rain_flag:
        alert(logfile, mail_settings)

if __name__ == '__main__':
    main()
