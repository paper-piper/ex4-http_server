import os
from PIL import Image
import io
import logging


logging.basicConfig(filename='Interfaces.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('Interfaces')

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


def parse_query_params(query_string):
    params = query_string.split('&')
    params_dict = {}
    for param in params:
        key, value = param.split('=')
        params_dict[key] = value
    return params_dict


def calculate_next(query_string):
    try:
        num = int(query_string.split('=')[1])
        response = str(num + 1)
        http_header = "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\n"
    except (ValueError, IndexError):
        http_header = "HTTP/1.1 400 Bad Request\r\n\r\n"
        response = ""

    http_response = http_header + response
    return http_response.encode()


def calculate_area(query_string):
    try:
        parameters = parse_query_params(query_string)
        height = float(parameters['height'])
        width = float(parameters['width'])
        response = str(height * width / 2)
        http_header = "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\n"
    except (KeyError, ValueError,):
        http_header = "HTTP/1.1 400 Bad Request\r\n\r\n"
        response = ""

    http_response = http_header + response
    return http_response.encode()


def upload(image_parameters):
    """
    save an image in the "upload" folder
    :param image_parameters: a tuple of the image name (0) and the image bytes (1)
    :return: OK status code
    """
    image_name = image_parameters[0].split('=')[1]
    image_bytes = image_parameters[1]
    logging.info(f"Trying to save image with the name = {image_name} "
                 f"and Image bytes = {image_bytes}")
    # Create the "Images" folder if it doesn't exist
    images_folder = os.path.join(os.path.dirname(__file__), "upload")
    os.makedirs(images_folder, exist_ok=True)

    # Construct the file path for the new image
    image_path = os.path.join(images_folder, image_name)

    # Open the image using PIL
    with Image.open(io.BytesIO(image_bytes)) as img:
        # Save the image to the specified path
        img.save(image_path)
        logger.info(f"Image: {image_name} saved successfully at: {image_path}")
    return "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nPOST request processed.".encode()


def image(image_name):
    # get only the value
    image_name = image_name.split('=')[1]
    images_folder = os.path.join(os.path.dirname(__file__), "upload")
    os.makedirs(images_folder, exist_ok=True)

    # Construct the file path for the new image
    image_path = os.path.join(images_folder, image_name)

    try:
        with open(image_path, 'rb') as image_file:
            image_bytes = image_file.read()
    except FileNotFoundError:
        # If the file is not found, return a 404 Not Found response
        return b"HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\nConnection: close\r\n\r\n"

    # Determine the content type based on the image file
    image_type = image_name.split('.')[1]

    # Constructing the HTTP response headers
    headers = [
        "HTTP/1.1 200 OK",
        f"Content-Type: {CONTENT_TYPES[image_type]}",
        f"Content-Length: {len(image_bytes)}",
        "Connection: close",
    ]

    # Joining headers with '\r\n' to create the header section
    headers_section = "\r\n".join(headers)

    # Creating the full HTTP response by combining headers and image bytes
    http_response = f"{headers_section}\r\n\r\n".encode() + image_bytes

    return http_response


def read_image_bytes(file_path):
    try:
        with open(file_path, 'rb') as f:
            image_bytes = f.read()
        return image_bytes
    except Exception as e:
        print(f"Error reading image bytes: {e}")
        return None


def config_not_found():
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