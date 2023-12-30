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
    return http_response


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
    return http_response



