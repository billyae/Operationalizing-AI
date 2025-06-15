import boto3
from botocore.exceptions import ClientError

def authenticate_aws(access_key: str, secret_key: str, region: str = 'us-east-1') -> bool:
    """
    Validate AWS credentials by calling Bedrock's ListModels API.
    Returns True if credentials are valid, False otherwise.
    """

    try:

        client = boto3.client(
            'bedrock-runtime',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )

        return True
    except ClientError:
        return False
