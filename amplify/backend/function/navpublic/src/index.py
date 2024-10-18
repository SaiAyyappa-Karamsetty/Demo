import json
import boto3
from boto3.dynamodb.conditions import Attr, Key
import os
from decimal import Decimal
from requests_aws4auth import AWS4Auth
from opensearchpy import OpenSearch, RequestsHttpConnection

dynamodb = boto3.resource('dynamodb')
dynamodb_table_name =  os.environ['STORAGE_TEZBUILDDATA_NAME']
table = dynamodb.Table(dynamodb_table_name)
region = os.environ['REGION']  # Change to your region
service = 'es'  # For OpenSearch
credentials = boto3.Session().get_credentials()
 
# Create AWS4Auth for OpenSearch

awsauth = AWS4Auth(
    credentials.access_key,
    credentials.secret_key,
    region,
    service,
    session_token=credentials.token
)

# Set the OpenSearch endpoint (without https://)
opensearch_endpoint = os.environ['OPENSEARCHENDPOINT']  # Change to your endpoint

# Create an OpenSearch client

client = OpenSearch(
    hosts=[{'host': opensearch_endpoint, 'port': 443}],
    http_auth=awsauth,
    use_ssl=True,
    verify_certs=False,  # Change to True for production
    connection_class=RequestsHttpConnection
)
 
def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError
 
def send_response(statusCode, body):
    return {
        'statusCode': statusCode,
        'headers': {
            'Access-Control-Allow-Headers': '*',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },
        'body': json.dumps(body, default=decimal_default)

    }
 
# returns a response object

# TODO: post-MVP we will need to filter by the user's serviceable facilities
def get_page_cards_home(body):
    params = body.get('params')
    if not params:
        return send_response(400, 'Missing params in request')
    print(params)
    id = params.get('homeId')
    print(id)
    if id:
        response = table.query(
            KeyConditionExpression=Key('ItemType').eq('H') & Key('UniqueId').eq(id)
        )
        print(response)
        if not response['Items']:
            return send_response(404, 'Item not found')
        
        home_item = response['Items'][0]
        
        title = home_item.get('Title', '')
        searchBar = home_item.get('SearchBar', '')
        pgids = home_item.get('PGIDs', [])
        pids = home_item.get('PIDs', [])
   
    # Prepare keys for batch_get_item with correct format
    keys_pg = [{'ItemType': 'PG', 'UniqueId': pgid} for pgid in pgids]
    print("Keys for batch_get_item:", keys_pg)

    response_pg = {}
    pg_items = []
    #change this before code push
    try:
        response_pg = dynamodb.batch_get_item(
            RequestItems={
                dynamodb_table_name: {
                    'Keys': keys_pg, 
                    'ProjectionExpression': 'Heading, Subheading, UniqueId, Image'
                }
            }
        )
        print(response_pg)
        pg_items = response_pg.get('Responses', {}).get(dynamodb_table_name, [])
        print(pg_items)
    except Exception as e:
        print("Error retrieving group items:", str(e))
        return send_response(500, f'Error retrieving group items: {str(e)}')

    if not pg_items:
        return send_response(404, 'No group items found')

    pid_items = []
    for pid in pids:
        print(pid)
        pid_response = table.query(
            IndexName='SKU',
            KeyConditionExpression=Key('ItemType').eq('P') & Key('SKU').eq(pid),
            ProjectionExpression='Heading, Subheading, SKU, Image' 
        )
        if pid_response['Items']:
            pid_items.append(pid_response['Items'][0])
    print(pid_items)
    cards = []
    for item in pg_items:
        cards.append({
            'heading': item.get('Heading', ''),
            'subheading': item.get('Subheading', ''),
            'id': item['UniqueId'],
            'image': item.get('Image', ''),
            'type': 'group'
        })

    for item in pid_items:
        cards.append({
            'heading': item.get('Heading', ''),
            'subheading': item.get('Subheading', ''),
            'id': item['SKU'],
            'image': item.get('Image', ''),
            'type': 'product'
        })

    return send_response(200, {
        'title': title,
        'cards': cards,
        'searchBar':searchBar
    })
    
def get_page_cards_nav(body):
    params = body.get('params')
    if not params:
        return send_response(400, 'Missing params in request')
    print(params)
    id = params.get('navId')
    print(id)
    if id:
        response = table.query(
            KeyConditionExpression=Key('ItemType').eq('N') & Key('UniqueId').eq(id)
        )
        print(response)
        if not response['Items']:
            return send_response(404, 'Item not found')
        
        navigation_item = response['Items'][0]
        
        title = navigation_item.get('Title', '')
        pgids = navigation_item.get('PGIDs', [])
        pids = navigation_item.get('PIDs', [])
        
        
    else:
        navigation_item = {}
        title = ''
        pgids = []
        pids = []

    filters = {}
    if not pgids and not pids:
        del navigation_item['PGIDs']
        del navigation_item['PIDs']
        del navigation_item['UniqueId']
        del navigation_item['ItemType']
        if 'Title' in navigation_item:
            del navigation_item['Title']
    #Check with Jacob on how to validate correct filters in Nav records
        filters = navigation_item
        filter_response = get_page_cards_by_filters(navigation_item)
        if len(filter_response) != 2:
            return send_response(400, filter_response[0])

        return send_response(200, {
            "filters": filters,
            "validFilters": {},
            "paginationToken": filter_response[0],
            "cards": filter_response[1],
            "title": title
        })

    # Prepare keys for batch_get_item with correct format
    keys_pg = [{'ItemType': 'PG', 'UniqueId': pgid} for pgid in pgids]
    print("Keys for batch_get_item:", keys_pg)

    response_pg = {}
    pg_items = []
    #change this before code push
    try:
        response_pg = dynamodb.batch_get_item(
            RequestItems={
                dynamodb_table_name: {
                    'Keys': keys_pg, 
                    'ProjectionExpression': 'Heading, Subheading, UniqueId, Image'
                }
            }
        )
        print(response_pg)
        pg_items = response_pg.get('Responses', {}).get(dynamodb_table_name, [])
        print(pg_items)
    except Exception as e:
        print("Error retrieving group items:", str(e))
        return send_response(500, f'Error retrieving group items: {str(e)}')

    if not pg_items:
        return send_response(404, 'No group items found')

    pid_items = []
    for pid in pids:
        print(pid)
        pid_response = table.query(
            IndexName='SKU',
            KeyConditionExpression=Key('ItemType').eq('P') & Key('SKU').eq(pid),
            ProjectionExpression='Heading, Subheading, SKU, Image' 
        )
        if pid_response['Items']:
            pid_items.append(pid_response['Items'][0])
    print(pid_items)
    cards = []
    for item in pg_items:
        cards.append({
            'heading': item.get('Heading', ''),
            'subheading': item.get('Subheading', ''),
            'id': item['UniqueId'],
            'image': item.get('Image', ''),
            'type': 'group'
        })

    for item in pid_items:
        cards.append({
            'heading': item.get('Heading', ''),
            'subheading': item.get('Subheading', ''),
            'id': item['SKU'],
            'image': item.get('Image', ''),
            'type': 'product'
        })

    return send_response(200, {
        'title': title,
        'cards': cards
    })


def get_page_cards_search(body):
    params = body.get('params')
    if not params:
        return send_response(400, 'Missing params in request')
    
    filter_response = get_page_cards_by_filters(params)
    if len(filter_response) != 2:
        return send_response(400, filter_response[0])

    return send_response(200, {
        "filters": params,
        "paginationToken": filter_response[0],
        "cards": filter_response[1]
    })
# TODO: this will use elasticsearch/opensearch when the cost of the service is justified ($26 per month for the smallest instance)

# returns a list of the form [pagination_token, cards] OR a list of the form ['error msg'], NOT a response object

def get_page_cards_by_filters(filters):


     # Extract page and limit from filters, with defaults
    page = filters.get('page', 1)
    limit = filters.get('limit',10000)

    # Calculate the 'from' value for pagination
    from_ = (page - 1) * limit

    # Construct the OpenSearch query

    query = {

        "bool": {

            "must": []

        }

    }
 
     
 
    # Add filters to the OpenSearch query

    if 'category' in filters:

        query['bool']['must'].append({

            "term": {"Category.keyword": filters['category']}

        })

    if 'searchTerm' in filters:

        search_terms = filters['searchTerm'].split()

        for term in search_terms:

            query['bool']['must'].append({"fuzzy":{"SearchableField": {"value": term,"fuzziness":2}}})

    # Additional filters from frontend
    
    for key, value in filters.items():
        if key not in ['category', 'searchTerm', 'page', 'limit']:
            # Check if the value is a dictionary (indicating a range)
            if isinstance(value, dict) and 'from' in value and 'to' in value:
                query['bool']['must'].append({
                    "range": {
                        key: {
                            "gte": value['from'],
                            "lte": value['to']
                        }
                    }
                })
            else:
                query['bool']['must'].append({
                    "term": {f"{key}.keyword": value}
                })

                
    # Perform the OpenSearch query
    print("Query generated--->")
    print(query)
    response = client.search(

        index="page-cards-index",  # Specify the correct index name

        body={

            "query": query,
            "sort": [{"_id": {"order": "asc"}}],
            "size": limit,  # Use the limit from the filters
            "from": from_   # Use the calculated 'from' value
        }

    )
 
    # Extract the hits (data) from the response

    cards = []

    for hit in response['hits']['hits']:

        source = hit['_source']
        
        if source.get('ItemType','') == 'PG':
           
           cards.append({
            'category': source.get('Category', ''),
            'heading': source.get('Heading', ''),
            'subheading': source.get('Subheading', ''),
            'id': source.get('id', ''),
            'image': source.get('Image', ''),
            'type': 'group'
            })
        else:
            cards.append({
            'category': source.get('Category', ''),
            'heading': source.get('Heading', ''),
            'subheading': source.get('Subheading', ''),
            'id': source.get('Sku', ''),
            'image': source.get('Image', ''),
            'type': 'product'
            })
            
 
    # Return the result in the desired format

    return [response['hits']['total']['value'], cards]


def get_page_cards_by_aggregations(filters):
    page = filters.get('page', 1)
    limit = filters.get('limit', 10000)
    from_ = (page - 1) * limit

    query = {"bool": {"must": []}}

    if filters.get('category'):
        query['bool']['must'].append({"term": {"Category.keyword": filters['category']}})

    if filters.get('searchTerm'):
        search_terms = filters['searchTerm'].split()
        for term in search_terms:
            query['bool']['must'].append({"fuzzy":{"SearchableField": {"value": term,"fuzziness":2}}})

    for key, value in filters.items():
        if key not in ['category', 'searchTerm', 'page', 'limit', 'aggr'] and value is not None:
            query['bool']['must'].append({"term": {f"{key}.keyword": value}})

    aggregations = {}
    if 'Length' in filters.get('aggr', []):
        aggregations['Length'] = {"stats": {"field": "Length"}}
    if 'Width' in filters.get('aggr', []):
        aggregations['Width'] = {"stats": {"field": "Width"}}
    if 'Thickness' in filters.get('aggr', []):
        aggregations['Thickness'] = {"stats": {"field": "Thickness"}}
    if 'Grade' in filters.get('aggr', []):
        aggregations['Grade'] = {"terms": {"field": "Grade.keyword"}}
    if 'Species' in filters.get('aggr', []):
        aggregations['Species'] = {"terms": {"field": "Species.keyword"}}
    if 'Brand' in filters.get('aggr', []):
        aggregations['Brand'] = {"terms": {"field": "Brand.keyword"}}
    if 'FingerJoint' in filters.get('aggr', []):
        aggregations['FingerJoint'] = {"terms": {"field": "FingerJoint.keyword"}}
    if 'Precision' in filters.get('aggr', []):
        aggregations['Precision'] = {"terms": {"field": "Precision.keyword"}}
    if 'Treatment' in filters.get('aggr', []):
        aggregations['Treatment'] = {"terms": {"field": "Treatment.keyword"}}
    if 'PanelType' in filters.get('aggr', []):
        aggregations['PanelType'] = {"terms": {"field": "PanelType.keyword"}}
    if 'Edge' in filters.get('aggr', []):
        aggregations['Edge'] = {"terms": {"field": "Edge.keyword"}}
    if 'Finish' in filters.get('aggr', []):
        aggregations['Finish'] = {"terms": {"field": "Finish.keyword"}}
    if 'Origin' in filters.get('aggr', []):
        aggregations['Origin'] = {"terms": {"field": "Origin.keyword"}}
    if 'Metric' in filters.get('aggr', []):
        aggregations['Metric'] = {"terms": {"field": "Metric.keyword"}}
    if 'Profile' in filters.get('aggr', []):
        aggregations['Profile'] = {"terms": {"field": "Profile.keyword"}}

    response = client.search(
        index="page-cards-index",
        body={
            "query": query,
             "sort": [{"_id": {"order": "asc"}}],
            "size": limit,
            "from": from_,
            "aggs": aggregations
        }
    )

    cards = []
    for hit in response['hits']['hits']:
        source = hit['_source']
        if source.get('ItemType') == 'PG':
            cards.append({
            'category': source.get('Category', ''),
            'heading': source.get('Heading', ''),
            'subheading': source.get('Subheading', ''),
            'id': source.get('id', ''),
            'image': source.get('Image', ''),
            'type': 'group'
            })
        else:
            cards.append({
            'category': source.get('Category', ''),
            'heading': source.get('Heading', ''),
            'subheading': source.get('Subheading', ''),
            'id': source.get('Sku', ''),
            'image': source.get('Image', ''),
            'type': 'product'
            })
            

    aggregations_response = {}
    for key in aggregations.keys():
        if "stats" in aggregations[key]:
            aggregations_response[key] = {
                "min": response["aggregations"][key]["min"],
                "max": response["aggregations"][key]["max"],
                "avg": response["aggregations"][key]["avg"],
                "type": "slider"  # Numerical fields
            }
        elif "terms" in aggregations[key]:
            aggregations_response[key] = {
                "values": [bucket["key"] for bucket in response["aggregations"][key]["buckets"]],
                "type": "dropdown"  # Categorical fields
            }

    return [response['hits']['total']['value'], cards, aggregations_response]

    
def handler(event, context):
    print('Received event:')
    print(event)

    body = event

    if 'action' not in body:
        print('Missing action in request')
        return send_response(400, 'Missing action in request')

    if body['action'] == 'getPageCardsByNavParams':
        return get_page_cards_nav(body)

    if body['action'] == 'getPageCardsByParams':
        return get_page_cards_search(body)
    
    if body['action'] == 'getPageCardsByHome':
        return get_page_cards_home(body)
        
    if body['action'] == 'getPageCardsByAggregations':
        filters = body.get('params', {})  # Directly use the input params
        filter_response = get_page_cards_by_aggregations(filters)
        return send_response(200, {
            "paginationToken": filter_response[0],
            "cards": filter_response[1],
            "aggregations": filter_response[2]
        })

    return send_response(400, 'Invalid action in request')