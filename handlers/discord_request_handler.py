import os

import requests
import dotenv

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.exceptions import InvalidSignature

class DiscordRequestHandler:
    def __init__(self):
        dotenv.load_dotenv()
        self.APPLICATION_PUBLIC_KEY = os.getenv('PUBLIC_KEY')
        self.BOT_TOKEN = os.getenv('BOT_TOKEN')
        env = os.getenv('ENV')
        match env:
            case "prod":
                self.CH_ID = os.getenv('PROD_DISCORD_SERVER_ID')
            case "dev":
                self.CH_ID = os.getenv('DEV_DISCORD_SERVER_ID')

    def verify(self, signature: str, timestamp: str, body: str) -> bool:
        try:
            # 公開鍵の16進数文字列をバイトに変換
            public_key_bytes = bytes.fromhex(self.APPLICATION_PUBLIC_KEY)

            # 公開鍵オブジェクトの作成
            public_key = ed25519.Ed25519PublicKey.from_public_bytes(public_key_bytes)

            # 検証対象のメッセージを作成
            message = f"{timestamp}{body}".encode()

            # 署名をバイトに変換
            signature_bytes = bytes.fromhex(signature)

            # 署名を検証
            public_key.verify(signature_bytes, message)
            return True

        except (ValueError, InvalidSignature) as e:
            print(f"Failed to verify request: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error during verification: {e}")
            return False

    async def post_message(self,message) -> None:
        url = f"https://discord.com/api/channels/{self.CH_ID}/messages"
        headers = {
            "Authorization": f"Bot {self.BOT_TOKEN}",
            "Content-Type": "application/json"
        }
        # 送信内容
        payload = {
            "content": message
        }
        # POSTリクエストを送信
        requests.post(url, json=payload, headers=headers)


