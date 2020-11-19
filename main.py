import requests
import os, sys, time
from datetime import datetime
import sqlite3
import shutil
from config import DB_PATH, SAVED_DIR, ROOT_DIR, HOST_OS

'''
// TODO
-> Add Support for Linux
-> Add Agent Option
'''

# -- Dictionary Containing the color ranges in HSL --
colors_dict = {
    'Green': {
        'min': [30, 20, 20],
        'max': [85, 255, 255]
    },
    'Red': {
        'min': [0, 20, 20],
        'max': [15, 255, 255]
    },
    'Yellow': {
        'min': [20, 20, 20],
        'max': [35, 255, 255]
    },
    'Cyan': {
        'min': [80, 20, 20],
        'max': [95, 255, 255]
    },
    'Blue': {
        'min': [95, 20, 20],
        'max': [135, 255, 255]
    },
    'Black': {
        'min': [0, 0, 0],
        'max': [85, 85, 85]
    }
}
# -- Dictonary Containing the color ranges in HSL --

current_wallpaper = os.path.join(ROOT_DIR, "current_wallpaper.txt")
image_name = f"Desktop_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpeg"

url = "https://source.unsplash.com/random/2560x1600"

# Terminal Colors
class TermStyle:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def error_handler(message):
    print("")
    print(TermStyle.FAIL + f"[x] Error - {message}" + TermStyle.ENDC)
    sys.exit()

def grab_new_wallpaper(url, image_name):
    response = requests.get(url)
    with open(image_name, 'wb') as image:
        image.write(response.content)   

def set_new_wallpaper(image_name, current_wallpaper):
    new_wallpaper = open(current_wallpaper, "w+")
    new_wallpaper.write(image_name)
    if HOST_OS == 'Darwin':
        # Apple
        from appscript import app, mactypes
        app('Finder').desktop_picture.set(mactypes.File(os.path.join(ROOT_DIR, image_name)))
    elif HOST_OS == 'Windows':
        # Windows
        import ctypes
        ctypes.windll.user32.SystemParametersInfoW(20, 0, os.path.join(ROOT_DIR, image_name) , 3)
    else:
        error_handler("Unsupported OS")

    new_wallpaper.close()
    print("")
    print(TermStyle.BOLD + TermStyle.OKGREEN + f"[+] New Wallpaper Set - {image_name}" + TermStyle.ENDC)

def clean_old(current_wallpaper):
    current_image = open(current_wallpaper, "r")
    image_name = current_image.readline()
    os.remove(os.path.join(ROOT_DIR, image_name))
    current_image.close()
    os.remove(current_wallpaper)
    if os.path.isfile(current_wallpaper):
        error_handler(f"Couldn't Remove {current_wallpaper}")
    

def color_check(colors_dict, color, image_name):
    import cv2
    img = cv2.imread(image_name)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv,
    (colors_dict[color]['min'][0], colors_dict[color]['min'][1], colors_dict[color]['min'][2]), 
    (colors_dict[color]['max'][0], colors_dict[color]['max'][1], colors_dict[color]['max'][2]) 
    )
    percentage = (mask>0).mean()
    return percentage

def save_image(current_wallpaper):
    current_image = open(current_wallpaper, "r")
    image_name = current_image.readline()

    # -- Creating Database/Tables --
    database = DB_PATH
    table = "Images"
    table_content = ["imageID", "imageName"] 

    new_table = f"""
        CREATE TABLE IF NOT EXISTS {table}(
            {table_content[0]} INTEGER PRIMARY KEY,
            {table_content[1]} VARCHAR(20) NOT NULL
        )
    """

    with sqlite3.connect(database) as db:
        cursor = db.cursor()

    cursor.execute(new_table)
    # -- Creating Database/Tables --

    find_image = (f"SELECT * FROM Images WHERE imageName = ?")
    cursor.execute(find_image, [(image_name)])
    results = cursor.fetchall()

    if results:
        print("")
        return print(TermStyle.WARNING + "[!] Image Already Saved" + TermStyle.ENDC)
    else:
        print("")
        print(TermStyle.BOLD + TermStyle.OKGREEN + "[+] Saving Image...")
        cursor.execute(f"""
            INSERT INTO Images(imageName)
            VALUES("{image_name}")
        """)
        db.commit()
        find_image = (f"SELECT * FROM Images WHERE imageName = ?")
        cursor.execute(find_image,[(image_name)])
        results = cursor.fetchall()

        # -- Checking if the entry exist -- 
        if results:
            # -- Copying Image --
            saved_file = SAVED_DIR
            shutil.copy(os.path.join(ROOT_DIR, image_name), saved_file)
            print("")
            return print(TermStyle.BOLD + TermStyle.OKGREEN + "[+] Image Saved" + TermStyle.ENDC)
        else:
            error_handler("Couldn't Add Image to the Database")

def view_saved(current_wallpaper):
    database = DB_PATH
    if os.path.isfile(database):

        with sqlite3.connect(database) as db:
            cursor = db.cursor()

        view_items = ("SELECT * FROM Images")
        cursor.execute(view_items)
        results = cursor.fetchall()
        
        if results:
            print(chr(27) + "[2J")
            print(TermStyle.BOLD + TermStyle.HEADER + """ 
  ---> Saved Wallpapers <---
ID   -   imageName     """ + TermStyle.ENDC)
            while True:
                for image in results:
                    print(TermStyle.BOLD + f"{image[0]} - {image[1]}" + TermStyle.ENDC)

                user_input = int(input("imageID: "))

                find_image = ("SELECT * FROM Images WHERE imageID = ?")
                cursor.execute(find_image,[(user_input)])
                results = cursor.fetchall()

                if results:
                    find_image = ("SELECT * FROM Images WHERE imageID = ?")
                    cursor.execute(find_image,[(user_input)])
                    for image in results:
                        image_name = image[1]
                    clean_old(current_wallpaper)
                    saved_image = os.path.join(SAVED_DIR, f"{image_name}")
                    shutil.copy(saved_image, ".")
                    set_new_wallpaper(image_name, current_wallpaper)
                    break
                else:
                    print("")
                    print(TermStyle.BOLD + TermStyle.WARNING + f"[!] Entry Doesn't Exist")
    else:
        print("")
        return print(TermStyle.BOLD + TermStyle.WARNING + "[!] No Images Have Been Saved" + TermStyle.ENDC)

def delete_saved():
    database = DB_PATH
    if os.path.isfile(database):

        with sqlite3.connect(database) as db:
            cursor = db.cursor()

        view_item = ("SELECT * FROM Images")
        cursor.execute(view_item)
        results = cursor.fetchall()

        if results:
            print(chr(27) + "[2J")
            print(TermStyle.BOLD + TermStyle.HEADER + """ 
  ---> Saved Wallpapers <---
ID   -   imageName     """ + TermStyle.ENDC)
            
            while True:
                for image in results:
                    print(TermStyle.BOLD + f"{image[0]} - {image[1]}" + TermStyle.ENDC)

                user_input = int(input("imageID: "))
                find_image = (f"SELECT * FROM Images WHERE imageID = ?")
                cursor.execute(find_image,[(user_input)])
                results = cursor.fetchall()

                if results:
                    delete_query = """DELETE from Images where imageID = ?"""
                    cursor.execute(delete_query,[(image[0])])
                    db.commit()
                    if os.path.isfile(os.path.join(SAVED_DIR, f"{image[1]}")):
                        os.remove(os.path.join(SAVED_DIR, f"{image[1]}"))
                        if os.path.isfile(os.path.join(SAVED_DIR, f"database/images/{image[1]}")):
                            error_handler(f"Couldn't Remove {image[1]}")
                
                print("")
                return print(TermStyle.BOLD + TermStyle.WARNING +f"[!] Image Removed" + TermStyle.ENDC)
                break


    else:
        print("")
        print(TermStyle.BOLD + TermStyle.WARNING + f"[!] Entry Doesn't Exist")


if __name__ == '__main__':
    try:
        try:
            print("")
            print(TermStyle.HEADER + """
 ______                     _                _  _  _         _   _  
(_____ \                   | |              (_)(_)(_)       | | | | 
 _____) ) _____  ____    __| |  ___   ____   _  _  _  _____ | | | | 
|  __  / (____ ||  _ \  / _  | / _ \ |    \ | || || |(____ || | | | 
| |  \ \ / ___ || | | |( (_| || |_| || | | || || || |/ ___ || | | | 
|_|   |_|\_____||_| |_| \____| \___/ |_|_|_| \_____/ \_____| \_) \_)

                    """)
            print(TermStyle.OKGREEN + TermStyle.BOLD + "Last Update - 19/11/2020            By - MrSaintJCode" + TermStyle.ENDC)
            print("")
            print(TermStyle.BOLD + TermStyle.WARNING + "---> CTRL-C TO EXIT <---" + TermStyle.ENDC)
            user_input = int(input(TermStyle.BOLD + "What would you like to do:\n1) New Wallpaper\n2) New Wallpaper - Color Select\n3) Save Current Wallpaper\n4) View Saved Wallpapers\n5) Delete a Saved Wallpaper\nOption: "))

            # User Option - Grab Random Wallpaper
            if user_input == 1:
                if os.path.isfile(current_wallpaper):
                    clean_old(current_wallpaper)

                print("")
                print(TermStyle.OKGREEN + TermStyle.BOLD + "[+] Grabbing Wallpaper...Please Wait" + TermStyle.ENDC)
                grab_new_wallpaper(url, image_name)
                set_new_wallpaper(image_name, current_wallpaper)

            # User Option - Grab Wallpaper w/ Color Selection
            elif user_input == 2:
                percentage = 0
                option_num = 1
                option_arr = []
                print(chr(27) + "[2J")
                print(TermStyle.BOLD + TermStyle.WARNING + "Note: This will take some time to find an image depending on the color." + TermStyle.ENDC)
                print("")
                print(TermStyle.BOLD + TermStyle.WARNING + "---> CTRL-C TO EXIT <---" + TermStyle.ENDC)
                print(TermStyle.BOLD + "Color Options:")
                for color in colors_dict:
                    print(TermStyle.BOLD + f"{option_num}) {color}")
                    option_arr.append(color)
                    option_num = option_num + 1
                user_input = int(input(TermStyle.BOLD + "Option: "))

                selection = user_input - 1
                print("")
                print(TermStyle.OKGREEN + TermStyle.BOLD + "[+] Grabbing Wallpaper...Please Wait" + TermStyle.ENDC)

                # -- Looping to find the color profile --
                while percentage < 0.30:
                    if os.path.isfile(current_wallpaper):
                        clean_old(current_wallpaper)
                        grab_new_wallpaper(url, image_name)
                        percentage = color_check(colors_dict, option_arr[selection], image_name)
                    else:
                        grab_new_wallpaper(url, image_name)
                        percentage = color_check(colors_dict, option_arr[selection], image_name) 
                    time.sleep(1)
                set_new_wallpaper(image_name, current_wallpaper)

            # User Option - Save Wallpaper to the Database
            elif user_input == 3:
                save_image(current_wallpaper)

            # User Option - View Saved Wallpapers in the Database
            elif user_input == 4:
                view_saved(current_wallpaper)

            # User Option - Delete a Saved Wallpaper in the Database
            elif user_input == 5:
                delete_saved()

            # User Option - Invalid
            else:
                error_handler("Invalid Option")

        except KeyboardInterrupt:
            print("")
            print(TermStyle.OKBLUE + "Exiting..." + TermStyle.ENDC)
    except (ValueError, OSError, IndexError) as reason:
        error_handler(reason)