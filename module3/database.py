import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def execute(query):
    """
    Execute a SQL query to the database
    :param query: SQL Statement
    :return: output of query
    """
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        port=os.getenv("DB_PORT")
    )

    cursor = conn.cursor()
    cursor.execute(query)

    output = cursor.fetchall()
    conn.close()

    return output


def get_stations():
    """
    Get a list of stations with facilities

    format:
    city: Amsterdam
    country: NL
    ov_bike = True
    elevator: True
    toilet = True
    park_and_ride = True


    :return: stations[{"city": "Amsterdam", "country": "NL", "ov_bike": True, "elevator": True, "toilet": True, "park_and_ride": True}, etc.]
    """

    reply = execute(("select * from station_service"))
    station_list = []
    for station in reply:
        station_info = {"city": station[0],
               "country": station[1],
               "ov_bike": station[2],
               "elevator": station[3],
               "toilet": station[4],
               "park_and_ride": station[5]}

        station_list.append(station_info)

    return station_list

def get_station_list():
    """
    Get a list of all station names
    :return: list=[Amsterdam, Utrecht]
    """
    reply = execute("select station_city from station_service")
    station_list = []

    for station in reply:
        station_list.append(station[0])

    return station_list

def get_global_messages():
    """
    Get last 5 messages with required information for station screen
    :return: [{message, city, name, facilities{ov_bike, elevator, toilet, park_and_ride}}]
    """
    reply = execute("""select messages.message, 
                        facility.ov_bike, 
                        facility.elevator, 
                        facility.toilet, 
                        facility.park_and_ride,
                        facility.station_city,
                        messages.name
                        from messages
                        join station_service as facility on messages.station = facility.station_city
                        order by messages.id desc 
                        limit 5 ;""")
    messages = []

    for message in reply:
        facilities = {
            "ov_bike": message[1],
            "elevator": message[2],
            "toilet": message[3],
            "park_and_ride": message[4]
        }

        message_data = {
            "message": message[0],
            "city": message[5],
            "name": message[6],
            "facilities": facilities
        }
        messages.append(message_data)

    return messages

def get_station_messages(city):
    """
    Get last 5 messages of city with required information for station screen
    :param city:
    :return: [{message, city, name, facilities{ov_bike, elevator, toilet, park_and_ride}}]
    """
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        port=os.getenv("DB_PORT")
    )

    query = """select messages.message, 
                        facility.ov_bike, 
                        facility.elevator, 
                        facility.toilet, 
                        facility.park_and_ride,
                        facility.station_city,
                        messages.name
                        from messages
                        join station_service as facility on messages.station = facility.station_city
                        where facility.station_city = %s
                        order by messages.id desc 
                        limit 5 ;"""
    data = city,

    cursor = conn.cursor()
    cursor.execute(query, data)

    output = cursor.fetchall()
    conn.close()

    messages = []

    for message in output:
        facilities = {
            "ov_bike": message[1],
            "elevator": message[2],
            "toilet": message[3],
            "park_and_ride": message[4]
        }

        message_data = {
            "message": message[0],
            "city": message[5],
            "name": message[6],
            "facilities": facilities
        }
        messages.append(message_data)

    return messages

def add_message(message:str, city:str, name="anoniem"):
    """
    Add message to the database
    :param message:
    :param city:
    :param name:
    :return: none
    """
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        port=os.getenv("DB_PORT")
    )

    query = "insert into messages(message, name, messagedate, station) values (%s, %s, now(), %s)"
    data = (message, name, city)

    cursor = conn.cursor()
    cursor.execute(query, data)

    conn.commit()

    conn.close()

