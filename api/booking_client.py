import os

import requests

API_URL = os.getenv("API_URL", "http://localhost:5001/api")


class BookingClient:
    """Thin wrapper over the booking API (adapted from double-booked/api/booking_client.py).

    Every method returns the raw `requests.Response` so tests assert on
    status codes and bodies directly.
    """

    def __init__(self, base_url=API_URL):
        self.base_url = base_url
        self.session = requests.Session()

    @staticmethod
    def payload(roomid=1, checkin="2027-05-01", checkout="2027-05-03",
                firstname="Test", lastname="User"):
        return {"roomid": roomid, "firstname": firstname, "lastname": lastname,
                "bookingdates": {"checkin": checkin, "checkout": checkout}}

    def create_booking(self, data):
        return self.session.post(f"{self.base_url}/booking", json=data)

    def get_booking(self, booking_id):
        return self.session.get(f"{self.base_url}/booking/{booking_id}")

    def update_booking(self, booking_id, data):
        return self.session.put(f"{self.base_url}/booking/{booking_id}", json=data)

    def delete_booking(self, booking_id):
        return self.session.delete(f"{self.base_url}/booking/{booking_id}")
