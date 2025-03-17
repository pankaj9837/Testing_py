from flask import Flask, request, jsonify
import requests

# app = Flask(__name__)

SCREEN_RESPONSES = {
  "APPOINTMENT": {
    "screen": "APPOINTMENT",
    "data": {
      "department": [
        {
          "id": "shopping",
          "title": "Shopping & Groceries"
        },
        {
          "id": "clothing",
          "title": "Clothing & Apparel"
        },
        {
          "id": "home",
          "title": "Home Goods & Decor"
        },
        {
          "id": "electronics",
          "title": "Electronics & Appliances"
        },
        {
          "id": "beauty",
          "title": "Beauty & Personal Care"
        }
      ],
      "location": [
        {
          "id": "1",
          "title": "King’s Cross, London"
        },
        {
          "id": "2",
          "title": "Oxford Street, London"
        },
        {
          "id": "3",
          "title": "Covent Garden, London"
        },
        {
          "id": "4",
          "title": "Piccadilly Circus, London"
        }
      ],
      "is_location_enabled": True,
      "is_date_enabled": True,
      "time": [
        {
          "id": "10:00",
          "title": "10:00"
        },
        {
          "id": "11:21",
          "title": "11:21",
          "enabled": False
        },
        {
          "id": "11:31",
          "title": "11:31"
        },
        {
          "id": "12:11",
          "title": "12:11",
          "enabled": False
        },
        {
          "id": "12:30",
          "title": "12:11"
        }
      ],
      "is_time_enabled": True,
      "img": "iVBORw0KGgoAAAANSUhEUgAAAGQAAABkCAYAAABw4pVUAAAACXBIWXMAAAsTAAALEwEAmpwYAA..."
    }
  },
  "DETAILS": {
    "screen": "DETAILS",
    "data": {
      "symptoms": [
        {
          "id": "Cold",
          "title": "cold"
        },
        {
          "id": "Cough",
          "title": "Cough"
        }
      ]
    }
  },
  "SUMMARY": {
    "screen": "SUMMARY",
    "data": {
      "appointment": "Beauty & Personal Care Department at Kings Cross, London\nMon Jan 01 2024 at 11:30.",
      "details": "Name: John Doe\nEmail: john@example.com\nPhone: 123456789\n\nA free skin care consultation, please",
      "department": "beauty",
      "location": "1",
      "date": "2024-01-01",
      "time": "11:30",
      "name": "John Doe",
      "email": "john@example.com",
      "phone": "123456789"
    }
  }
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

