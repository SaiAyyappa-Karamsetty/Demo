import json
from decimal import Decimal
import json
import os
import boto3
from urllib import request, error, parse
from botocore.exceptions import ClientError,ParamValidationError
from boto3.dynamodb.conditions import Attr, Key
location_client = boto3.client('location')
CALCULATOR_NAME = os.environ['ROUTECALCULATOR_TEZBUILD']
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
def get_shipping_cost(supplier_id):
   shipping_flat_rate=0
   if supplier_id == 'BX_YL':
      shipping_flat_rate=1      #In future this should be fetched from a table from the db
      return shipping_flat_rate
   elif supplier_id == 'RRT':
      shipping_flat_rate=1
      return shipping_flat_rate
   elif supplier_id == 'GS_PSK':
      shipping_flat_rate=1
      return shipping_flat_rate
   else:
      return -1
   
def calculate_route(position1, position2):
   print(position1, position2)

   response = location_client.calculate_route(
    CalculatorName=CALCULATOR_NAME,
    DeparturePosition=position1,
    DestinationPosition=position2,
    TravelMode="Truck",
    DistanceUnit="Miles"
   )
   miles=response['Summary']['Distance'] if 'Distance' in response['Summary'] else -1
   print(miles)
   return miles
def get_sales_tax(state):
   #if state == 'FL': In future we will have to fetch this from db and check each states sales tax
    #  return 0.06
   return send_response(200, 0.06) #for now we wil return Florida sales tax
def get_facility_location(facility_id):
   if facility_id == 'RRT':
      return [-82.33288,29.64849]   #hardcoded for now just for Ridgway Roof Truss, in future it should be fetched for all facilities from a table in the db  
def pricing(event):
  try:
    body = json.loads(event['body'])
    print(body) 
    grouped_items = {}
    position=body['position']
    cartitems=json.loads(body['cartitems'])
    for item in cartitems:
        facility_id = item['facilityid']
        if item['facilityid'] not in grouped_items:
            #shipping
            grouped_items[facility_id] = {
                'items': [],  
                'shippingcost': 0
            }
        grouped_items[facility_id]['items'].append(item)
        if facility_id == 'BX_YL' or 'GS_PSK':
            grouped_items[facility_id]['shippingcost']=100
        if facility_id == 'RRT':
            facility_location=get_facility_location(facility_id)
            distance_in_miles=calculate_route(position,facility_location)
            if distance_in_miles == -1:
                return send_response(400, 'Invalid location position')
            print(distance_in_miles)
            shipping_cost=distance_in_miles*get_shipping_cost(facility_id)+20 #20 is a flat fee which is constant for now, will change in future with data from db
            grouped_items[facility_id]['shippingcost']=shipping_cost
    print(grouped_items)
    return send_response(200, grouped_items)
  except Exception as e:
    print(e)
    return send_response(400, 'Invalid request, something is wrong, please contact support')


def handler(event, context):
  print('received event:')
  print(event)
  
  body = json.loads(event['body'])
  
  if 'action' not in body:
    print('Missing action in request')
    return send_response(400, 'Missing action in request')
  if body['action'] == 'pricing':
    return pricing(event)
  elif body['action'] == 'getSalesTax':
    return get_sales_tax(event)
  elif body['action'] == 'calculateRoute':
    return calculate_route(body['position1'], body['position2'])
  else:
    return send_response(400, 'Invalid action in request')
  