import socket
import os
import logging

# Server settings
QUEUE_SIZE = 10
IP = '0.0.0.0'
PORT = 80
SOCKET_TIMEOUT = 2
WEBROOT = "webroot"
DEFAULT_URL = WEBROOT + "/index.html"

# logger settings
# set up logging
logging.basicConfig(filename='sever.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('server')

# http protocol information
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
    '/legal': "HTTP/1.1 451 Unavailable for Legal Reasons\r\n\r\n",
}

# common status codes
BAD_REQUEST = "HTTP/1.1 400 Bad Request\r\n\r\n"
NOT_FOUND = "HTTP/1.1 404 Not Found\r\n\r\n"
NOT_FOUND_IMAGE_NAME = "not_found_duck.jpg"
NOT_FOUND_FOLDER_NAME = "special_images"
END_OF_MESSAGE = "/r/n/r/n"


def send_response(client_socket, response):
    """
    sends response and logs the process
    :param client_socket:
    :param response:
    :return:
    """
    try:
        client_socket.send(response.encode())
        logging.info(f"sent message ({response})")
    except SOCKET_TIMEOUT:
        logging.error(f"Failed to send message ({response}), socket timed out")


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
        http_header = NOT_FOUND
        http_response = http_header
        client_socket.send(http_response)
        return

    # Read the data from the file
    data = get_file_data(url)

    if data:
        http_header = (f"HTTP/1.1 200 OK\r\nContent-Type: {CONTENT_TYPES.get(file_type, 'text/plain')}\r\n"
                       f"Content-Length: {len(data)}\r\n\r\n")
        http_response = http_header.encode() + data
    else:
        http_header = NOT_FOUND
        http_response = http_header.encode()

    client_socket.send(http_response)


def validate_request_line(request_line):
    """
    validate and parse request line
    :param request_line:
    :return:
    """
    try:
        method, path, protocol = request_line.decode('utf-8').strip().split(' ')
        if method.lower() != "get" or not protocol.lower().startswith("http"):
            logger.info("User entered invalid http request")
            return False, "", ""
        logger.info(f"Read valid HTTP request: Method: {method}, Path: {path}")
        return True, method, path
    except IndexError as i:
        logger.info("User entered invalid http request")
        return False, "", ""


def read_http_request(client_socket):
    """
    get the entire request details, parsed.
    :param client_socket:
    :return: a tuple where [0] = is valid request, [1] = path
    """
    try:
        # Read the request line
        request_line = b''
        while b'\r\n' not in request_line:
            request_line += client_socket.recv(1)

        # If the request line is empty, return an empty string
        if not request_line.strip():
            return ""

        # Read headers until an empty line is encountered
        headers = b''
        while True:
            header_line = b''
            while b'\r\n' not in header_line:
                header_line += client_socket.recv(1)

            headers += header_line

            # If an empty line is encountered, break the loop
            if not header_line.strip():
                break

        # return request details
        return request_line
    except TypeError as t:
        logger.error(f"Error reading HTTP request: {t}")


def handle_client(client_socket):
    """
    Handles client requests: verifies client's requests are legal HTTP, calls
    function to handle the requests
    :param client_socket: the socket for the communication with the client
    :return: None
    """
    print('Client connected')
    try:

        request_line = read_http_request(client_socket)
        valid_http, method, path = validate_request_line(request_line)
        if valid_http:
            logger.error('Got a valid HTTP request')
            handle_client_request(path, client_socket)
        else:
            print('Error: Not a valid HTTP request')
            http_header = BAD_REQUEST
            client_socket.send(http_header.encode())
    except socket.timeout:
        print('Client request timed out')
    print('Closing connection')


def config_not_found():
    """
    configs the not found variable and adds to it the picture
    :return:
    """
    global NOT_FOUND
    images_folder = os.path.join(os.path.dirname(__file__), NOT_FOUND_FOLDER_NAME)
    image_path = os.path.join(images_folder, NOT_FOUND_IMAGE_NAME)
    with open(image_path, 'rb') as image:
        image_bytes = image.read()
        image_type = NOT_FOUND_IMAGE_NAME.split('.')[1]
        headers = [
            "HTTP/1.1 404 Not Found",
            f"Content-Type: {CONTENT_TYPES[image_type]}",
            f"Content-Length: {len(image_bytes)}",
            "Connection: close",
        ]
        headers_section = "\r\n".join(headers)
        NOT_FOUND = f"{headers_section}\r\n\r\n".encode() + image_bytes


def main():
    """
    the main function
    :return:
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    config_not_found()
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
    # Test case 1: Valid GET request
    request_line_1 = b"GET /path/to/resource HTTP/1.1"
    assert validate_request_line(request_line_1) == (True, "GET", "/path/to/resource")

    # Test case 2: Valid GET request with different path
    request_line_2 = b"GET /another/path HTTP/1.1"
    assert validate_request_line(request_line_2) == (True, "GET", "/another/path")

    # Test case 3: Invalid method (not GET)
    request_line_3 = b"POST /path/to/resource HTTP/1.1"
    assert validate_request_line(request_line_3) == (False, "", "")

    # Test case 4: Invalid protocol (not HTTP)
    request_line_4 = b"GET /path/to/resource AGreatProtocol/1.1"
    assert validate_request_line(request_line_4) == (False, "", "")
    main()
