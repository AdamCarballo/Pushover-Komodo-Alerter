import socket
import json
import requests
import os

# Pushover API settings
PUSHOVER_USER_KEY = os.getenv('PUSHOVER_USER_KEY')
PUSHOVER_API_TOKEN = os.getenv('PUSHOVER_API_TOKEN')

# Webhook settings
LISTEN_HOST = '0.0.0.0'
LISTEN_PORT = 7000

def send_pushover_alert(message, priority = 0):
    url = "https://api.pushover.net/1/messages.json"
    payload = {
        "token": PUSHOVER_API_TOKEN,
        "user": PUSHOVER_USER_KEY,
        "message": message,
        'priority': priority
    }
    response = requests.post(url, data=payload)
    return response.status_code, response.text

def start_server(host=LISTEN_HOST, port=LISTEN_PORT):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)

    print(f"Listening on {host}:{port}...")

    while True:
        client_socket, addr = server_socket.accept()
        print(f"Connection from {addr}")

        request_data = client_socket.recv(4096).decode("utf-8")
        if not request_data:
            client_socket.close()
            continue

        try:
            # Extract JSON payload from the HTTP request
            request_lines = request_data.split("\r\n\r\n", 1)
            if len(request_lines) < 2:
                client_socket.close()
                continue

            json_data = json.loads(request_lines[1])
            level = json_data.get("level", "INFO")
            type = json_data.get('data', {}).get('type', 'Unknown')
            alert_data = json_data.get("data", {}).get("data", {})
            server_name = alert_data.get("name", "Unknown")
            region = alert_data.get('region', 'World')

            # Remove non-human-readable data and already extracted data
            alert_data.pop('id', None)
            alert_data.pop('name', None)
            alert_data.pop('region', None)

            message = (
                f'{level} - {type}\n'
                f'{server_name} [{region}]\n'
                f'Msg: {json.dumps(alert_data, indent=2).strip('{}')}'
            )

            # Send alert via Pushover
            priority = 1 if level == 'ERROR' else 0
            status_code, response_text = send_pushover_alert(message, priority)
            print(f"Pushover Response: {response_text}")

            # Send HTTP response
            response = "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n{\"status\": \"alert sent\"}"
            client_socket.sendall(response.encode("utf-8"))

        except json.JSONDecodeError:
            client_socket.sendall(b"HTTP/1.1 400 Bad Request\r\n\r\nInvalid JSON")
        finally:
            client_socket.close()

if __name__ == "__main__":
    # Check if the environment variables are set
    if not PUSHOVER_USER_KEY or not PUSHOVER_API_TOKEN:
        raise ValueError("Pushover environment variables are not set!")

    start_server()
