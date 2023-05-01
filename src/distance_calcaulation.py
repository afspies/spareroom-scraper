import http.client
from urllib.parse import urlencode
import json



def get_travel_information(start_coords, api_key=None, work_coords=(51.4983, 0.1743)):
    if start_coords is None or api_key is None:
        return None
    conn = http.client.HTTPSConnection("api.external.citymapper.com")

    headers = {"Citymapper-Partner-Key": api_key}

    payload = {
        "start": f"{start_coords[0]},{start_coords[1]}",
        "end": f"{work_coords[0]},{work_coords[1]}",
        "traveltime_types": "bike,transit",
    }

    endpoint = f"/api/1/traveltimes?{urlencode(payload, doseq=True)}"
    conn.request("GET", endpoint, headers=headers)

    res = conn.getresponse()
    data = res.read()
    json_data = json.loads(data.decode("utf-8"))

    return json_data
