import json
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
...
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
    app.run(port=PORT)
