from flask import Flask, request, jsonify
import requests

# app = Flask(__name__)

SCREEN_RESPONSES = {
    "APPOINTMENT": {
        "data": {
            "is_date_enabled": True,
            "is_time_enabled": False
        }
    },
    "DETAILS": {},
    "SUMMARY": {},
    "SUCCESS": {}
}

def get_data(search):
    response = requests.get(f"https://api.duniyatech.com/WhatsApp-cloud-api/fatch_date_and_time/{search}")
    return response.json()

def get_next_screen(decrypted_body):
    screen = decrypted_body.get("screen")
    data = decrypted_body.get("data", {})
    action = decrypted_body.get("action")
    flow_token = decrypted_body.get("flow_token")

    if action == "ping":
        return {"data": {"status": "active"}}

    if "error" in data:
        print("Received client error:", data)
        return {"data": {"acknowledged": True}}

    if action == "INIT":
        res_date = get_data("date")
        response = SCREEN_RESPONSES["APPOINTMENT"].copy()
        response["data"].update({"date": res_date})
        return response

    if action == "data_exchange":
        if screen == "APPOINTMENT":
            if data.get("trigger") == "Date_selected":
                res_time = get_data(data.get("Date_of_appointment"))
                response = SCREEN_RESPONSES["APPOINTMENT"].copy()
                response["data"].update({"time": res_time, "is_time_enabled": True})
                return response

            appointment = f"{data.get('Date_of_appointment_0')} at {data.get('Time_Slot_1')}"
            details = (f"Name: {data.get('Patient_Name_2')}\n"
                       f"Guardian: {data.get('Guardian_Name')}\n"
                       f"DOB: {data.get('Date_Of_Birth')}\n"
                       f"Age: {data.get('Age_3')}\n"
                       f"Email: {data.get('Email_4')}\n"
                       f"Symptoms: {data.get('Other_Symptoms_5')}\n"
                       f"City: {data.get('City')}\n"
                       f"Address: {data.get('Address')}")
            response = SCREEN_RESPONSES["DETAILS"].copy()
            response["data"].update({"appointment": appointment, "details": details, **data})
            return response

        if screen == "SUMMARY":
            response = SCREEN_RESPONSES["SUCCESS"].copy()
            response["data"] = {"extension_message_response": {"params": {"flow_token": flow_token}}}
            return response

    print("Unhandled request body:", decrypted_body)
    return {"error": "Unhandled request"}, 400

