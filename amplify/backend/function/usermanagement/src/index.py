import json
import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Attr, Key
import os
from decimal import Decimal

cognito_client = boto3.client('cognito-idp')
USER_POOL_ID = os.environ['AUTH_TEZBUILD_USERPOOLID']
COGNITO_CLIENT_ID ="53shoghqau8et7u30avo43k708"
dynamodb = boto3.resource('dynamodb')
table_name = os.environ['STORAGE_TEZBUILDDATA_NAME']
user_table = dynamodb.Table(table_name)
def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

    
def send_cookie_response(statusCode, body,cookies):
    if isinstance(body, list):
        pass

    response={
        'statusCode': statusCode,
        'headers': {
            'Access-Control-Allow-Headers': '*',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
            'Access-Control-Allow-Credentials': 'true'
        },
        'body': json.dumps(body, default=decimal_default)
    }
    if cookies:
        response['multiValueHeaders'] = {'Set-Cookie': cookies}
    return response
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
    return f"{name}={value}; Max-Age={max_age}; Path=/; SameSite=Lax;"
    
def register_users(event):
    print("registering user")
    user=event["user"]
    try:
        response = cognito_client.sign_up(
            ClientId='53shoghqau8et7u30avo43k708',  #  Client ID
            Username=user['email'],
            Password=user['password'],
            UserAttributes=[
                {
                    'Name': 'name',
                    'Value': user['name']
                },
                {
                    'Name': 'email',
                    'Value': user['email']
                }
             
            ]
        )
        cognito_user_id=response['UserSub']
        print(cognito_user_id)
        user_data = {
            'ItemType': 'U',
            'UniqueId': user['email'],
            'email': user['email'],
            'name': user['name'],
            'company': user.get('company', ''),
            'user_status': 'UNCONFIRMED',
            'customertype':user.get('customertype', ''),
            # Add any other fields you want to store
        }
        user_table.put_item(Item=user_data)

        return send_response(200, {"message": "User registered successfully", "userId": response['UserSub']})
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(error_code)
        print(error_message)
        if error_code == 'UsernameExistsException':
            return send_response(400, {"error": "An account with this email already exists"})
        else:
            print(f"Error occurred: {error_message}")
            return send_response(400, {"error": error_message})

def verify_users(event):
    print("verifying user")
    user=event["user"]
    try:
        response = cognito_client.confirm_sign_up(
            ClientId='53shoghqau8et7u30avo43k708',
            Username=user['email'],
            ConfirmationCode=user['code'],

        )
        print(response)
        user_data = {
            'ItemType': 'U',
            'UniqueId': user['email'],
            'user_status': 'CONFIRMED',
         
            # Add any other fields you want to store
        }
        user_table.update_item(
            Key={'ItemType': 'U', 'UniqueId': user['email']},
            UpdateExpression='SET user_status = :status',
            ExpressionAttributeValues={':status': 'CONFIRMED'}
        )
        return send_response(200, {"message": "User verified successfully"})
    except ClientError as e:
        print(e)
        return send_response(400, {"error": str(e)})
        
def resend_code(event):
    print("resending code")
    user=event["user"]
    try:
        response=cognito_client.resend_confirmation_code(
            ClientId=COGNITO_CLIENT_ID,
            Username=user['email']
        )
        print(response)
        return send_response(200, {"message": "Code resent successfully"})
    except ClientError as e:
        print(e)
        error_message = e.response['Error']['Message']
        return send_response(401, {"error": error_message})
        
def login_users(event):
    print("logging users")
    user=event["user"]
    try:
        # response=cognito_client.initiate_auth( 
        #     ClientId='53shoghqau8et7u30avo43k708',
        #     AuthFlow='USER_PASSWORD_AUTH',
        #     AuthParameters={
        #         'USERNAME': user['email'],
        #         'PASSWORD': user['password']
        #     }
        # )
        # tokens = response['AuthenticationResult']
        # cognito_id = cognito_client.get_user(AccessToken=tokens['AccessToken'])['Username']
        #print("cognitoID",cognito_id)
        user_details = user_table.get_item(
            Key={
                'ItemType': 'U',
                'UniqueId': user['email']
            }
        ).get('Item', {})
        # cookies = [
        #     set_cookie_header('accessToken', tokens['AccessToken'], 3600),
        #     set_cookie_header('idToken', tokens['IdToken'], 3600),
        #     set_cookie_header('refreshToken', tokens['RefreshToken'], 2592000)  # 30 days
        # ]
#         return send_cookie_response(200, {"message": "User logged in successfully","user": {
#                 "name": user_details.get('name', ''),
#                 "customertype": user_details.get('customertype', ''),
#                 "email": user_details.get('email', ''),
#                 "company": user_details.get('company', '')
#             }
# },cookies)
        return send_response_withCred(200,{"message": "User logged in successfully","user": {
                 "name": user_details.get('name', ''),
                 "customertype": user_details.get('customertype', ''),
                 "email": user_details.get('email', ''),
                 "company": user_details.get('company', '')
             }
             })
    except ClientError as e:
        error_message = e.response['Error']['Message']
        return send_response(401, {"error": error_message})        
        
        
def forgot_password(event):
    print("inside forgot password", event)
    try:
        email = event['username']
        cognito_client.forgot_password(
            ClientId=COGNITO_CLIENT_ID,
            Username=email
        )
        return send_response(200, {"message": "Confirmation code sent to email address"})
    except ClientError as e:
        error_message = e.response['Error']['Message']
        return send_response(400, {"error": error_message})

def confirm_forgot_password(event):
    print("inside confirm forgot password", event)
    try:
        email = event['username']
        confirmation_code = event['confirmationCode']
        new_password = event['newPassword']
        cognito_client.confirm_forgot_password(
            ClientId=COGNITO_CLIENT_ID,
            Username=email,
            ConfirmationCode=confirmation_code,
            Password=new_password
        )
        return send_response(200, {"message": "Password reset successfully"})
    except ClientError as e:
        error_message = e.response['Error']['Message']
        return send_response(400, {"error": error_message})        
        



def handler(event, context):
    print('received event:')
    print(event)
    body = json.loads(event['body'])
    if 'action' not in body:
        print('Missing action in request')
        return send_response(400, 'Missing action in request')
    if body['action'] == 'registerUsers':
        return register_users(body)
    elif body['action'] == 'verifyUsers':
        return verify_users(body)
    elif body['action']=='loginUsers':
        return login_users(body)    
    elif body['action']=='resendCode':
        return resend_code(body)    
    elif body['action']=='forgotPassword':
        print("entering forgot password")
        return forgot_password(body)
    elif body['action']=='confirmResetPassword':
        print("entering confirm reset password")
        return confirm_forgot_password(body)        
    return send_response(400, 'Invalid action in request')
