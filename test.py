import json
from unittest import TestCase
from unittest.mock import patch, MagicMock

from omni_manager import CRConfig


class TestCRConfig(TestCase):
    @patch("omni_manager.Boto3Caller")
    def test_instantiate_crconfig(self, mock_boto3_caller):
        # Set up the mock chain: Boto3Caller.client("lambda").invoke(...)["Payload"].read().decode()
        mock_payload = MagicMock()
        mock_payload.read.return_value = json.dumps({"status": "ok"}).encode("utf-8")

        mock_lambda_client = MagicMock()
        mock_lambda_client.invoke.return_value = {"Payload": mock_payload}

        mock_boto3_caller.client.return_value = mock_lambda_client

        config = CRConfig(owner="owner1", requestor="req1", prod_id="prod1")

        self.assertIsInstance(config, CRConfig)
        mock_boto3_caller.client.assert_called_once_with("lambda")
