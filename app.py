from flask import Flask, render_template, request, url_for, redirect, jsonify
import sqlite3

app = Flask(__name__, static_folder="templates/static")

def get_temperature_color(temperature_str, room_name):
    try:
        temperature_value, temperature_unit = temperature_str.split()
        temperature_value = float(temperature_value)
        
        conn = sqlite3.connect("Data_Waltikka.db")
        cursor = conn.cursor()
        cursor.execute('SELECT min_temperature, max_temperature FROM settings')
        min_temp, max_temp = cursor.fetchone()
        conn.close()
        
        if temperature_unit == '°C':
            if temperature_value >= max_temp:
                return 'red'
            elif temperature_value <= min_temp:
                return 'blue'
        elif temperature_unit == '°F':
            temperature_celsius = (temperature_value - 32) * 5/9
            if temperature_celsius >= max_temp:
                return 'red'
            elif temperature_celsius <= min_temp:
                return 'blue'
    except (ValueError, TypeError):
        pass
    return ''


def get_humidity_color(humidity_str, room_name):
    try:
        humidity = float(humidity_str.split(' %')[0])
        conn = sqlite3.connect("Data_Waltikka.db")
        cursor = conn.cursor()
        cursor.execute('SELECT min_humidity, max_humidity FROM settings')
        min_humidity, max_humidity = cursor.fetchone()
        conn.close()
        
        if humidity >= max_humidity:
            return 'red'
        elif humidity <= min_humidity:
            return 'blue'
    except (ValueError, TypeError):
        pass
    return ''

def get_co2_color(co2_str, room_name):
    try:
        co2 = float(co2_str.split(' ppm')[0])
        conn = sqlite3.connect("Data_Waltikka.db")
        cursor = conn.cursor()
        cursor.execute('SELECT min_co2, max_co2 FROM settings')
        min_co2, max_co2 = cursor.fetchone()
        conn.close()
        
        if co2 >= max_co2:
            return 'red'
        elif co2 <= min_co2:
            return 'blue'
    except (ValueError, TypeError):
        pass
    return ''


room_tables = {
    "Room 'ala_aula'": "room_ala-aula_1",
    "Room 109": "room_109_1",
    "Room 126": "room_126_1",
    "Room 129": "room_129_1",
    "Room '2. kerroksen aulatila'": "room_2._kerroksen_aulatila_2",
    "Room 209": "room_209_2",
    "Room 226": "room_226_2",
    "Room 229": "room_229_2",
    "Room 307": "room_307_3",
    "Room 326": "room_326_3",
    "Room 'Ala-aulan narikka'": "room_Ala-aulan_narikka_1",
    "Room 'Alaravintola'": "room_Alaravintola_1",
    "Room 'Linno_1_...' 2nd floor": "room_Linno_1_ja_2_neuvottelutila_2",
    "Room 'Linno_1_...' 3rd floor": "room_Linno_1_ja_2_neuvottelutila_3",
    "Room 'Ravintolasali'": "room_Ravintolasali_1",
    "Room 'Vuolle 1 neuvottelutila'": "room_Vuolle_1_neuvottelutila_2",
    "Room 'Yläravintola lavan...'": "room_Yläravintola_lavan_oikea_puoli_2",
}

room_floors = {
    "Room 'ala_aula'": "1st floor",
    "Room 109": "1st floor",
    "Room 126": "1st floor",
    "Room 129": "1st floor",
    "Room '2. kerroksen aulatila'": "2nd floor",
    "Room 209": "2nd floor",
    "Room 226": "2nd floor",
    "Room 229": "2nd floor",
    "Room 307": "3rd floor",
    "Room 326": "3rd floor",
    "Room 'Ala-aulan narikka'": "1st floor",
    "Room 'Alaravintola'": "1st floor",
    "Room 'Linno_1_...' 2nd floor": "2nd floor",
    "Room 'Linno_1_...' 3rd floor": "3rd floor",
    "Room 'Ravintolasali'": "1st floor",
    "Room 'Vuolle 1 neuvottelutila'": "2nd floor",
    "Room 'Yläravintola lavan...'": "2nd floor",
}


def get_temperature_unit():
    conn = sqlite3.connect("Data_Waltikka.db")
    cursor = conn.cursor()
    cursor.execute('SELECT temperature_unit FROM settings')
    temperature_unit = cursor.fetchone()
    conn.close()
    return temperature_unit[0] if temperature_unit else 'Celsius'


def get_latest_data(room_name):
    conn = sqlite3.connect("Data_Waltikka.db")
    cursor = conn.cursor()
    table_name = room_tables.get(room_name)
    if table_name:
        cursor.execute(f'SELECT Temperature, Humidity, CO2 FROM "{table_name}" WHERE Timestamp = (SELECT MAX(Timestamp) FROM "{table_name}")')
        data = cursor.fetchone()
        conn.close()
        if data:
            temperature, humidity, co2 = data
            temperature_unit = get_temperature_unit()
            
            if temperature_unit == 'Celsius':
                temperature_str = f'{temperature:.2f} °C' if temperature is not None and temperature != 0 else 'Missing'
            else:
                temperature = (temperature * 9/5) + 32
                temperature_str = f'{temperature:.2f} °F' if temperature is not None and temperature != 0 else 'Missing'

                
            humidity_str = f'{humidity:.2f} %' if humidity is not None and humidity != 0 else 'Missing'
            co2_str = f'{co2:.2f} ppm' if co2 is not None and co2 != 0 else 'Missing'
            return temperature_str, humidity_str, co2_str
    conn.close()
    return 'Missing', 'Missing', 'Missing'

@app.route("/apply_settings", methods=["POST"])
def apply_settings():
    if request.method == "POST":
        temperature_unit = request.form.get("temperature-unit")
        min_temp = float(request.form.get("minTemp"))
        max_temp = float(request.form.get("maxTemp"))
        min_co2 = float(request.form.get("minCO2"))
        max_co2 = float(request.form.get("maxCO2"))
        min_humidity = float(request.form.get("minHumidity"))
        max_humidity = float(request.form.get("maxHumidity"))
        email_address = request.form.get("emailAddress")

        conn = sqlite3.connect("Data_Waltikka.db")
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE settings
            SET
                email = ?,
                temperature_unit = ?, 
                min_temperature = ?,
                max_temperature = ?,
                min_humidity = ?,
                max_humidity = ?,
                min_co2 = ?,
                max_co2 = ?
        ''', (email_address, temperature_unit, min_temp, max_temp, min_humidity, max_humidity, min_co2, max_co2))
        conn.commit()
        conn.close()

        return redirect(url_for("settings", current_temperature_unit=temperature_unit))

@app.route("/default_settings")
def reset_settings():
    initial_settings = {
        "minTemp": 20.0,
        "maxTemp": 24.0,
        "minHumidity": 40.0,
        "maxHumidity": 65.0,
        "minCO2": 400.0,
        "maxCO2": 1000.0
    }
    
    return jsonify(initial_settings)

@app.route("/rooms")
def rooms():
    room_data = {}
    rooms_with_red_border = []
    room_info_list = []

    floor = request.args.get('floor', 'all')  # Get the 'floor' parameter from the URL

    for room_name, table_name in room_tables.items():
        latest_data = get_latest_data(room_name)
        if latest_data:
            temperature, humidity, co2 = latest_data
        else:
            temperature, humidity, co2 = None, None, None
        room_data[room_name] = {
            "temperature": temperature,
            "humidity": humidity,
            "co2": co2
        }

        # Check if any of the parameters are out of the norm
        temperature_color = get_temperature_color(temperature, room_name)
        humidity_color = get_humidity_color(humidity, room_name)
        co2_color = get_co2_color(co2, room_name)

        room_info = f"{room_name}"

        if temperature_color == 'red':
            room_info += f" | High temp."

        if temperature_color == 'blue':
            room_info += f" | Low temp."

        if humidity_color == 'red':
            room_info += f" | High hum."

        if humidity_color == 'blue':
            room_info += f" | Low hum."

        if co2_color == 'red':
            room_info += f" | High CO2"

        if co2_color == 'blue':
            room_info += f" | Low CO2"

        if (temperature_color in ['red', 'blue'] or humidity_color in ['red', 'blue'] or co2_color in ['red', 'blue']):
            rooms_with_red_border.append(room_name)
            room_info_list.append(room_info)

        # Filter rooms based on the selected floor
        if floor != 'all':
            abnormal_rooms = [room_name for room_name in rooms_with_red_border if room_floors.get(room_name) == floor]
            normal_rooms = [room_name for room_name in room_data if room_floors.get(room_name) == floor and room_name not in abnormal_rooms]
        else:
            abnormal_rooms = [room_name for room_name in rooms_with_red_border]
            normal_rooms = [room_name for room_name in room_data if room_name not in abnormal_rooms]

        # Sort the rooms separately
        abnormal_rooms.sort(key=lambda room_name: room_data[room_name]['temperature'] + room_data[room_name]['humidity'] + room_data[room_name]['co2'], reverse=True)
        normal_rooms.sort(key=lambda room_name: room_data[room_name]['temperature'] + room_data[room_name]['humidity'] + room_data[room_name]['co2'], reverse=True)

        # Concatenate the two lists to maintain the order of abnormal rooms first
        filtered_rooms = abnormal_rooms + normal_rooms



    return render_template("mainpage.html", room_data=room_data, sorted_rooms=filtered_rooms,
                           get_temperature_color=get_temperature_color, get_humidity_color=get_humidity_color,
                           get_co2_color=get_co2_color, room_floors=room_floors, room_info_list=room_info_list)





@app.route("/settings")
def settings():
    return render_template("settings.html")

@app.route("/customization")
def customization():
    return render_template("customization.html")

@app.route("/weather")
def weather():
    return render_template("weather.html")

if __name__ == "__main__":
    app.run(debug=True)