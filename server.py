import socket
import os
import Interfaces
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
NOT_IMPLEMENTED = "HTTP/1.1 501 Not Implemented\r\n\r\n"
OK = "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nPOST request processed."


def send_response(client_socket, response):
    """
    sends response and logs the process
    :param client_socket:
    :param response:
    :return:
    """
    try:
        if isinstance(response, str):
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


def brake_header(resource):
    """
    brake the header into formatted interface name and query parameters.
    basically, convert /calculate-area?height=3&width=4 to calculate_area and height=3&width=4
    :param resource:
    :return: interface name, query_string
    """
    # TODO: add try except in case of invalid parsing
    interface_name = resource.split('?')[0][1:].replace('-', '_')
    query_string = resource.split('?')[1]
    return interface_name, query_string


def run_interface(interface_name, interface_parameters, client_socket):
    try:
        if hasattr(Interfaces, interface_name):
            interface_func = getattr(Interfaces, interface_name)
            http_response = interface_func(interface_parameters)
            # in case of post request, the send_response won't send anything since the response is None
            send_response(client_socket, http_response)
            return True
        else:
            logger.error(f"Client tried to run un-supported interface (interface: {interface_name})")
            return False
    except AttributeError as e:
        logger.error(f"Error while finding interface: ({e})")
        return False


def handle_get_request(resource, client_socket):
    """
    Check the required resource, generate proper HTTP response and send
    to client
    :param resource: the required resource
    :param client_socket: a socket for the communication with the client
    :return: None
    """
    # TODO: parse function into multiple functions for easier understanding
    # TODO: add try except to needed parts of the code
    # if it is interface, we will call the interface and return
    if '?' in resource:
        interface_name, query_params = brake_header(resource)
        run_interface(interface_name, query_params, client_socket)
        return

    # / means the user request the default url
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

    # Check if file doesn't exist
    if not os.path.isfile(url):
        http_header = NOT_FOUND
        http_response = http_header.encode()
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


def handle_post_request(request, body, client_socket):
    interface_name, query_params = brake_header(request)
    # we compress together the body and query params in a tuple, [0] = query string and [1] = body
    # if the interface executed successfully, we return okay response. else, we return bad request
    if run_interface(interface_name, (query_params, body), client_socket):
        send_response(client_socket, OK)
    else:
        send_response(client_socket, BAD_REQUEST)


def read_http_request(client_socket):
    """
    get the entire request details, parsed.
    :param client_socket:
    :return: a tuple where [0] = request type, [1] = request path, [2] = body (optional)
    """
    # TODO: parse the function into multiple functions
    # TODO: handle errors while parsing (request isn't formatted accordingly, decoding failed)
    # TODO: add try except for necessary parts
    # Read the request line
    request_line = b''
    while b'\r\n' not in request_line:
        request_line += client_socket.recv(1)

    # If the request line is empty, return an empty string
    if not request_line.strip():
        return ""

    # Split the request line into method, path, and protocol
    method, path, protocol = request_line.decode('utf-8').strip().split(' ')

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

    # Extract Content-Length from headers
    content_length = 0
    for header in headers.decode('utf-8').split('\r\n'):
        if header.startswith('Content-Length:'):
            content_length = int(header.split(':')[1].strip())

    # Read the request body based on Content-Length
    if content_length > 0:
        body = b''
        while len(body) < content_length:
            body += client_socket.recv(1)
    else:
        body = b""

    # return request details
    return method, path, body


def handle_client(client_socket):
    """
    Handles client requests: verifies client's requests are legal HTTP, calls
    function to handle the requests
    :param client_socket: the socket for the communication with the client
    :return: None
    """
    print('Client connected')
    try:
        method, resource, body = read_http_request(client_socket)

        if method == "-1":
            print('Error: Not a valid HTTP request')
            send_response(client_socket, BAD_REQUEST)
        else:
            # Select handler method accordingly
            if method == "GET":
                handle_get_request(resource, client_socket)
            elif method == "POST":
                handle_post_request(resource, body, client_socket)
            else:
                send_response(client_socket, NOT_IMPLEMENTED)
    except socket.timeout:
        print('Client request timed out')
    finally:
        print('Closing connection')


def main():
    """
    the main function
    :return:
    """
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
    # TODO: add assertion checks for function I can check
    main()
