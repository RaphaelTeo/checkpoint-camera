import random
from datetime import datetime, timedelta
import schedule # !pip install schedule
#import pytz # standard package, else pip install pytz
import time
import os

import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageFont, ImageDraw # pip install Pillow

user_agent_list = [
'user agent 1',
'user agent 2',
'user agent 3',
'user agent 4',
'user agent 5',
'user agent 6',
]

token = 'enter Telegram token here'
userID = 'enter Telegram userID here'

dir = r'enter file directory here'
fontdir = dir + "/Roboto-Regular.ttf"
font = ImageFont.truetype(fontdir, 30)
position = (700, 0)
position_error = (900,540)
padding = 10
url_lta = "https://onemotoring.lta.gov.sg/content/onemotoring/home/driving/traffic_information/traffic-cameras/woodlands.html#trafficCameras"


def send_tele_msg(message, token, userID): #send_tele_msg('hi', token, userID)
        url = f'https://api.telegram.org/bot{token}/sendMessage'
        data = {'chat_id': userID, 'text': message}
        requests.post(url, data)
        print(f'Sent Telegram message: {message}')

def combine_images(columns, space, images):
    rows = 2
    width_max = 1920
    height_max = 1080
    background_width = width_max*columns + (space*columns)-space
    background_height = height_max*rows + (space*rows)-space
    background = Image.new('RGB', (background_width, background_height), (255, 255, 255))
    x = 0
    y = 0
    for i, image in enumerate(images):
        img = image
        x_offset = int((width_max-img.width)/2)
        y_offset = int((height_max-img.height)/2)
        background.paste(img, (x+x_offset, y+y_offset))
        x += width_max + space
        if (i+1) % columns == 0:
            y += height_max + space
            x = 0
    return background

def get_page_info():
    
    user_agent = random.choice(user_agent_list)
    page = requests.get(url_lta, headers={'User-Agent': user_agent}, timeout=(6.05, 14))
    print(page.status_code)
    soup = BeautifulSoup(page.content, 'html.parser')
    return soup 

def get_lta_img(each_card):
    title = each_card.find('div', attrs={'class': 'trf-desc'}).string
    timestamp = each_card.find('div', attrs={'class': 'timestamp'}).find('span', attrs={'class': 'left'}).string
    href = 'https:' + each_card.find('img', attrs={'alt': title})['src']

    img = Image.open(requests.get(href, stream = True).raw)
    draw = ImageDraw.Draw(img)
    timestamp_cut = ''.join(i+' ' for i in timestamp.split()[:4])
    text = title + '\n' + timestamp_cut
    left, top, right, bottom = draw.textbbox(position, text, font=font)
    draw.rectangle((left-padding, top-padding, right+padding, bottom+padding), fill="white")
    draw.text(position, text, font=font, fill="black", align="center")
    return img

def get_lta_img_error():
    error_text = 'ERROR' + '\n' 
    img = Image.new('RGB', (1920,1080))
    draw = ImageDraw.Draw(img)
    left, top, right, bottom = draw.textbbox(position_error, error_text, font=font)
    draw.rectangle((left-padding, top-padding, right+padding, bottom+padding), fill="white")
    draw.text(position_error, error_text, font=font, fill="black", align="center")
    return img

def get_images(all_cards):
    attempt_no_get_cards = 0
    while True:
        all_images = []
        try:  
            if attempt_no_get_cards <= 2:
                for each_card in all_cards:
                    img = get_lta_img(each_card)
                    all_images.append(img)

            else: # we take what we can get
                #send_tele_msg(f"Card scraping error, using whatever cards we can get", token, userID)
                for each_card in all_cards:
                    try:
                        img = get_lta_img(each_card)
                    except:
                        img = get_lta_img_error()
                    finally:
                        all_images.append(img)
                    
            return all_images # at this point, exit the loop and return the images with/without error

        except:
            #send_tele_msg(f"Error in getting cards, attempt {attempt_no_get_cards}", token, userID)
            attempt_no_get_cards += 1
            time.sleep(random.randint(6,11))
            continue # go on to next try

def main_sequence():

    for attempt_no_main in range(0,4):

        if attempt_no_main == 3:
            #send_tele_msg(f"Unresolvable Error in main function, attempt {attempt_no_main}. Skipping this timestamp.", token, userID)
            break

        else:
            try:
                time.sleep(random.randint(0,4))
                run_timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                date = datetime.now().strftime("%Y-%m-%d")

                soup = get_page_info()
                all_cards = soup.find_all('div', attrs={'class': 'card'})
                all_images = get_images(all_cards)
            
                combined_image = combine_images(2, 0, all_images)
                # Create folder if needed and save image
                if os.path.exists(dir + '/' + date) == False:
                    os.mkdir(dir + '/' + date)
                
                filename = dir + '/' + date + '/' + run_timestamp +'.jpeg'
                combined_image.thumbnail((1920,1080), Image.LANCZOS)
                combined_image.save(filename, quality=60)
                break

            except:
                #send_tele_msg(f"Error: in main function, current attempt {attempt_no_main}", token, userID)
                attempt_no_main += 1
                pass

# MAIN

schedule.every().minute.at(":XX").do(main_sequence)
schedule.every().day.at("XX:XX").do(send_tele_msg, 'Script still running', token, userID)

while True:
    try:
        schedule.run_pending()
        time.sleep(1)

    except:
        send_tele_msg("Error: Outermost function with scheduler, script terminated", token, userID)
        continue