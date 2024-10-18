import json
import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Attr, Key
import os
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['STORAGE_TEZBUILDDATA_NAME'])

def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def send_response(statusCode, body):
    if isinstance(body, list):
        for item in body:
            if 'Costs' in item:
                del item['Costs']

    return {
        'statusCode': statusCode,
        'headers': {
            'Access-Control-Allow-Headers': '*',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },
        'body': json.dumps(body, default=decimal_default)
    }
def get_products_after_update_withbatch(event):
    print('getProductsAfterUpdate')
    if 'itemIds' not in event:
        return send_response(400, 'Missing itemIds in request')

    item_ids = event['itemIds']
    print(f"Processing item IDs: {item_ids}")
    items = []
    batch_keys = {
         table.name: {
            'Keys': [{'ItemType': 'P', 'UniqueId': id} for id in item_ids],
            #'ProjectionExpression': 'SKU'
        }
    }
    try:
        response = dynamodb.batch_get_item(RequestItems=batch_keys)
        items = response.get('Responses', {}).get(table.name, [])

        unprocessed_keys = response.get('UnprocessedKeys', {})
        while unprocessed_keys:
            response = dynamodb.batch_get_item(RequestItems=unprocessed_keys)
            items.extend(response.get('Responses', {}).get(table.name, []))
            unprocessed_keys = response.get('UnprocessedKeys', {})

        filtered_items = [item for item in items if item.get('ItemType') == 'P']

        return send_response(200, filtered_items)
    
    except Exception as e:
        return ("error",e)
def get_products_after_update_withquery(event):
    print('getProductsAfterUpdate')
    if 'itemIds' not in event:
        return send_response(400, 'Missing itemIds in request')

    item_ids = event['itemIds']
    print(f"Processing item IDs: {item_ids}")

    #id=item_ids[0]
    print(f"Processing item IDs: {item_ids}")
    items = []
    try:
        for id in item_ids:
            print(f"Querying for SKU: {id}")
            response = table.query(
                IndexName='SKU',
                KeyConditionExpression=Key('ItemType').eq('P') & Key('SKU').eq(id),
                ProjectionExpression= 'Heading, Subheading, SKU, Image, ItemType'
             
            )
            items.extend(response.get('Items', []))
            
            while 'LastEvaluatedKey' in response:
                response = table.query(
                    IndexName='SKU',
                    KeyConditionExpression=Key('ItemType').eq('P') & Key('SKU').eq(id),
                    ExclusiveStartKey=response['LastEvaluatedKey']
                )
                items.extend(response.get('Items', []))

        print(f"Successfully retrieved {len(items)} items")
        return send_response(200, items)
    
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"An error occurred: {error_code} - {error_message}")
        print(f"Table name: {table.name}")
        return send_response(500, f"An error occurred: {error_code} - {error_message}")
  
def get_products_by_id(event):
    print('getProductById')
    if 'id' not in event:
        return send_response(400, 'Missing id in request')

    id = event['id']
   
    response = table.query(
        IndexName='SKU',
        KeyConditionExpression=Key('ItemType').eq('P') & Key('SKU').eq(id)
    )

    items = response.get('Items', [])

    return send_response(200, items)


def get_products_by_pgid(event):
    print('getProductsByPGID')
    if 'pgid' not in event:
        print('Missing pgid in request')
        return send_response(400, 'Missing pgid in request')

    pgid = event['pgid']
    response = table.query(
        KeyConditionExpression=Key('ItemType').eq('PG') & Key('UniqueId').eq(pgid)
    )

    items = response.get('Items', [])
    print('items:', items)

    if not len(items):
        print('PGID not found')
        return send_response(404, "PGID not found")
    
    attributes = items[0]

    if 'Category' not in attributes:
        print('Category not found in attributes')
        return send_response(400, 'Category not found in attributes')
    
    category = attributes['Category']

    del attributes['ItemType']
    del attributes['UniqueId']
    del attributes['Category']
    del attributes['Heading']
    del attributes['Subheading']

    filter_expression = None
    for key, value in attributes.items():
        if filter_expression is None:
            filter_expression = Attr(key).eq(value)
        else:
            filter_expression = filter_expression & Attr(key).eq(value)

    response = table.query(
        IndexName='Category',
        KeyConditionExpression='ItemType = :itemType AND Category = :category',
        ExpressionAttributeValues={
            ':itemType': 'P',
            ':category': category
        },
        FilterExpression=filter_expression
    )

    items = response.get('Items', [])

    res = {}
    res["Products"] = {}
    for item in items:
        if 'Costs' in item:
            del item['Costs']
        hashed_id = item.get('SKU')

        if hashed_id not in res["Products"]:
            res["Products"][hashed_id] = [item]
        else:
            res["Products"][hashed_id].append(item)
    
    res["Id"] = pgid

    return send_response(200, res)


def handler(event, context):
    print('received event:')
    print(event)

    # TODO: get approx location
     # print("detected user ip:", event['requestContext']['identity'].get('sourceIp'))

    body = json.loads(event['body'])

    if 'action' not in body:
        print('Missing action in request')
        return send_response(400, 'Missing action in request')
    if body['action'] == 'getProductsAfterUpdateBatch':
        return get_products_after_update_withbatch(body)
    if body['action'] == 'getProductsAfterUpdateQuery':
        return get_products_after_update_withquery(body)        
    if body['action'] == 'getProductById':
        return get_products_by_id(body)
    if body['action'] == 'getProductsByPGID':
        return get_products_by_pgid(body)
    
    return send_response(400, 'Invalid action in request')
