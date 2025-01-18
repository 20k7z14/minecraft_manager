import os
import dotenv
import boto3

dotenv.load_dotenv()
region = os.getenv('EC2_REGION')
instances = os.getenv('EC2_INSTANCE_ID').split(',')
ec2 = boto3.client('ec2', region_name=region)


async def get_ec2_status():
    status = ec2.describe_instances(
        Filters=[
            {
                'Name': 'instance-id',
                'Values': instances
            }
        ]
    )["Reservations"][0]["Instances"][0]['State']['Name']
    return status
