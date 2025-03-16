from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

SCREEN_RESPONSES = {
    "APPOINTMENT": {"data": {}},
    "DETAILS": {"data": {}},
    "SUCCESS": {"data": {}}
}

API_URL = "https://api.duniyatech.com/WhatsApp-cloud-api/fatch_date_and_time/"

def get_data(search):
    response = requests.get(f"{API_URL}{search}")
    return response.json()

@app.route('/api/getNextScreen', methods=['POST'])

def get_next_screen():
    decrypted_body = request.json
    screen = decrypted_body.get("screen")
    data = decrypted_body.get("data")
    action = decrypted_body.get("action")
    flow_token = decrypted_body.get("flow_token")
    
    if action == "ping":
        return jsonify({"data": {"status": "active"}})
    
    if data and "error" in data:
        print("Received client error:", data)
        return jsonify({"data": {"acknowledged": True}})
    
    if action == "INIT":
        res_date = get_data('date')
        response = SCREEN_RESPONSES["APPOINTMENT"].copy()
        response["data"] = {
            **SCREEN_RESPONSES["APPOINTMENT"]["data"],
            "date": res_date,
            "is_date_enabled": True,
            "is_time_enabled": False
        }
        return jsonify(response)
    
    if action == "data_exchange":
        if screen == "APPOINTMENT":
            if data.get("trigger") == "Date_selected":
                res_time = get_data(data.get("Date_of_appointment"))
                response = SCREEN_RESPONSES["APPOINTMENT"].copy()
                response["data"] = {
                    **SCREEN_RESPONSES["APPOINTMENT"]["data"],
                    "time": res_time,
                    "is_time_enabled": True
                }
                return jsonify(response)
            
            appointment = f"{data.get('Date_of_appointment_0')} at {data.get('Time_Slot_1')}"
            details = f"Name: {data.get('Patient_Name_2')}\n" \
                      f"Guardian: {data.get('Guardian_Name')}\n" \
                      f"DOB: {data.get('Date_Of_Birth')}\n" \
                      f"Age: {data.get('Age_3')}\n" \
                      f"Email: {data.get('Email_4')}\n" \
                      f"Symptoms: {data.get('Other_Symptoms_5')}\n" \
                      f"City: {data.get('City')}\n" \
                      f"Address: {data.get('Address')}"
            response = SCREEN_RESPONSES["DETAILS"].copy()
            response["data"] = {
                **SCREEN_RESPONSES["DETAILS"]["data"],
                "appointment": appointment,
                "details": details,
                **data
            }
            return jsonify(response)
        
        if screen == "SUMMARY":
            response = SCREEN_RESPONSES["SUCCESS"].copy()
            response["data"] = {
                "extension_message_response": {
                    "params": {
                        "flow_token": flow_token
                    }
                }
            }
            return jsonify(response)
    
    print("Unhandled request body:", decrypted_body)
    return jsonify({"error": "Unhandled request"}), 400

if __name__ == '__main__':
    app.run(debug=True)
