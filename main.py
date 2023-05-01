import csv
from src.spareroom import SpareRoom, read_existing_rooms_from_spreadsheet, append_new_rooms_to_spreadsheet
# Base of scraper is taken from https://github.com/davidmoremad/find-room-in-london with significant modifications to extract more info

# -- Configuration --
# Set file path for the spreadsheet
filename = 'spareroom_listing.csv'

#! Note that %i is used for min and max rent to be substituted with the values below
search_url = '/search.pl?nmsq_mode=normal&action=search&max_per_page=&flatshare_type=offered&search=London+Zone+1+to+2&min_rent=%i&max_rent=%i&per=pw&available_search=N&day_avail=02&mon_avail=05&year_avail=2023&min_term=0&max_term=0&days_of_wk_available=7+days+a+week&showme_rooms=Y'
min_rent_pw = 180
max_rent_pw = 290
WORK_COORDS = (51.49887,-0.17897) # (lat, long) Imperial College London coordinates
API_KEY = "XXXXXXXXXXXXXXXXXXXXXXXX" # CityMapper API key
entries_to_scrape = 30 # Number of entries to scrape - you have 5000 free CityMapper API calls per month
# -----------------------------------------------------

def main():
    # Read the existing rooms from the spreadsheet
    existing_rooms_df = read_existing_rooms_from_spreadsheet(filename)

    # Instantiate SpareRoom and get new rooms
    spare_room = SpareRoom(search_url, WORK_COORDS, API_KEY, min_rent_pw, max_rent_pw, entries_to_scrape)
    new_rooms = spare_room.get_rooms(previous_rooms=existing_rooms_df)


    # Filter out rooms that already exist in the spreadsheet
    filtered_new_rooms = []
    for room in new_rooms:
        if existing_rooms_df.empty:
            filtered_new_rooms.append(room)
        elif room.id not in existing_rooms_df['id'].values:
            filtered_new_rooms.append(room)

    # Append new rooms to the spreadsheet
    append_new_rooms_to_spreadsheet(existing_rooms_df, filtered_new_rooms, filename)
    print(f'[+] Resuls saved: ./{filename}')




if __name__ == "__main__":
    main()