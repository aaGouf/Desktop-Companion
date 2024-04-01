import network
import requests, json
import gc
import board
from machine import Pin, I2C, SPI
from pprint import pprint
import math
from time import sleep
from ili9341 import Display, color565
from machine import Pin, SPI
import time
import tm1637
from xglcd_font import XglcdFont
import ntptime
import config
import urequests

calendar = config.CALENDAR
api_key = config.APIKEY

arcadepix = XglcdFont('ArcadePix9x11.c', 9, 11)
motion_sensor = Pin(0, Pin.IN, Pin.PULL_DOWN)
screen_select = 0
spi = SPI(1, baudrate=40000000, sck=Pin(14), mosi=Pin(15))
display = Display(spi, dc=Pin(6), cs=Pin(17), rst=Pin(7))
tm = tm1637.TM1637(clk=Pin(5), dio=Pin(4))
display.clear()

def connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect('SSID', 'PASSWORD')
    print('connected!')

def find_weather():
    global temps
    global conditions
    temps = []
    conditions = []
    current = time.gmtime(time.time() + -6 * 3600)
    api_key = "openweathermap API key"
    city = 'Your City Name'
    base_url = "http://api.openweathermap.org/data/2.5/forecast?"
    complete_url = base_url + "appid=" + api_key + "&q=" + city
    response = requests.get(complete_url)
    gc.collect()
    x = response.json()
    current_time = time.strftime("%H:%M:%S", current)
    hour = str(current_time[0]) + str(current_time[1])
    while True:
        if int(hour) / 3 not in list(range(1,8)):
            hour = int(hour) + 1
        else:  
            time_search = str(hour) + ':00:00'
            break
    for i in list(range(0,39)):
        if time_search in x['list'][i]['dt_txt']:
            temps.append(round(x['list'][0]['main']['temp'] - 273.15))
            temps.append(round(x['list'][i]['main']['temp'] - 273.15))
            conditions.append(x['list'][0]['weather'][0]['main'])
            conditions.append(x['list'][i]['weather'][0]['main'])
    print(temps)
    print(conditions)
    gc.collect()

def International_News():
    search = requests.get("https://api.rss2json.com/v1/api.json?rss_url=https%3A%2F%2Fglobalnews.ca%2Fworld%2Ffeed%2F") # replace with your city's news RSS to json url
    global results
    results = []
    for story in range(0, 4):
        results.append(search.json()['items'][story]['title'])
    gc.collect()

def Canadian_News():
    results = requests.get("https://api.rss2json.com/v1/api.json?rss_url=https%3A%2F%2Fglobalnews.ca%2Fcalgary%2Ffeed%2F")
    global local_results
    peen = []
    for story in range(0, 4):
        peen.append(results.json()['items'][story]['title'])
    local_results = '   '.join(peen)
    gc.collect()

def convert_time(event_start_times, event_end_times):
    global event_start
    global event_end
    
    event_start = []
    event_end = []
    
    for i in event_start_times:
        hours, minutes = map(int, i.split(":"))
        meridian = "AM"
        if hours > 12:
            hours -= 12
            meridian = "PM"
        elif hours == 12:
            meridian = "PM"
        elif hours == 0:
            hours = 12
        s = [str(hours) + ':' + str(minutes), meridian]
        event_start.append(s)
        
    for n in event_end_times:
        hours, minutes = map(int, n.split(":"))
        meridian = "AM"
        if hours > 12:
            hours -= 12
            meridian = "PM"
        elif hours == 12:
            meridian = "PM"
        elif hours == 0:
            hours = 12
        e = [str(hours) + ':' + str(minutes), meridian]
        event_end.append(e)
        
def find_days_in_month():
    global num_days
    m = time.strftime("%m", time.localtime())
    month = int(m[1])
    year = int(time.strftime("%Y", time.localtime()))
    if((month==2) and ((year%4==0)  or ((year%100==0) and (year%400==0)))) :
        num_days = 29
    elif(month==2) :
        num_days = 28
 
    elif(month==1 or month==3 or month==5 or month==7 or month==8 or month==10 or month==12) :
        num_days = 31
 
    else :
        num_days = 30
        
def get_event_details(calendar_id, api_key, tz):
    rtc = machine.RTC()
    year, month, day, _, hour, minute, _, _ = rtc.datetime()
    date = "{:04d}-{:02d}".format(year, month)
    url = 'https://www.googleapis.com/calendar/v3/calendars/{calendar}/events?timeMin=' + date + '-01T00:00:00Z&key={api_key}'
    response = urequests.get(url)
    data = response.json()

    global event_name
    global events_today
    global occupied_dates
    
    events_today = 0
    event_name = []
    event_start = []
    event_end = []
    
    for n in data['items']:
        event_name.append(n['summary'])
        event_start.append(n['start']['dateTime'])
        event_end.append(n['end']['dateTime'])
        
    raw_dates = []
    for date in event_start:
        for n in range(0,10):
            raw_dates.append(str(date[n]))
    out = [raw_dates[k:k+10] for k in range(0, len(raw_dates), 10)]
    dates = []
    
    for i in out:
        final = ''.join(i)
        dates.append(final)
        
    start_time = []
    for date in event_start:
        for n in range(11,16):
            start_time.append(str(date[n]))
    out = [start_time[k:k+5] for k in range(0, len(start_time), 5)]
    event_start_times = []
    for i in out:
        final = ''.join(i)
        event_start_times.append(final)
        
    end_time = []
    for date in event_end:
        for n in range(11,16):
            end_time.append(str(date[n]))
    out = [end_time[k:k+5] for k in range(0, len(end_time), 5)]
    event_end_times = []
    for i in out:
        final = ''.join(i)
        event_end_times.append(final)
    
    convert_time(event_start_times, event_end_times)
    current_time = time.localtime()
    current_day = time.strftime("%Y-%m-%d", current_time)
    events_today = dates.count(current_day)
    occupied_dates = []
    for i in range(len(dates)):
        occupied_dates.append(dates[i][8] + dates[i][9])
        
def find_availability():
    for i in range(1,7):
        if str(i) in occupied_dates:
            availability = color565(255, 0, 0)
        else:
            availability = color565(0, 255, 0)
        display.fill_rectangle(155, 12 + 43 * i, 33, 40, availability)
    for i in range(1,7):
        if str(i + 7) in occupied_dates:
            availability = color565(255, 0, 0)
        else:
            availability = color565(0, 255, 0)
        display.fill_rectangle(120, 12, 33, 40, availability)
        display.fill_rectangle(120, 12 + 43 * i, 33, 40, availability)
    for i in range(1,7):
        if str(i + 14) in occupied_dates:
            availability = color565(255, 0, 0)
        else:
            availability = color565(0, 255, 0)
        display.fill_rectangle(85, 12, 33, 40, availability)
        display.fill_rectangle(85, 12 + 43 * i, 33, 40, availability)
        for i in range(1,7):
            if str(i + 21) in occupied_dates:
                availability = color565(255, 0, 0)
            else:
                availability = color565(0, 255, 0)
            display.fill_rectangle(50, 12, 33, 40, availability)
            display.fill_rectangle(50, 12 + 43 * i, 33, 40, availability)
    for i in range(1,7):
        if str(i + 28) in occupied_dates:
            availability = color565(255, 0, 0)
        else:
            availability = color565(0, 255, 0)
        display.fill_rectangle(15, 12, 33, 40, availability)
        display.fill_rectangle(15, 12 + 43 * i, 33, 40, availability)
        
def main_screen(events_today):
    x = time.gmtime(time.time() + -6 * 3600)
    display.clear(color565(255, 255, 255))
    display.fill_rectangle(215, 10, 20, 295, color565(0, 0, 0))
    display.fill_rectangle(34, 10, 173, 163, color565(0, 0, 0))
    display.fill_rectangle(32, 211, 86, 92, color565(0, 0, 0))
    display.fill_rectangle(121, 211, 86, 92, color565(0, 0, 0))
    display.draw_text(185, 135,'Events Today', arcadepix, color565(255, 255, 0), landscape = True, rotate_180= True)
    display.draw_text(66, 270,str(temps[0]) + '*' + 'C', arcadepix, color565(255, 255, 0), landscape = True, rotate_180= True)
    display.draw_text(160, 287, str(time.strftime('%I:%M %P', x)), arcadepix, color565(255, 255, 0), landscape = True, rotate_180= True)
    y = 230
    d = 80
    z = 210

    if events_today > 3:
        events_today = 3
        display.draw_text(40, 160, 'More Events on App', arcadepix, color565(255, 255, 0), landscape = True, rotate_180= True)
    
    for i in range (0, events_today):
        display.draw_text(y - d - 45*(i) + 10, 70, event_name[i], arcadepix, color565(255, 255, 0), landscape = True, rotate_180= True)
        display.draw_text(y - d - 45*(i) - 10, 160, event_start[i][0] + event_start[i][1], arcadepix, color565(255, 255, 0), landscape = True, rotate_180= True)
        display.draw_text(y - d - 45*(i) + 10, 160, event_end[i][0] + event_end[i][1], arcadepix, color565(255, 255, 0), landscape = True, rotate_180= True)
    time.sleep(2)
    current_time = int(time.strftime("%M", time.localtime()))
    while True:
        for i in range(len(local_results) - 38):
            display.draw_text(220, 300, local_results[i:i+39], arcadepix, color565(255, 255, 0), landscape = True, rotate_180= True)
            if motion_sensor.value() == 1:
               return create_calendar()
            if int(time.strftime("%M", time.localtime())) == current_time + 2:
                display.clear(color565(0, 0, 0))
                return idle_clock() 
    return create_calendar()

def news_screen():
    display.clear(color565(255, 255, 255))
    display.fill_rectangle(205, 10, 30, 300, color565(0, 0, 0))
    display.draw_text(215, 205,'Global News', arcadepix, color565(255, 255, 0), landscape = True, rotate_180= True)
    y = 240
    d = 100
    print(results[0])
    for z in range(0, 4):
        display.fill_rectangle(y - d - 45*(z), 10, 50, 300, color565(0, 0, 0))
    time.sleep(1)
    current_time = int(time.strftime("%M", time.localtime()))
    while motion_sensor.value() == 0:
        for i in range(len(results[0]) - 30):
            display.draw_text(y - d - 45*(0) + 30, 270, results[0][i:i+31], arcadepix, color565(255, 255, 0), landscape = True, rotate_180= True)
            display.draw_text(y - d - 45*(1) + 30, 270, results[1][i:i+31], arcadepix, color565(255, 255, 0), landscape = True, rotate_180= True)
            display.draw_text(y - d - 45*(2) + 30, 270, results[2][i:i+31], arcadepix, color565(255, 255, 0), landscape = True, rotate_180= True)
            display.draw_text(y - d - 45*(3) + 30, 270, results[3][i:i+31], arcadepix, color565(255, 255, 0), landscape = True, rotate_180= True)
            if motion_sensor.value() == 1:
                print('switching')
                break
            if int(time.strftime("%M", time.localtime())) == current_time + 2:
                display.clear(color565(0, 0, 0))
                return idle_clock() 
    return main_screen(events_today)


def weather_screen():
    display.clear(color565(255, 255, 255))
    display.fill_rectangle(205, 10, 30, 300, color565(0, 0, 0))
    display.draw_text(215, 190,'Weather', arcadepix, color565(255, 255, 0), landscape = True, rotate_180= True)
    y = 240
    d = 100
    days = ['Today:     ', 'Tomorrow: ', 'Day After:']
    for i in range(0,3):
        display.fill_rectangle(y - d - 45*(i), 10, 50, 300, color565(0, 0, 0))
        display.draw_text(y - d - 45*(i) + 20, 100, days[i], arcadepix, color565(255, 255, 0), landscape = True, rotate_180= True)
    display.draw_text(y - d - 45*(0) + 30, 300, str(temps[0]) + '*' + 'C', arcadepix, color565(255, 255, 0), landscape = True, rotate_180= True)
    display.draw_text(y - d - 45*(0) + 10, 300, conditions[0], arcadepix, color565(255, 255, 0), landscape = True, rotate_180= True)
    display.draw_text(y - d - 45*(1) + 30, 300, str(temps[1]) + '*' + 'C', arcadepix, color565(255, 255, 0), landscape = True, rotate_180= True)
    display.draw_text(y - d - 45*(1) + 10, 300, conditions[1], arcadepix, color565(255, 255, 0), landscape = True, rotate_180= True)
    display.draw_text(y - d - 45*(2) + 30, 300, str(temps[3]) + '*' + 'C', arcadepix, color565(255, 255, 0), landscape = True, rotate_180= True)
    display.draw_text(y - d - 45*(2) + 10, 300, conditions[3], arcadepix, color565(255, 255, 0), landscape = True, rotate_180= True)
    time.sleep(2)   
    current_time = int(time.strftime("%M", time.localtime()))
    while True:
        if motion_sensor.value() == 1:
            return news_screen()
        if int(time.strftime("%M", time.localtime())) == current_time + 1:
            display.clear(color565(0, 0, 0))
            return idle_clock()            
    
def create_calendar():
    find_days_in_month()
    display.clear(color565(255, 255, 255))
    display.fill_rectangle(205, 10, 30, 300, color565(0, 0, 0))
    display.draw_text(215, 180, time.strftime("%b", time.localtime()) , arcadepix, color565(255, 255, 0), landscape = True, rotate_180= True)
    display.fill_rectangle(10, 10, 180, 300, color565(0, 0, 0))
    display.draw_image('/tip.raw', x=10, y=10, w=180, h=300)
    find_availability()
    for i in range(1,7):
        display.draw_text(180, 22 + 43*i, str(i) , arcadepix, color565(0, 0, 0), color565(255, 255, 255),landscape = True, rotate_180= True)
        display.draw_text(140, 20, str(7) , arcadepix, color565(0, 0, 0), color565(255, 255, 255), landscape = True, rotate_180= True)
        display.draw_text(140, 25 + 44*i, str(i + 7) , arcadepix, color565(0, 0, 0), color565(255, 255, 255),landscape = True, rotate_180= True)
        display.draw_text(105, 28, str(14) , arcadepix, color565(0, 0, 0), color565(255, 255, 255),landscape = True, rotate_180= True)
        display.draw_text(105, 28 + 44*i, str(i + 14) , arcadepix, color565(0, 0, 0), color565(255, 255, 255),landscape = True, rotate_180= True)
        display.draw_text(68, 28, str(21) , arcadepix, color565(0, 0, 0), color565(255, 255, 255),landscape = True, rotate_180= True)
        display.draw_text(68, 28 + 44*i, str(i + 21) , arcadepix, color565(0, 0, 0), color565(255, 255, 255),landscape = True, rotate_180= True)
        display.draw_text(32, 28, str(28) , arcadepix, color565(0, 0, 0), color565(255, 255, 255),landscape = True, rotate_180= True)
        if num_days == 28:
            break
        else:
            display.draw_text(32, 75, str(29) , arcadepix, color565(0, 0, 0), color565(255, 255, 255),landscape = True, rotate_180= True)
        if num_days != 31:
            display.draw_text(32, 118, str(30) , arcadepix, color565(0, 0, 0), color565(255, 255, 255),landscape = True, rotate_180= True)
        else:
            display.draw_text(32, 118, str(30) , arcadepix, color565(0, 0, 0), color565(255, 255, 255),landscape = True, rotate_180= True)
            display.draw_text(32, 160, str(31) , arcadepix, color565(0, 0, 0), color565(255, 255, 255),landscape = True, rotate_180= True)
    time.sleep(2)
    current_time = int(time.strftime("%M", time.localtime()))
    while True:
        if motion_sensor.value() == 1:
            return weather_screen()
        if int(time.strftime("%M", time.localtime())) == current_time + 2:
            display.clear(color565(0, 0, 0))
            return idle_clock()     

def idle_clock():
    screen_on = False
    while True:
        x = time.gmtime(time.time() + -6 * 3600)
        tm.brightness(7)
        time.sleep(1)
        hh = int(time.strftime("%I", x))
        mm = int(time.strftime("%M", x))
        tm.numbers(hh, mm, colon=True)
        time.sleep(1)
        if motion_sensor.value() == 1:
            tm.brightness(0)
            tm.numbers(00, 00, colon=False)
            return main_screen(events_today)
            
try:
    display.draw_text(180, 110,'Loading...', arcadepix, color565(255, 255, 0), landscape = True, rotate_180= True)
    gc.collect()
    connect()
    display.draw_text(140, 150,'finding weather data', arcadepix, color565(255, 255, 0), landscape = True, rotate_180= True)
    find_weather()
    display.draw_text(170, 110,'finding news...', arcadepix, color565(255, 255, 0), landscape = True, rotate_180= True)
    International_News()
    display.draw_text(160, 110,'found 1/2', arcadepix, color565(255, 255, 0), landscape = True, rotate_180= True)
    time.sleep(2)
    Canadian_News()
    display.draw_text(150, 110,'found 2/2', arcadepix, color565(255, 255, 0), landscape = True, rotate_180= True)
    ntptime.settime()
    gc.collect()
    display.draw_text(130, 160,'finding Calendar data', arcadepix, color565(255, 255, 0), landscape = True, rotate_180= True)
    get_event_details(calendar, api_key, config.TIMEZONE)
    display.clear()
    gc.collect()
    display.draw_text(180, 110,'begin', arcadepix, color565(255, 255, 0), landscape = True, rotate_180= True)
    print(events_today)
except MemoryError:
    print('resetting')
    machine.reset()
gc.collect()

tm.brightness(0)
tm.numbers(00, 00, colon=False)

main_screen(events_today)












