import json
import os
import boto3
import requests
import dotenv

from datetime import datetime
from dateutil.relativedelta import relativedelta

dotenv.load_dotenv()
region = os.getenv('EC2_REGION')
instances = os.getenv('EC2_INSTANCE_ID').split(',')

ec2 = boto3.client('ec2', region_name=region)

def lambda_handler(event: dict, context: dict):
    try:
        # ヘッダーを小文字に統一
        headers = {k.lower(): v for k, v in event.get('headers', {}).items()}
        raw_body = event.get('body', '')

        # リクエストの検証
        signature = headers.get('x-signature-ed25519')
        timestamp = headers.get('x-signature-timestamp')

        if not signature or not timestamp:
            return {
                "statusCode": 401,
                "headers": {},
                "body": json.dumps({"error": "Missing signature or timestamp"}),
                "isBase64Encoded": False
            }

        if not verify(signature, timestamp, raw_body):
            return {
                "statusCode": 401,
                "headers": {},
                "body": "",
                "isBase64Encoded": False
            }

        # リクエストボディのパース
        req = json.loads(raw_body)

        # Pingリクエストの処理
        if req['type'] == 1:  # InteractionType.Ping
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"type": 1}),  # InteractionResponseType.Pong
                "isBase64Encoded": False
            }

        # コマンドの処理
        elif req['type'] == 2:  # InteractionType.ApplicationCommand
            action = req['data']['options'][0]['value']
            text = ""

            match action:
              case 'start':
                text = start_ec2()
                if text == False:
                    text = "Something went wrong. Please try again later."
                    raise Exception(text)
              case 'stop':
                text = stop_ec2()
              case 'status':
                status = get_ec2_status()

                match status:
                  case False:
                    text = f"instance ID:{instances[0]} is not found"
                    return {
                        "statusCode": 200,
                        "headers": {"Content-Type": "application/json"},
                        "body": json.dumps({
                            "type": 4,  # InteractionResponseType.ChannelMessageWithSource
                            "data": {
                                "content": text
                            }
                        }),
                        "isBase64Encoded": False
                    }
                  case 'stopped':
                      text = f"instance ID: {instances[0]} has stopped"
                  case 'pending':
                      text = f"instance ID: {instances[0]} has booted. Please waiting...."
                  case 'running' | 'stopping':
                      global_ip = fetch_public_ip()
                      text = f"instance ID: {instances[0]} with {fetch_public_ip()} is {status}."

              case 'cost':
                cost = get_cost()
                jpy = str(exchange_rate(cost))
                text = f"This month's cost is【{jpy} yen】"

            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({
                    "type": 4,  # InteractionResponseType.ChannelMessageWithSource
                    "data": {
                        "content": text
                    }
                }),
                "isBase64Encoded": False
            }

    except Exception as e:
        print(f"Error processing request: {e}")
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Internal server error"}),
            "isBase64Encoded": False
        }

def start_ec2():
  try:
    status = get_ec2_status()
    match status:
      case 'pending':
        text = f"instance ID : {instances[0]} have booted. Please waiting...."
      case 'running':
        public_ip  = fetch_public_ip()
        text = f"instance ID : {instances[0]} with {public_ip} have already started."
      case 'stopped':
        ec2.start_instances(InstanceIds=instances)
        text = f"instance ID : {instances[0]} started."
    return text

  except Exception as e:
    print(e)
    return False

def fetch_public_ip():
  try:
    response = ec2.describe_instances(
      Filters=[
        {
          'Name': 'instance-id',
          'Values': instances
        }
      ]
    )
    public_ip = response['Reservations'][0]['Instances'][0]['PublicIpAddress']
    return public_ip
  except Exception as e:
    print(e)
    return False

def stop_ec2():
  status = get_ec2_status()
  match status:
    case 'stopped':
      text = f"instance ID : {instances[0]} have already stopped."
    case 'stopping':
      text = f"instance ID : {instances[0]} haven't stopped yet."
    case 'running':
      ec2.stop_instances(InstanceIds=instances)
      text = f"instance ID : {instances[0]} with {global_ip} have shut down...."
  return text
  
def get_ec2_status():
  status = ec2.describe_instances(
    Filters=[
      {
        'Name': 'instance-id',
        'Values': instances
      }
    ]
  )["Reservations"][0]["Instances"][0]['State']['Name']
  return status

def get_cost():
  ce = boto3.client('ce')
  response = ce.get_cost_and_usage(
    TimePeriod={
      'Start': datetime.now().strftime("%Y-%m-01"),
      'End' : (datetime.now()+relativedelta(months=1)).strftime("%Y-%m-01"),
    },
    Granularity='MONTHLY',
    Metrics= [
      'UnblendedCost'
    ]
  )
  return response['ResultsByTime'][0]['Total']['UnblendedCost']['Amount']

def exchange_rate(usd):
  url = "https://api.excelapi.org/currency/rate?pair=usd-jpy"
  response = requests.get(url)
  rate = response.json()
  jpy = float(usd) * float(rate)
  return int(jpy)
