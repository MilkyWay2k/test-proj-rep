import requests
import sqlite3
from datetime import datetime, timedelta
from dateutil.parser import isoparse
import time
import threading

api_url = "https://iot.research.hamk.fi/api/v1/hamk/rooms?building-id=2"
api_key = "II6dsQDctGjWeoHgnT5wPjXlyJVmmUbvASnh2Zay"

headers = {
    "x-api-key": api_key
}

def create_table_if_not_exists(conn, room_name, building, floor):
    cursor = conn.cursor()
    table_name = f'room_{room_name.replace(" ", "_")}_{floor}'
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS "{table_name}" (
            room_id INTEGER,
            Timestamp TEXT,
            Temperature REAL,
            Humidity REAL,
            CO2 REAL,
            Light REAL,
            Motion REAL,
            VDD REAL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS all_rooms (
            room_id INTEGER PRIMARY KEY,
            room TEXT,
            street_address TEXT,
            building TEXT,
            floor INTEGER
        )
    ''')

    conn.commit()

def alter_timestamp_column_type(conn, room_name, building, floor):
    cursor = conn.cursor()
    table_name = f'room_{room_name.replace(" ", "_")}_{floor}'
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS "{table_name}_new" (
            room_id INTEGER,
            Timestamp DATETIME,
            Temperature REAL,
            Humidity REAL,
            CO2 REAL,
            Light REAL,
            Motion REAL,
            VDD REAL
        )
    ''')

    conn.commit()

def copy_data_to_new_table(conn, room_name, building, floor):
    cursor = conn.cursor()
    table_name = f'room_{room_name.replace(" ", "_")}_{floor}'
    cursor.execute(f'''
        INSERT INTO "{table_name}_new" (room_id, Timestamp, Temperature, Humidity, CO2, Light, Motion, VDD)
        SELECT room_id, DATETIME(Timestamp), Temperature, Humidity, CO2, Light, Motion, VDD
        FROM "{table_name}"
    ''')

    conn.commit()

def drop_old_table(conn, room_name, building, floor):
    cursor = conn.cursor()
    table_name = f'room_{room_name.replace(" ", "_")}_{floor}'
    cursor.execute(f'DROP TABLE IF EXISTS "{table_name}"')
    conn.commit()

def rename_new_table(conn, room_name, building, floor):
    cursor = conn.cursor()
    table_name = f'room_{room_name.replace(" ", "_")}_{floor}'
    cursor.execute(f'ALTER TABLE "{table_name}_new" RENAME TO "{table_name}"')
    conn.commit()

def insert_data_into_table(conn, room_name, room_id, building, floor, data):
    cursor = conn.cursor()
    table_name = f'room_{room_name.replace(" ", "_")}_{floor}'

    cursor.execute(f'DELETE FROM "{table_name}"')

    cursor.executemany(f'''
        INSERT INTO "{table_name}" (room_id, Timestamp, Temperature, Humidity, CO2, Light, Motion, VDD)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', [(room_id, *([0 if val is None else val for val in row])) for row in data])
    conn.commit()

def create_settings_table_if_not_exists(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            email TEXT,
            temperature_unit TEXT,
            min_temperature REAL,
            max_temperature REAL,
            min_humidity REAL,
            max_humidity REAL,
            min_co2 REAL,
            max_co2 REAL
        )
    ''')

    cursor.execute('SELECT COUNT(*) FROM settings')
    count = cursor.fetchone()[0]
    if count == 0:
        default_settings = (
            None,
            'Celsius',
            20.0,
            24.0,
            40.0,
            65.0,
            400.0,
            1000.0
        )
        cursor.execute('''
            INSERT INTO settings (email, temperature_unit, min_temperature, max_temperature, min_humidity, max_humidity, min_co2, max_co2)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', default_settings)

    conn.commit()

def update_data():
    while not stop_requested.is_set():
        try:
            response = requests.get(api_url, headers=headers, verify=False)

            if response.status_code == 200:
                data = response.json()

                conn = sqlite3.connect("Data_Waltikka.db")

                create_settings_table_if_not_exists(conn)

                for room_data in data:
                    room_name = room_data.get("room")
                    building = room_data.get("building")
                    floor = room_data.get("floor")

                    if room_name and building and floor:
                        create_table_if_not_exists(conn, room_name, building, floor)
                        alter_timestamp_column_type(conn, room_name, building, floor)
                        copy_data_to_new_table(conn, room_name, building, floor)
                        drop_old_table(conn, room_name, building, floor)
                        rename_new_table(conn, room_name, building, floor)

                        room_id = room_data.get("room-id")

                        if room_id:
                            end_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
                            start_time = (datetime.now() - timedelta(weeks=1.5)).strftime("%Y-%m-%dT%H:%M:%SZ")
                            fields = "temperature,humidity,co2,light,motion,vdd"
                            link = f"https://iot.research.hamk.fi/api/v1/hamk/rooms/tsdata?room-id={room_id}&startTime={start_time}&endTime={end_time}&fields={fields}"

                            response_data = requests.get(link, headers=headers, verify=False)
                            if response_data.status_code == 200:
                                data = response_data.json()

                                for result in data["results"]:
                                    for series in result["series"]:
                                        values = series["values"]
                                        values = [(datetime.fromisoformat(v[0]).strftime("%Y-%m-%d %H:%M:%S"), *v[1:]) for v in values]
                                        insert_data_into_table(conn, room_name, room_id, building, floor, values)

                            room_info = (
                                room_id,
                                room_name,
                                room_data.get("street-address"),
                                building,
                                floor
                            )
                            cursor = conn.cursor()
                            cursor.execute('''
                                INSERT OR REPLACE INTO all_rooms (room_id, room, street_address, building, floor)
                                VALUES (?, ?, ?, ?, ?)
                            ''', room_info)
                            conn.commit()

                conn.close()

                print("Data has been updated")

            else:
                print(f"Error: {response.status_code} - {response.text}")

        except Exception as e:
            print(f"Error happened: {str(e)}")

        time.sleep(10)

stop_requested = threading.Event()

update_thread = threading.Thread(target=update_data)
update_thread.start()

while True:
    user_input = input().strip().lower()
    if user_input == "stop":
        stop_requested.set()
        break

update_thread.join()

print("Program has been stopped.")
