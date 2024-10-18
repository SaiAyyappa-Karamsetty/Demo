import json
import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Attr, Key
import os
from decimal import Decimal

cognito_client = boto3.client('cognito-idp')
USER_POOL_ID = os.environ['AUTH_TEZBUILD_USERPOOLID']
COGNITO_CLIENT_ID =os.environ['AUTH_COGNITO_CLIENT_ID']
dynamodb = boto3.resource('dynamodb')
table_name = os.environ['STORAGE_TEZBUILDDATA_NAME']
user_table = dynamodb.Table(table_name)
def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

    

def send_response_withCred(statusCode, body):
    if isinstance(body, list):
        pass
    return {
        'statusCode': statusCode,
        'headers': {
            'Access-Control-Allow-Headers': '*',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
            'Access-Control-Allow-Credentials': 'true'
        },
        'body': json.dumps(body, default=decimal_default)
    }
    
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

def set_cookie_header(name, value, max_age, http_only=True, secure=True):
    return f"{name}={value}; Max-Age={max_age}; Path=/; HttpOnly; SameSite=None;secure"

def reset_password(event):
    print("inside reset password", event)
    try:
        email = event['email']
        cognito_client.admin_reset_user_password(
            UserPoolId=USER_POOL_ID,
            Username=email
        )
        return send_response(200, {"message": "Password reset email sent"})
    except ClientError as e:
        error_message = e.response['Error']['Message']
        return send_response(400, {"error": error_message})

def update_user_details(event,authenticated_email):
    print("inside update user details", event)
    try:
        user = event['user']
        user_table.put_item(Item={
                'ItemType': 'U',
                'UniqueId': authenticated_email,
                'name': user.get('name', ''),
                'customertype': user.get('customertype', ''),
                'email': authenticated_email,
                'company': user.get('company', '')
            })
        user_details = user_table.get_item(
            Key={
                'ItemType': 'U',
                'UniqueId': authenticated_email
            }
        ).get('Item', {})
        print("details",user_details)
        return send_response(200, {
            "message": "User details updated successfully",
            "user": {
                "name": user_details.get('name', ''),
                "customertype": user_details.get('customertype', ''),
                "email": user_details.get('email',''),
                "company": user_details.get('company', '')
            }
        })
    except ClientError as e:
        error_message = e.response['Error']['Message']
        return send_response(400, {"error": error_message})



def confirm_code(event):
    print("inside confirm code",event)
    



def handler(event, context):
    # TODO implement
        
    print('received event:')
    print(event)

    claims = event['requestContext']['authorizer']['claims']
    print("claims",claims)
    authenticated_email = claims['email']

    body = json.loads(event['body'])

    if 'action' not in body:
        print('Missing action in request')
        return send_response(400, 'Missing action in request')
    elif body['action']=='updateUserDetails':
        print("entering update details")
        return update_user_details(body,authenticated_email)
    elif body['action']=='logoutUsers':
        print("entering logout users")
        return logout_user(body)
    return send_response(400, 'Invalid action in request')
