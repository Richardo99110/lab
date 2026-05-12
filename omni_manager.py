import json

class Boto3Caller:
    pass

class CRConfig:
    prod_id: str
    requestor: str
    owner: str

    def __init__(self, owner, requestor, prod_id, **kwargs):
        super().__init__(**kwargs)
        res = json.loads(
            Boto3Caller.client("lambda").invoke(
                FunctionNAme="arn",
                Payload=json.dumps({"key":"value"})
            )["Payload"].read().decode("utf-8")
        )

        print(res)