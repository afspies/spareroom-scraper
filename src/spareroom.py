import requests
import re
from .distance_calcaulation import get_travel_information
from bs4 import BeautifulSoup
import pandas as pd
import datetime

class SpareRoom:
    DOMAIN = 'https://www.spareroom.co.uk'
    URL_ROOMS = DOMAIN + '/flatshare'
    URL_SEARCH = URL_ROOMS 

    def __init__(self, search_url, workplace_coords, citymapper_api_key, min_price_pw=180, max_price_pw=290, entries_to_scrape=30):
        self.workplace_coords = workplace_coords
        self.citymapper_api_key = citymapper_api_key
        self.URL_SEARCH = self.URL_ROOMS + search_url
        self.entries_to_scrape = entries_to_scrape

        r = requests.get(self.URL_SEARCH % (min_price_pw, max_price_pw))
        s = BeautifulSoup(r.content, 'lxml')
        self.url = r.url + 'offset=%i'
        self.pages = int(int(s.find("p", {"class": "navcurrent"}).findAll("strong")[1].string[:-1]) / 10)

    def _get_soup(self, url):
        '''
        Make request & return soup
        '''
        r = requests.get(url, allow_redirects=False)
        if r.status_code == 200:
            return BeautifulSoup(r.content, 'lxml')
        elif r.status_code == 301:
            print('Finalizado')
            exit(0)
        else:
            print('[X] Response %s .Something went wrong.' % r.status_code)
            exit(1)

    def _get_rooms_info(self, rooms_soup, previous_rooms=None):
        '''
        Iterate rooms & return object list
        '''
        rooms = list()
        try:
            for room in rooms_soup.find_all('article'):
                add_room = True
                if previous_rooms is not None and not previous_rooms.empty:
                    room_id = int(room.find("a")['href'].split("flatshare_id=")[1].split("&")[0])
                    add_room = room_id not in previous_rooms['id'].values

                if add_room:
                    room = Room(room, self.DOMAIN, self.workplace_coords, self.citymapper_api_key)
                    if room is not None:
                        rooms.append(room)
                else:
                    print('[X] Room already exists')
        except Exception as e:
            print("Catch exception: ", e)
        return rooms

    def get_rooms(self, previous_rooms=None):
        '''
        Main method
        '''
        rooms = list()

        for i in range(0, self.entries_to_scrape, 10):
            print('[ ] Visited pages:%i/%i \tRooms: %i' % (i+1, i+10, len(rooms)))
            soup = self._get_soup(self.url % i)
            rooms.extend(self._get_rooms_info(soup, previous_rooms=previous_rooms))

        return rooms



class Room:
    """
    Room Object
     * extracts listing info from the listing's page (not the search results page)
     * calculates commute times to workplace

    Contains:
        url
        title
        description
        features (minimum term, maximum term, deposit, bills included, furnishings, parking, garage, garden
                  balcony, disabled access, living room, broadband, housemates. total rooms, ages, smoker, pets,
                  language, occupation, gender, couples ok, smoking ok, pets ok, references, min age, max age)
        gps_location
        commute distance to workplace (by public transport and cycling)
        
    """
    def __init__(self, room_soup, domain, workplace_coords, citymapper_api_key):
        # Get listing page
        self.url = str(domain + room_soup.find("a")['href'])
        self.id = int(self.url.split("flatshare_id=")[1].split("&")[0])
        room_soup = BeautifulSoup(requests.get(self.url).content, 'lxml')

        # Populate basics from the search results page
        try:
            header = room_soup.find("div", {"id": "listing_heading"})
            self.title = str(header.h1.text.strip()) if header.h1 else None
        except AttributeError:
            print('[X] Error parsing listing page - probably not live')
            return
        self.desc = str(room_soup.find("p", {"class": "detaildesc"}).text.strip().replace('\r\n', ' '))

        key_features = self._get_key_features(room_soup)
        [setattr(self, feature, key_features[feature]) for feature in key_features]

        pm_prices = self._get_pm_price(room_soup)
        for i, room in enumerate(pm_prices):
            price, type = room['price'], room['type']
            setattr(self, f'room_{i}_price', price)
            setattr(self, f'room_{i}_type', type)

        # Calculate commute times
        self.location_coords = self._get_location_coords(room_soup)
        commute_times = get_travel_information(self.location_coords, api_key=citymapper_api_key, work_coords=workplace_coords)
        self.cycle_time = commute_times['bike_time_minutes']
        self.transit_time = commute_times['transit_time_minutes']

        features = self._get_features(room_soup)
        [setattr(self, feature, features[feature]) for feature in features]

        # Todays date
        self.date_scraped = datetime.datetime.now().strftime("%d-%m-%Y")


    def __str__(self):
        return str(self.__dict__)

    def _get_pm_price(self, room_soup):
        rooms = []
        room_price_lists = room_soup.find('ul', class_='room-list')

        for li in room_price_lists.find_all('li'):
            # get price from strong class="room-list__price"
            price = li.find('strong', {"class": "room-list__price"}).text.strip()
            price, interval = price.split(" ")
            price = price.replace("£", "")
            if interval == "pw":
                price = int(price)*(52/12)
            type = li.find('small').text.strip().replace('(', '').replace(')', '')
            rooms.append({'price': price, 'type': type})
        return rooms

    def _get_key_features(self, room_soup):
        feature_list = room_soup.find('ul', class_='key-features')
        features = {'Type': None, 'Area': None, 'Postcode': None, 'Nearest station': None}
        for i, li in enumerate(feature_list.find_all('li')):
            # check if there is a sublist, and if so only take the first element
            text = li.text.strip()
            if i == 2:
                text = text.split(" ")[0]
            elif i == 3:
                text = text.split("\n")[0]

            features[list(features.keys())[i]] = li.text.strip()
        return features

    def _get_features(self, room_soup):
        feature_list = room_soup.findAll('dl', class_='feature-list')
        features = {}
        for feature_list in feature_list:
            for dt, dd in zip(feature_list.find_all('dt'), feature_list.find_all('dd')):
                key = dt.text.replace('\n', ' ').replace('#', '').strip().capitalize()
                features[key] = dd.text.strip()
        return features

    def _get_location_coords(self, room_soup):
        script_text = room_soup.head.findAll("script")
        for script in script_text:
            script_text = script.text
            if "_sr.page" in script_text:
                location_idx = script_text.find("location")
                if location_idx == -1:
                    continue
                location = script_text[location_idx:location_idx+100]
                location = location.split('{')[1].split('}')[0]
                location = location.split(',')[:-1]
                location = [float(l.split(':')[1].strip().replace('"', '')) for l in location]
                # latitude, longitude
                location = (location[0], location[1])
                return location


def read_existing_rooms_from_spreadsheet(file_path):
    try:
        df = pd.read_csv(file_path)
    except (FileNotFoundError, pd.errors.EmptyDataError):
        print("Creating new spreadsheet for rooms.")
        df = pd.DataFrame()
    return df


def append_new_rooms_to_spreadsheet(df, new_rooms, file_path):
    new_df = pd.DataFrame([room.__dict__ for room in new_rooms])
    combined_df = pd.concat([df, new_df], ignore_index=True)

    # Reorder columns
    def reorder_columns(columns):
        room_columns = [col for col in columns if col.startswith("room_")]
        deposit_columns = [col for col in columns if col.startswith("Deposit")]
        non_room_columns = [col for col in columns if (col not in room_columns + deposit_columns)]

        room_and_deposit = [room_columns[i*2:i*2+2] + [deposit_columns[i]] for i in range(len(deposit_columns))]
        # flatten list
        room_and_deposit = [item for sublist in room_and_deposit for item in sublist]

        reordered_columns = []
        for col in non_room_columns:
            reordered_columns.append(col)
            if col.startswith("Maximum term"):
                reordered_columns.extend(room_and_deposit)
        return reordered_columns

    reordered_columns = reorder_columns(combined_df.columns)
    combined_df = combined_df[reordered_columns]

    combined_df.to_csv(file_path, index=False)

# def append_new_rooms_to_spreadsheet(df, new_rooms, file_path):
#     new_df = pd.DataFrame([room.__dict__ for room in new_rooms])
#     combined_df = pd.concat([df, new_df], ignore_index=True)
#     combined_df.to_csv(file_path, index=False)