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
MIIFJDBWBgkqhkiG9w0BBQ0wSTAxBgkqhkiG9w0BBQwwJAQQd6lQS6B5yB3w35l9
nsF+QAICCAAwDAYIKoZIhvcNAgkFADAUBggqhkiG9w0DBwQIzrJNJZQ76F4EggTI
TucgxOwQlFeqJIv8PNepQOToYpWZyYR6w8KOhc0T3N/9bI6dpLUSEuW5FbcM5zmx
33CsMfEqWuEnaALuhxWJfFWEQEYHyJMXgaFvW9k6W14ZmyTaW3S3rwKThsYWaZcc
PLx/stu0eaRDde8sBIi6tN8ujPJofpFFC7vo4mKNN46lE+CPwPNTeu/sRogdOv74
KS9LFxYt44bEooa4A2WCKd5EzyefN6eLx1j5Rpz9mcHBRBvwGEy211HduxqPXamc
GxqVdgUMz3a+MXCqhqBs4abhUw5jPhSwsxli+xNIAti7g4dgfTyuzI9v+PR6pnOL
xJrFbkpd0mvpvTwhufVB0k8zbJwDjDnb8DlTf75PAApRCJx6sUw7BlJEy43DHtzr
xMVWdd6qiMAroV50W/HHXMW649VbqWQPwdcoxE4OJykMIDZ+2orXrfh/PoVBvQoE
IBfBgWyuaBxAF/+2filulkpLwMHjEuxb8wssCA8gNnDNsHrlVMlFtdobUxHHE8ID
efviJVG/TXp4jcr8McF0mZBbP1FGKb2kuDhcBTGhBQgjJA7Xba0macAfXnmrJuGl
tPQshid4tO1GFuKkx0dWbTwlmcWgg4a3V++2+om2dRQ//NeyOEgG8/3hXArx699g
Jufjg8v7lQcMyYYwxEPxfNYjnuU5DeJn+ebgVP9vQvY+mLIA0arIj2RUhLBZgWZi
lHvlqI2ofXWpkJpuKqBYjOH7Vo6hkDQjo6h4uaS0YouuY7+di7UxE8zt0f/ODLWn
lYIqCJ9tvFPXkTJ9H9z3K8cA2QLgiZcvJTkHBMq5sKslsBb+iMiTwub+ka6Q0TM5
0EhJE4qQHMJKDtsrr0Qy6kXA7NlK3sLWMcFeNSmBUEW+K7GruvwZwAzWd3GVqjwo
XYvxjRFu82Yp5Ric1Q2/+VNK27gYD/ONcfpqrsvZo6G6bAVQ1vhLcqBdDDslyEbP
ix08SunoGCNzIGLpJ5j/0bDaz1RIfMvRwwtiNldhRHEv+q44AU9Hr5TdzGCNO9Sf
xMgUArYdObqAAwTUhlcM9Py0ZLl0Xvvh3lMjGUnXHvykBi8gNvcm1BZkQZTANXFJ
GG35B3+Q2oRtePTQxT1cgV4XOfM4NexOa3RPKbt4qnqcyCgYVtZa0nQW3JNMbbox
t9kP+8N7IjZMnxDwEG9WSc44GzCGK8kY3G/yxePnPCd8DVP6O2W1+uzka0mjsGj5
93U4wqEC3YwAjuuJXeX7pDe4ehyh1wF3aer4sSZbJMRnuPDWqMyscHjRqx+8K9ZR
2Abm/Uo8fjO3lKWTsvUfrf6brpxwlysHli6hq+i7oWIs5LRxwAIrsy8sx5gLTNrB
/sBz7xBXHXUoQ17LC/EPCyCuNDdCCTAy2zCSTzypKQxRVMRDldyC8xMOmc4GWYrq
8yu1uEYpD3HHA7eQXm+pwcwkaU9lgI5XyUhRuyuFucDpuyIzjuJCGLZsPw3XK8B/
iUoHbXrTPt42+OKdwMggVpsp1Ll03ogh69h0iE7zDxz9O9SzNEMFqunNj+G09ISx
Q0IKi7TQUwfWzilTUSEpaUXBpSL+C9RiOIrnd0h89kbzDEqU2PE6l4GuRrtvIuLK
k3aT53ltPKzgI5Aa/w2fVTCPoDW9kI2R
-----END ENCRYPTED PRIVATE KEY-----"""

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
