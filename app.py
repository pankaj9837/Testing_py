import json
import os
import base64
import hmac
import hashlib
from flask import Flask, request, Response
from encryption import decrypt_request, encrypt_response, FlowEndpointException
from flow import get_next_screen

app = Flask(__name__)

PORT = 3000
PASSPHRASE = "password"
APP_SECRET = "62528c1b0adc2320d8b6e27b0254ede0"
PRIVATE_KEY = """-----BEGIN ENCRYPTED PRIVATE KEY-----
MIIFJDBWBgkqhkiG9w0BBQ0wSTAxBgkqhkiG9w0BBQwwJAQQNxRsdQY3ZxCRhhRg
YPsxcgICCAAwDAYIKoZIhvcNAgkFADAUBggqhkiG9w0DBwQIRXIfeYDwfFUEggTI
/OKx+yH0WFgHErS+htFIJ+hsagBtU+sJefuOlCFqju3/oVoRoK26lhFW3/7O4hfU
nVM+CGiHEGmD/UHAkzw3EcB3q6MUhzdXBhZOI6UNZBcrHlCDNX+IbDK+gyBVCIN1
NYjSvUa/Zu6Tn/iIzj9GCriE+/T4ZIrZ/NpqERwkzGP4ptHrX0nOAqsIPfzqCkdy
xyf7E5wNssZJV7ZSPuwLzNQZH4RQvYgxDXK5dR0Hzyw2IAaB3V3RAhaoM8eU7o24
i3Wl9FuXhDuyKfbTJInPEUCsxBzRypY8Tk+3OMQD4rkkrFjo6GarRauizgn4/UND
n12GOFBaPXmgPkTMuBm/016GANHF5l6e5DPVrWvKrHgbozGarYhLUi5CU6ll47kc
ZDWGP0GGiQWLotZJBg5hVKB0Y5QVrl1lo0BquW794ymzN3GQPw5WiaZuash6fzSq
frZQL2/8y/S7faV7u80dlWaMHlG95XuHqibGP04p7Sjqn76ByjDHZSBtdnh2Qqjc
UAOVeYxKwZfMg8vd28TlzUovKoAzUFh/tNdbbsf5x7/VyfG5HWAmWrb8qEhPG712
jl43st6xfR7x82Kn0x9FylZZ5tisuxAWA+WcDkva8mcb6HTpd/kvi6HOf78mhskK
pj8B8LHfAQTfSvvsvJYiyZ9ZexQBDmLIEUqI9fS9Z0fi7KWEKjTBj5vKn/+e7YjO
h6Plr6UfDavParPhHCmFbX2TaX2/CPVCJDJTol3lmh8Wc3DftHn0WmD0h0/KADze
d49rRxoqATtWyz5O2pRL9VZURu+2PEzsZzR/VOBAtiHKla9bNyqSfsLLmPRsPht6
huqQVUYSOFDilCseOssG8gosWjpdFHMkQDWd/8g7FNoDVx5kTSTdD0g0TWwWGA6l
/5FE3W4KNhmPIhOtE9axhfcD+ayrK1F8PwEY4jYrrbgEpG3lmA0uZFjDdgoRSLiQ
0qZrRTiro3U5KKPQyWqlmsjJ6DiwBt1KE41hchZwXAjsUwfBp48Gi95T+8fTlpUN
R1RXVkNOQJxnlb1x/XEvsVMe/gwfcBKZHCeY8PTondoEvddwkUBLNEusr4DkoOFo
etj61LE4yMrrFpMhLb/dQLmfZd1JiV4e4GmSnCuPt3jiV6M8QL+zocyij+k3xB1y
LrCLDxmQ+i8bteQ4TsZsJCyU7fV+DLvdKRy4D4K07IbRPtCWN+gZ31G+GfLKaC93
Zj50Lt1k+HBXw5o69EvdyNrZqMHHpejXH9+tWa2tz09jt2vvCLGPzT9CHn5CLb6y
CW/+J4tLU0YEwp49FSoTXe69jVlAc4+cQlyuXtSne9sehKQSbYsnYqPBIGdCz9+6
yIVN/Q3Wm+AChCB9xjLU4dQDt/zBngxYAvlZx6mYGrsqzOBvFnnbtRUXL1oN399M
TXxvjc/QoxzVgy841G89LyW2U+Ak/GtbEXmKEySZctvbJOdJHIEfA23WVS3HlX+C
/9R68G33DjHe/ThbjRxa4NKmSzWkSQ846dT/6Xs9aUaNYNRsIbBWe4WGLCiGP7vZ
+TEzKgHGgMc1+DIOkpVHhrB88L2O/XZWNocd4jXN5Yi/m1dqw1JaMSRKkk/07Iq7
OjFeUtREr3lHqpCxA7JNNh0/u+687pXA
-----END ENCRYPTED PRIVATE KEY-----"""

@app.route("/", methods=["POST"])
def handle_request():
    if not PRIVATE_KEY:
        raise Exception('Private key is empty. Please check your environment variable "PRIVATE_KEY".')
    
    if not is_request_signature_valid(request):
        return Response(status=432)
    
    try:
        decrypted_request = decrypt_request(request.json, PRIVATE_KEY, PASSPHRASE)
    except FlowEndpointException as err:
        return Response(status=err.status_code)
    except Exception as err:
        print(err)
        return Response(status=500)
    
    aes_key_buffer = decrypted_request["aesKeyBuffer"]
    initial_vector_buffer = decrypted_request["initialVectorBuffer"]
    decrypted_body = decrypted_request["decryptedBody"]
    
    print("\U0001F4AC Decrypted Request:", decrypted_body)
    
    screen_response = get_next_screen(decrypted_body)
    print("\U0001F449 Response to Encrypt:", screen_response)
    
    return encrypt_response(screen_response, aes_key_buffer, initial_vector_buffer)

@app.route("/", methods=["GET"])
def home():
    return "<pre>Nothing to see here.\nCheckout README.md to start.</pre>"

def is_request_signature_valid(req):
    if not APP_SECRET:
        print("Warning: App Secret is not set. Please add it in the .env file.")
        return True
    
    signature_header = req.headers.get("x-hub-signature-256")
    if not signature_header:
        print("Error: Missing x-hub-signature-256 header")
        return False
    
    signature_buffer = bytes.fromhex(signature_header.replace("sha256=", ""))
    
    raw_body = req.data
    if not raw_body:
        print("Error: req.data is undefined. Ensure middleware is set up correctly.")
        return False
    
    digest = hmac.new(APP_SECRET.encode(), raw_body, hashlib.sha256).digest()
    
    if not hmac.compare_digest(digest, signature_buffer):
        print("Error: Request Signature did not match")
        return False
    
    return True

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # Use Render's assigned port
    app.run(host="0.0.0.0", port=port)
