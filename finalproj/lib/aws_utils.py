import boto3
import json
from lib.utils import user_hash

from lib.constants import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION
from lib.constants import S3_BUCKET


def get_sns_client():
    sns = boto3.client('sns',
                       aws_access_key_id=AWS_ACCESS_KEY_ID,
                       aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                       region_name=AWS_REGION)
    return sns


def get_s3_client():
    s3 = boto3.client('s3',
                       aws_access_key_id=AWS_ACCESS_KEY_ID,
                       aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                       region_name=AWS_REGION)
    return s3


def generate_topic_name(user_email):
    return "photos_notify_" + user_hash(user_email)


# Create a SNS topic for user to publish notifications
def create_sns_topic(user_email):
    sns = get_sns_client()
    topic = generate_topic_name(user_email)
    resp = sns.create_topic(Name=topic)
    return resp['TopicArn']


# Subscribe to a SNS topic
def subscribe_sns_topic(subscriber_email, target_user_email):
    sns = get_sns_client()
    topic_arn = create_sns_topic(target_user_email)
    sns.subscribe(TopicArn=topic_arn,
                  Protocol='email',
                  Endpoint=subscriber_email)


def list_subscriptions(user_email):
    topic_arn = create_sns_topic(user_email)
    sns = get_sns_client()
    resp = sns.list_subscriptions_by_topic(TopicArn=topic_arn)
    return resp['Subscriptions']

# Subscribe to a SNS topic
def unsubscribe_sns_topic(subscriber_email, target_user_email):
    sns = get_sns_client()
    subscriptions = list_subscriptions(target_user_email)
    for s in subscriptions:
        if s['Endpoint'] == subscriber_email:
            sns.unsubscribe(SubscriptionArn=s['SubscriptionArn'])
            return


def put_subscriber_list(email, content="[]"):
    key = user_hash(email) + "/subscribers.json"
    s3 = get_s3_client()
    s3.put_object(Bucket=S3_BUCKET,
                  Key=key,
                  Body=content)


def update_subscription(subscriber, target):
    s3 = get_s3_client()
    key = user_hash(target) + "/subscribers.json"
    subscriber_topic = create_sns_topic(subscriber)
    resp = s3.get_object(Bucket=S3_BUCKET,
                         Key=key)
    data = json.loads(resp['Body'].read())
    data.append(subscriber_topic)
    data = list(set(data))
    put_subscriber_list(target, json.dumps(data))
