import json
import boto3
import logging
import urllib3
import os
http = urllib3.PoolManager()

logger = logging.getLogger(__name__)
logging.getLogger().setLevel(logging.INFO)

SUCCESS = "SUCCESS"
FAILED = "FAILED"

client = boto3.client('ec2')
vpcid = os.environ['VPCID']
accountid = os.environ['ACCOUNTID']

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
            
            sts_client = boto3.client('sts')

            response = sts_client.assume_role(
                RoleArn='arn:aws:iam::'+accountid+':role/AWSControlTowerExecution',
                RoleSessionName='assume_role_session'
            )
            
            remoteresource = boto3.resource('ec2',
                    aws_access_key_id=response['Credentials']['AccessKeyId'],
                    aws_secret_access_key=response['Credentials']['SecretAccessKey'],
                    aws_session_token=response['Credentials']['SessionToken']
            )

            output = GetSubNames1
            try:
                    for addtags in output:
                        names = (addtags[0])
                        subnetids = (addtags[1])
                        subnet = remoteresource.Subnet(subnetids)
                        subnet.create_tags(
                            Tags=[
                                {
                                    'Key': 'Name',
                                    'Value': names
                                },
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

    response = client.describe_subnets(
        Filters=[ {
                'Name': 'vpc-id',
                'Values': [vpcid]},
                {
                'Name': 'tag:IsUsedForDeploy',
                'Values': ['True']}
        ]
    )

    tags = []
    for tag in response['Subnets']:
        for value in tag['Tags']:
            if value['Key'] == 'Name':
                tags.append(value['Value'])

    subnets = []
    for subnetids in response['Subnets']:
        subnets.append(subnetids['SubnetId'])

    output=[(tags[i],subnets[i]) for i in range(0,len(tags))]
    
    return output
    
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