# spareroom-scraper
Filter SpareRoom listings and calculate commute times with CityMapper API to allow more comprehensive filtering. Outputs a .csv and can be re-run daily.

This code is pretty horrible as it was written in a mad rush to find an apartment - it was extremely useful as it narrowed SpareRoom's >1000 suggested Apartments to <20. Use with trepidation.

The barebones of the scraper were stolen and bastardised from https://github.com/davidmoremad/find-room-in-london

# Usage
1. Get an API key for citymapper from [this link](https://docs.external.citymapper.com/api/)
2. Copy and paste the API key into `main.py` along with a search link for your city of choice. 
3. Run the script and apply filters on the resulting spreadsheet as you see fit. For this I recommend google sheets.

# Example Output
Fields:
`url	id	title	desc	Type	Area	Postcode	Nearest station	location_coords	cycle_time	transit_time	Available	Minimum term	Maximum term	room_0_price	room_0_type	Deposit	room_1_price	room_1_type	Deposit(room 1)	room_2_price	room_2_type	Deposit(room 2)	rBills included?	Furnishings	Parking	Garage	Garden/terrace	Balcony/patio	Disabled access	Living room	Broadband included	Flatmates	Total rooms	Age	Smoker?	Any pets?	Language	Nationality	Occupation	Gender	Couples ok?	Smoking ok?	Pets ok?	References?	Min age	Ages	Interests	Max age	Housemates	Orientation	University	Vegetarian	date_scraped`

And a filtered google sheet:
![image](https://user-images.githubusercontent.com/14139469/235493682-db45832a-e911-4813-bbc6-bf55341f4181.png)

