from decimal import Decimal
import json
import os
import boto3
from urllib import request, error, parse
from botocore.exceptions import ClientError,ParamValidationError
from boto3.dynamodb.conditions import Attr, Key
from math import radians, cos, sin, sqrt, atan2
location_client = boto3.client('location')
PLACES_INDEX_NAME = os.environ['PLACESINDEX_TEZBUILDLOCATION']
IPINFO_TOKEN = os.environ['IPINFO_ACCESS_TOKEN']
def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def send_response(statusCode, body):
    if isinstance(body, list):
        pass
    return {
        'statusCode': statusCode,
        'headers': {
            'Access-Control-Allow-Headers': '*',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },
        'body': json.dumps(body, default=decimal_default)
    }
def get_ip_info(ip_address):
    try:
        url = f'https://ipinfo.io/{ip_address}'
        params = {'token': IPINFO_TOKEN}
        
        # Encode parameters and append to URL
        full_url = f"{url}?{parse.urlencode(params)}"
        
        # Make the request
        with request.urlopen(full_url) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                print(data['loc'])
                latitude=data['loc'].split(',')[0]
                latitude=float(latitude)
                longitude=data['loc'].split(',')[1]
                longitude=float(longitude)
                print(type(latitude))
                print(latitude,longitude)
                position=[longitude,latitude]
                try:
                    response_search_place_index_for_position=location_client.search_place_index_for_position(   
                        IndexName=PLACES_INDEX_NAME,
                        Position=position,
                        MaxResults=1,
                    )
                    print(response_search_place_index_for_position)
                    address = response_search_place_index_for_position['Results'][0]['Place']['Label']
                    print(address)
                    return send_response(200, address)
                except Exception as e:
                    print(f"Unexpected error in getting location, Please enter your address manually: {str(e)}")
                    return send_response(500, {'error': 'Internal server error: Enter address manually', 'message':'Unexpected error in getting location, Please enter your address manually'})
                print(f"IP Info for {ip_address}: {json.dumps(coordinates)}")
                
            else:
                raise error.HTTPError(full_url, response.status, "HTTP Error", response.headers, None)
    except error.HTTPError as e:
        print(f"HTTP Error in get_ip_info: {e.code} - {e.reason}")
        return send_response(e.code, {'error': f'HTTP Error: {e.reason}'})
    except error.URLError as e:
        print(f"URL Error in get_ip_info: {str(e)}")
        return send_response(500, {'error': 'Failed to reach the server'})
    except Exception as e:
        print(f"Unexpected error in get_ip_info: {str(e)}")
        return send_response(500, {'error': 'Internal server error', 'details': str(e)})
        
def autocomplete_suggestions(event):
    try:
        body = json.loads(event['body'])
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {str(e)}")
        return send_response(400, {'error': 'Invalid JSON in request body'})

    text = body.get('text', '')
    if not text:
        return send_response(400, {'error': 'Missing or empty "text" parameter in request body'})

    try:
        response = location_client.search_place_index_for_suggestions(
            IndexName=PLACES_INDEX_NAME,
            Text=text,
            FilterCountries=['USA'],
            MaxResults=5,
            # You can add more parameters here as needed, such as:
            # BiasPosition=[longitude, latitude],
        )
        print(f"Successful response: {json.dumps(response, default=str)}")

        suggestions = [
            {
                'text': result['Text'],
                'place_id': result['PlaceId']
            }
            for result in response.get('Results', [])
        ]
        return send_response(200, suggestions)

    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"AWS ClientError: {error_code} - {error_message}")
        if error_code == 'ResourceNotFoundException':
            return send_response(404, {'error': 'Location index not found'})
        elif error_code == 'ValidationException':
            return send_response(400, {'error': 'Invalid parameters', 'details': error_message})
        elif error_code == 'AccessDeniedException':
            return send_response(403, {'error': 'Access denied to location service'})
        elif error_code == 'ThrottlingException':
            return send_response(429, {'error': 'Too many requests', 'details': 'Please try again later'})
        else:
            return send_response(500, {'error': 'AWS service error', 'details': error_message})

    except ParamValidationError as e:
        print(f"Parameter validation error: {str(e)}")
        return send_response(400, {'error': 'Invalid parameters', 'details': str(e)})

    except Exception as e:
        print(f"Unexpected error in autocomplete_suggestions: {str(e)}")
        return send_response(500, {'error': 'Internal server error', 'details': str(e)})
        
def geocode_location(event):
    try:
        body = json.loads(event['body'])
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {str(e)}")
        return send_response(400, {'error': 'Invalid JSON in request body'})

    if 'text' not in body:
        return send_response(400, {'error': 'Missing "text" parameter in request body'})

    try:
        response = location_client.search_place_index_for_text(
            IndexName=PLACES_INDEX_NAME,
            Text=body['text'],
            FilterCountries=["USA"],
            MaxResults=1,
        )
        print(f"Successful response: {json.dumps(response, default=str)}")
        coordinates = response['Results'][0]['Place']['Geometry']['Point']
        
        return send_response(200, coordinates)

    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"AWS ClientError: {error_code} - {error_message}")
        if error_code == 'ResourceNotFoundException':
            return send_response(404, {'error': 'Location index not found'})
        elif error_code == 'ValidationException':
            return send_response(400, {'error': 'Invalid parameters', 'details': error_message})
        elif error_code == 'AccessDeniedException':
            return send_response(403, {'error': 'Access denied to location service'})
        else:
            return send_response(500, {'error': 'AWS service error', 'details': error_message})

    except ParamValidationError as e:
        print(f"Parameter validation error: {str(e)}")
        return send_response(400, {'error': 'Invalid parameters', 'details': str(e)})

    except Exception as e:
        print(f"Unexpected error in geocode_location: {str(e)}")
        return send_response(500, {'error': 'Internal server error', 'details': str(e)})
def reverse_geocode_location(event):
    try:
        body = json.loads(event['body'])
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {str(e)}")
        return send_response(400, {'error': 'Invalid JSON in request body'})

    if 'position' not in body:
        return send_response(400, {'error': 'Missing "position" parameter in request body'})    
    position_str = body['position'].strip('[]')
    position = [float(x.strip()) for x in position_str.split(',')]
    print(position)
    try:
        response = location_client.search_place_index_for_position(
            IndexName=PLACES_INDEX_NAME,
            Position=position,
            MaxResults=1,
        )
        print(f"Successful response: {json.dumps(response, default=str)}")
        address = response['Results'][0]['Place']['Label']
        return send_response(200, address)
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"AWS ClientError: {error_code} - {error_message}")
        return send_response(500, {'error': 'AWS service error', 'details': error_message})
    except ParamValidationError as e:
        print(f"Parameter validation error: {str(e)}")
        return send_response(400, {'error': 'Invalid parameters', 'details': str(e)})
    except Exception as e:
        print(f"Unexpected error in reverse_geocode_location: {str(e)}")
        return send_response(500, {'error': 'Internal server error', 'details': str(e)})
    
def is_within_radius(event):
    try:
        response = geocode_location(event)
        print("response from geocode from is_within_radius",response)
        if response.get('statusCode') == 200:
            coordinates1 = json.loads(response.get('body', '{}'))
            print(coordinates1)
            coordinates2 = [-82.327377, 29.640493]
            distance = haversine_distance(coordinates1, coordinates2)
            
            if distance <=120:
                print("within radius")
                return send_response(200, True)
            else:
                print("not within radius")
                return send_response(200, False)
        else:
            raise Exception("Error in geocode_location")
    except Exception as e:
        print(f"Unexpected error in is_within_radius: {str(e)}")

def haversine_distance(coordinates1, coordinates2):
    lon1, lat1 = coordinates1[0], coordinates1[1]
    print("lon1",lon1)
    print("lat1",lat1)
    lon2, lat2 = coordinates2[0], coordinates2[1]
    print("lon2",lon2)
    print("lat2",lat2)
    R = 6371000
    phi_1 = radians(lat1)
    phi_2 = radians(lat2)
    delta_phi = radians(lat2 - lat1)
    delta_lambda = radians(lon2 - lon1)
    
    a = sin(delta_phi/2)**2 +\
          cos(phi_1) * cos(phi_2) *\
      sin(delta_lambda/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distance_miles = R * c * 0.000621371
    return distance_miles


def handler(event, context):
    # TODO implement
        
    print('received event:')
    print(event)

    # TODO: get approx location
     # print("detected user ip:", event['requestContext']['identity'].get('sourceIp'))

    body = json.loads(event['body'])

    if 'action' not in body:
        print('Missing action in request')
        return send_response(400, 'Missing action in request')
    if body['action'] == 'autocomplete':
        return autocomplete_suggestions(event)
    elif body['action'] == 'validAddress':
        return is_within_radius(event)
    elif body['action'] == 'reverseGeocode':
        return reverse_geocode_location(event)
    elif body['action'] == 'geocode':
        return geocode_location(event)
    elif body['action'] == 'getIpInfo':
        return get_ip_info(event['requestContext']['identity'].get('sourceIp'))
    return send_response(400, 'Invalid action in request')