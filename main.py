import socket
import re
import os

# Constants
QUEUE_SIZE = 10
IP = '0.0.0.0'
PORT = 80
SOCKET_TIMEOUT = 2
CONTENT_TYPES = {
    "html": "text/html;charset=utf-8",
    "jpg": "image/jpeg",
    "css": "text/css",
    "js": "text/javascript; charset=UTF-8",
    "txt": "text/plain",
    "ico": "image/x-icon",
    "gif": "image/gif",
    "png": "image/png"
}
SPECIAL_CASE_HEADERS = {
    '/forbidden': "HTTP/1.1 403 Forbidden\r\n\r\n",
    '/moved': "HTTP/1.1 302 Moved Temporarily\r\nLocation: /\r\n\r\n",
    '/error': "HTTP/1.1 500 Internal Server Error\r\n\r\n",
}
WEBROOT = "webroot"
DEFAULT_URL = WEBROOT + "/index.html"

END_OF_MESSAGE = "/r/n/r/n"


def get_file_data(file_name):
    """
    Get data from file
    :param file_name: the name of the file
    :return: data in a string
    """
    try:
        with open(file_name, 'rb') as file:
            return file.read()
    except FileNotFoundError:
        return None


def handle_client_request(resource, client_socket):
    """
    Check the required resource, generate proper HTTP response and send
    to client
    :param resource: the required resource
    :param client_socket: a socket for the communication with the client
    :return: None
    """
    if resource == '/':
        url = DEFAULT_URL
    else:
        url = WEBROOT + resource

    # Special cases handling
    if resource in SPECIAL_CASE_HEADERS:
        http_header = SPECIAL_CASE_HEADERS[resource]
        client_socket.send(http_header.encode())
        return

    # Extract the file type (extension)
    file_type = url.split('.')[-1]

    # Check if file exists and is not a directory
    if not os.path.isfile(url):
        http_header = "HTTP/1.1 404 Not Found\r\n\r\n"
        http_response = http_header.encode()
        client_socket.send(http_response)
        return

    # Read the data from the file
    data = get_file_data(url)

    if data:
        http_header = f"HTTP/1.1 200 OK\r\nContent-Type: {CONTENT_TYPES.get(file_type, 'text/plain')}\r\n\r\n"
        http_response = http_header.encode() + data
    else:
        http_header = "HTTP/1.1 404 Not Found\r\n\r\n"
        http_response = http_header.encode()

    client_socket.send(http_response)


def parse_http_request(request):
    """
    Check if request is a valid HTTP request and returns TRUE / FALSE and
    the requested URL
    :param request: the request which was received from the client
    :return: a tuple of (True/False - depending on if the request is valid,
    the requested resource )
    """
    pattern = re.compile(r'^(GET)\s+(/[^ ]*)\s+HTTP/1\.1\r\n')
    match = pattern.match(request.decode())

    if match:
        method, requested_url = match.groups()
        return True, requested_url
    else:
        return False, None


def handle_client(client_socket):
    """
    Handles client requests: verifies client's requests are legal HTTP, calls
    function to handle the requests
    :param client_socket: the socket for the communication with the client
    :return: None
    """
    print('Client connected')
    try:
        while (char := client_socket.recv(2).decode()) != END_OF_MESSAGE:
            client_socket += char
        client_request = client_socket.recv(1024)

        valid_http, resource = parse_http_request(client_request)
        if valid_http:
            print('Got a valid HTTP request')
            handle_client_request(resource, client_socket)
        else:
            print('Error: Not a valid HTTP request')
            http_header = "HTTP/1.1 400 Bad Request\r\n\r\n"
            client_socket.send(http_header.encode())
    except socket.timeout:
        print('Client request timed out')
    print('Closing connection')


def main():
    """Main function."""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_socket.bind((IP, PORT))
        server_socket.listen(QUEUE_SIZE)
        print("Listening for connections on port %d" % PORT)

        while True:
            client_socket, client_address = server_socket.accept()
            try:
                client_socket.settimeout(SOCKET_TIMEOUT)
                handle_client(client_socket)
            except socket.error as err:
                print('Received socket exception - ' + str(err))
            finally:
                client_socket.close()
    except socket.error as err:
        print('Received socket exception - ' + str(err))
    finally:
        server_socket.close()


if __name__ == "__main__":
    # some assertion checks
    assert parse_http_request(b"GET / HTTP/1.1\r\n")[0]
    assert not parse_http_request(b"GET /not_a_real_page HTTP/1.0\r\n")[0]
    assert not parse_http_request(b"BAD REQUEST / HTTP/1.1\r\n")[0]
    main()
