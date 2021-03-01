import json
import boto3
import logging
import urllib3
import os
http = urllib3.PoolManager()

logger = logging.getLogger(__name__)
logging.getLogger().setLevel(logging.INFO)

logging.basicConfig(
    format='%(levelname)s %(threadName)s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d:%H:%M:%S',
    level=logging.INFO
)

SUCCESS = "SUCCESS"
FAILED = "FAILED"

ec2_client = boto3.client('ec2')

def lambda_handler(event, context):
    logger.info('Event: %s' % json.dumps(event))
    responseData={}
    try:
        if event['RequestType'] == 'Delete':
            print("Request Type:",event['RequestType'])
            print("Delete Request - Nothing to delete")
        elif event['RequestType'] == 'Create' or event['RequestType'] == 'Update':
            print("Request Type:",event['RequestType'])
            GETNAMES1=event['ResourceProperties']['GETNAMES1']
            GetSubNames1=get_ids(GETNAMES1)
            
            try:
                    tag_creation = ec2_client.create_tags(
                        Resources = 
                            GetSubNames1,
                        Tags = [
                            {
                                'Key':'BackupRetention',
                                'Value':'15days'
                            }
                        ]
                    )
                    tag_creation = ec2_client.create_tags(
                        Resources = 
                            GetSubNames1,
                        Tags = [
                            {
                                'Key':'costcenter',
                                'Value':'financial'
                            }
                        ]
                    )
            except Exception as ex:
                raise
            
            responseData={'GetSubNames1':GetSubNames1}
            print("Sending CFN")
        responseStatus = 'SUCCESS'
    except Exception as e:
        print('Failed to process:', e)
        responseStatus = 'FAILURE'
        responseData = {'Failure': 'Check Logs.'}
    send(event, context, responseStatus, responseData)

def get_ids(GETNAMES1):
    
    response = ec2_client.describe_instances()
    instances = response['Reservations']
    
    instance_ids = []
    for instance in instances:
        instance_ids.append(instance['Instances'][0]['InstanceId'])
    
    return instance_ids
    
def send(event, context, responseStatus, responseData, physicalResourceId=None, noEcho=False):
    responseUrl = event['ResponseURL']
    print(responseUrl)
    responseBody = {'Status': responseStatus,
                    'Reason': 'See the details in CloudWatch Log Stream: ' + context.log_stream_name,
                    'PhysicalResourceId': physicalResourceId or context.log_stream_name,
                    'StackId': event['StackId'],
                    'RequestId': event['RequestId'],
                    'LogicalResourceId': event['LogicalResourceId'],
                    'Data': responseData}
    json_responseBody = json.dumps(responseBody)
    print("Response body:\n" + json_responseBody)
    headers = {
        'content-type' : '',
        'content-length' : str(len(json_responseBody))
    }
    try:
        response = http.request('PUT', responseUrl, headers=headers, body=json_responseBody)
        print("Status code:", response.status)
    except Exception as e:
        print("send(..) failed executing http.request(..):", e)