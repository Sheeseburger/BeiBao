import requests
import numpy as np
import cv2
import random
import string
import pathlib
import os
from PIL import Image
from colorthief import ColorThief
from flask import redirect, session
from functools import wraps
from cs50 import SQL
from datetime import datetime

db = SQL("sqlite:///wardrobe.db")

ALLOWED_EXTENSIONS = {'.png', '.jpg', '.jpeg'}


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def allowed_file(filename):

    file_extension = pathlib.Path(filename).suffix

    if file_extension in ALLOWED_EXTENSIONS:
        return 1
    else:
        return 0

def random_string(letter_count, digit_count):
    str1 = ''.join((random.choice(string.ascii_letters) for x in range(letter_count)))
    str1 += ''.join((random.choice(string.digits) for x in range(digit_count)))
    sam_list = list(str1) # it converts the string to list.
    random.shuffle(sam_list) # It uses a random.shuffle() function to shuffle the string.
    final_string = ''.join(sam_list)
    return final_string

def new_image_size(orig_width, orig_height, smallest_side_size):
    new_w = orig_width
    new_h = orig_height
    if smallest_side_size <= 0:
        return new_w, new_h

    if orig_width > orig_height:
        new_h = smallest_side_size
        new_w = round(orig_width * new_h / orig_height)
    else:
        new_w = smallest_side_size
        new_h = round(orig_height * new_w / orig_width)

    return new_w, new_h


def removeBg(img):

    smallestSideSize = 500
    # real would be thicker because of masking process
    mainRectSize = .04
    fgSize = .10
    #img = cv2.imread(path)
    img = np.asarray(img)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    height, width = img.shape[:2]
    new_w, new_h = new_image_size(width, height, smallestSideSize)

    # resize image to lower resources usage
    # if you need masked image in original size, do not resize it
    img_small = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)

    # create mask tpl
    mask = np.zeros(img_small.shape[:2], np.uint8)

    # create BG rect
    bg_w = round(new_w * mainRectSize)
    bg_h = round(new_h * mainRectSize)
    bg_rect = (bg_w, bg_h, new_w - bg_w, new_h - bg_h)

    # create FG rect
    fg_w = round(new_w * (1 - fgSize) / 2)
    fg_h = round(new_h * (1 - fgSize) / 2)
    fg_rect = (fg_w, fg_h, new_w - fg_w, new_h - fg_h)

    # color: 0 - bg, 1 - fg, 2 - probable bg, 3 - probable fg
    cv2.rectangle(mask, fg_rect[:2], fg_rect[2:4], color=cv2.GC_FGD, thickness=-1)

    bgdModel1 = np.zeros((1, 65), np.float64)
    fgdModel1 = np.zeros((1, 65), np.float64)

    cv2.grabCut(img_small, mask, bg_rect, bgdModel1, fgdModel1, 3, cv2.GC_INIT_WITH_RECT) # first launch

    cv2.rectangle(mask, bg_rect[:2], bg_rect[2:4], color=cv2.GC_PR_BGD, thickness=bg_w * 3)

    cv2.grabCut(img_small, mask, bg_rect, bgdModel1, fgdModel1, 10, cv2.GC_INIT_WITH_MASK) # repeat for more accurace

    # mask to remove background
    mask_result = np.where((mask == 1) + (mask == 3), 255, 0).astype('uint8') # making decision where 1 is FG and 3 is PROBABLY FG

    # apply mask to image
    masked = cv2.bitwise_and(img_small, img_small, mask=mask_result)
    masked[mask_result < 2] = [38, 38, 38]  # change blue bg to gray
    masked = cv2.cvtColor(masked, cv2.COLOR_RGB2BGR)
    return masked

def color(path):
    color_thief = ColorThief(path)
    # get the dominant color
    dominant_color = color_thief.get_color(quality=1)
    a = ('{:X}{:X}{:X}').format(dominant_color[0],dominant_color[1],dominant_color[2])
    return a

def random_name():
    now = datetime.now()
    dt_string = now.strftime("%d-%m-%Y_%H-%M-%S")


    size = random.randint(1,5) # make bigger range for bigger str
    filename = str(random_string(size,5-size)) + ".png" # 1 arg is for letter,2 arg is for numeric
    dt_string = dt_string + filename
    return dt_string

def get_temperature(city_id):
    # base URL
    BASE_URL = "https://api.openweathermap.org/data/2.5/weather?"
    # City Name
    CITY = city_id
    # API key
    API_KEY = os.environ.get("WEATHER_API_KEY")
    # upadting the URL
    URL = BASE_URL + "q=" + str(CITY) + "&appid=" + API_KEY
    # HTTP request
    response = requests.get(URL)
    # checking the status code of the request
    if response.status_code == 200:
        # getting data in the json format
        data = response.json()
        # getting the main dict block
        main = data['main']
        # getting temperature
        weather = data['weather'][0]['main']
        temperature = main['temp']
        answ = {'temp':round(temperature - 273.15),'weather':weather}
        return answ
    else:
    # showing the error message
        return 0

def get_look(temperature_dict,rows_up):
    temperature = int(temperature_dict['temp'])
    weather = temperature_dict['weather']

    tshirt = []
    jacket = []
    overshirt =[]
    shorts = []
    pants = []
    full = []
    final_res = []

    warm_up = ['T-shirt','Top']
    warm_down = ['Shorts','Skirt']
    for row in rows_up:
        if row['name'] in warm_up:
            tshirt.append(row)
        elif row['type'] == 'UnderJacket' and row['name'] not in warm_up:
            overshirt.append(row)
        elif row['type'] == 'Jacket':
            jacket.append(row)
        elif row['name'] in warm_down:
            shorts.append(row)
        elif row['type'] == 'Pants' and row['name'] not in warm_down:
            pants.append(row)
        elif row['type'] == 'Full':
            full.append(row)

    if temperature > random.randint(17,21):
        if 0.4 > random.random() and full:
            final_res.append(full[random.randint(0,len(full)-1)])
            return final_res


    if tshirt:
        final_res.append(tshirt[random.randint(0,len(tshirt)-1)])#choose tshirt

    if temperature in range(random.randint(17,21),25):
        if 0.15 > random.random() and overshirt: # if weather is hot but dont enought 15% to get extra item
            final_res.insert(0,overshirt[random.randint(0,len(overshirt)-1)])
    elif temperature in range(15,random.randint(18,21)) and overshirt:
        if 0.4 > random.random():
            final_res.insert(0,overshirt[random.randint(0,len(overshirt)-1)])
    elif overshirt and temperature < 15:
        final_res.insert(0,overshirt[random.randint(0,len(overshirt)-1)])

    # now choose pants
    if temperature > random.randint(18,21):
        if 0.8 > random.random() and shorts:
            final_res.append(shorts[random.randint(0,len(shorts)-1)])
        elif pants:
            final_res.append(pants[random.randint(0,len(pants)-1)])
    elif temperature in range(15,18):
        if 0.55 > random.random() and pants:
            final_res.append(pants[random.randint(0,len(pants)-1)])
        elif shorts:
            final_res.append(shorts[random.randint(0,len(shorts)-1)])
    else:
        if pants:
            final_res.append(pants[random.randint(0,len(pants)-1)])
        elif shorts:
            final_res.append(shorts[random.randint(0,len(shorts)-1)])

    if (weather == 'Rain' and temperature < 18) or temperature < 10 :
        if jacket:
            final_res = [jacket[random.randint(0,len(jacket)-1)]] + final_res

    return final_res

def item_check(item):
    rows = db.execute('SELECT name FROM Item')
    check = 0
    item = item.capitalize()

    for row in rows:
        if item == row['name']:
            check +=1
    return check

def outfit_add(rows):
    db.execute('INSERT INTO Users_Outfits (user_id,temperature) VALUES (?,?)',session['user_id'],get_temperature(session['city_name'])["temp"]) # insert and than get outfit id
    id = db.execute('SELECT id FROM Users_Outfits WHERE user_id=? ORDER BY ID DESC LIMIT 1',session['user_id'])[0]['id']
    for row in rows:
         db.execute('INSERT INTO Outfits_Item (outfits_id,item_id) VALUES(?,?)',id,row)

def filter_rows(rows):
    pants = []
    underjacket = []
    jacket = []
    for row in rows:
        if row['type'] == 'Pants':
            pants.append(row)
        elif row['type'] == 'UnderJacket':
            underjacket.append(row)
        else:
            jacket.append(row)
    return jacket,underjacket,pants
