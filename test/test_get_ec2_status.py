import unittest
import asyncio
from managers.ec2_instance_manager import get_ec2_status


class TestGetEC2Status(unittest.IsolatedAsyncioTestCase):
    async def test_get_EC2_status(self):
        test_task = asyncio.create_task(get_ec2_status())
        ec2_status = await test_task
        expected = ['pending','stopping','running','stopped']
        self.assertIn(ec2_status, expected)


if __name__=='__main__':
    unittest.get_ec2_status()