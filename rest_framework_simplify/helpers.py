import base64
import dateutil.parser
import pytz
import uuid


def convert_utc_to_tz(d, tz):
    # make sure datetime is aware of timezone
    d = d.replace(tzinfo=pytz.utc)
    return d.astimezone(pytz.timezone(tz)).replace(tzinfo=None)


def convert_tz_to_utc(d, tz):
    tzinfo = pytz.timezone(tz)
    return tzinfo.normalize(tzinfo.localize(d.replace(tzinfo=None))).astimezone(pytz.utc)


def convert_serialized_binary_to_string(serialized_binary_data):
    binary_str = base64.b64decode(serialized_binary_data)
    return binary_string_to_string(binary_str)


def binary_string_to_string(binary_str):
    return binary_str.decode('utf-8', errors='ignore').replace('\\n', ' ').replace('\\r', '')

def handle_bytes_decoding(item):
    for key in item:
        if type(item[key]) is dict:
            handle_bytes_decoding(item[key])
        if type(item[key]) is memoryview:
            item[key] = binary_string_to_string(bytes(item[key]))
        elif type(item[key]) is bytes:
            item[key] = binary_string_to_string(item[key])

def generate_str(str_length):
    return str(uuid.uuid4())[:str_length]


def parse_binary(str):
    # todo: check if it's binary first, then return the binary value
    return bytes(str, 'utf-8')


def parse_date(date_str):
    try:
        field_value = dateutil.parser.parse(date_str)
    except ValueError:
        field_value = None
    return field_value
