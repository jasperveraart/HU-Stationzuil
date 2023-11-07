from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import database

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/stationinfo/{city}")
def read_city(city: str, ShowFacilities: bool = True, GlobalMessages: bool = True):
    station_list = database.get_stations()

    if GlobalMessages == True:
        messages = database.get_global_messages()
    else:
        messages = database.get_station_messages(city)

    found = False
    for station in station_list:
        city_station = station.get("city")
        if city_station == city:
            found = True

            if ShowFacilities == True:
                return {
                    "Information": {
                        "country": station.get("country"),
                        "city": station.get("city"),
                        "name": station.get("name")
                    },
                    "Facilities": {
                        "toilet": station.get("toilet"),
                        "ov_bike": station.get("ov_bike"),
                        "elevator": station.get("elevator"),
                        "park_and_ride": station.get("park_and_ride")
                     },
                    "GlobalMessages": GlobalMessages,
                    "Messages": messages
                }
            else:
                return {
                    "Information": {
                        "country": station.get("country"),
                        "city": station.get("city"),
                    },
                    "GlobalMessages": GlobalMessages,
                    "Messages": messages
                }

    if found == False:
        return {
            "Error": "404",
            "msg": "No city found with selected name"
        }