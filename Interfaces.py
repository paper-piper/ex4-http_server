import os
from PIL import Image
import io
import logging


logging.basicConfig(filename='Interfaces.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('Interfaces')

# common status codes
BAD_REQUEST = "HTTP/1.1 400 Bad Request\r\n\r\n"


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
        http_header = BAD_REQUEST
        response = ""

    http_response = http_header + response
    return http_response


def calculate_area(query_string):
    try:
        parameters = parse_query_params(query_string)
        height = float(parameters['height'])
        width = float(parameters['width'])
        response = str(height * width / 2)
        http_header = "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\n"
    except (KeyError, ValueError,):
        http_header = BAD_REQUEST
        response = ""

    http_response = http_header + response
    return http_response


def upload(image_parameters):
    """
    save an image in the "upload" folder
    :param image_parameters: a tuple of the image name (0) and the image bytes (1)
    :return: nothing
    """
    image_name = image_parameters[0].split('=')[1]
    image_bytes = image_parameters[1]
    logging.info(f"Trying to save image with the name = {image_name} "
                 f"and Image bytes = {image_bytes}")
    # Create the "upload" folder if it doesn't exist
    images_folder = os.path.join(os.path.dirname(__file__), "upload")
    os.makedirs(images_folder, exist_ok=True)

    # Construct the file path for the new image
    image_path = os.path.join(images_folder, image_name)

    # Open the image using PIL
    with Image.open(io.BytesIO(image_bytes)) as img:
        # Save the image to the specified path
        img.save(image_path)
        logger.info(f"Image: {image_name} saved successfully at: {image_path}")


def read_image_bytes(file_path):
    try:
        with open(file_path, 'rb') as f:
            image_bytes = f.read()
        return image_bytes
    except Exception as e:
        print(f"Error reading image bytes: {e}")
        return None
