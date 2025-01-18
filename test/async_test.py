import os
import asyncio
import dotenv
import boto3
from handlers.discord_request_handler import DiscordRequestHandler


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
    print(status)
    return status

async def send_ec2_status():
    discord_handler = DiscordRequestHandler()

    get_status_task = asyncio.create_task(get_ec2_status())
    post_message_task = asyncio.create_task(discord_handler.post_message('this is a pen'))

    await get_status_task
    await post_message_task


def main():
    asyncio.run(send_ec2_status())

if __name__=='__main__':
    main()
