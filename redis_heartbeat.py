#!/usr/bin/env python3

import requests
import redis
import json
import time
import boto3
import os
import argparse


def sns_invoke(msg):
    sns = boto3.client('sns', region_name=awsRegion)
    response = sns.publish(
        TopicArn='arn:aws:sns:' + awsRegion + ':' + accountId + ':' + snsTopic,
        Message=msg,
    )


def redis_ping(url):
    fail_counter = 0
    try:
        r = redis.from_url(url)
        for i in range(3):
            if r.ping() == True:
                return True
            else:
                fail_counter = fail_counter + 1
            time.sleep(30)
    except Exception as e:
        print(e)
    if fail_counter == 3:
        return False


def get_connection_strings(deployment_id):
    response = requests.get(base_url + '/deployments/' + deployment_id, headers=headers)
    connections = response.json()["connection_strings"]["direct"]
    return connections


def get_alerts(deployment_id):
    response = requests.get(base_url + '/deployments/' + deployment_id + '/alerts/', headers=headers)
    print(response.json())


def get_redis_deployments():
    prod_deploys = []
    response = requests.get(base_url + '/deployments/', headers=headers)
    for deployment in response.json()["_embedded"]["deployments"]:
        deployment_item = {
            'Id': deployment['id'],
            'Name': deployment['name']
        }
        if 'prod' in deployment['name'] and deployment['type'] == 'redis':
            prod_deploys.append(deployment_item)

    return prod_deploys


#VARS Declaration
parser = argparse.ArgumentParser()
parser.add_argument(dest='apiToken')
parser.add_argument(dest='awsRegion')
parser.add_argument(dest='snsTopic')
parser.add_argument(dest='accountId')
args = parser.parse_args()
apiToken=args.apiToken
awsRegion=args.awsRegion
snsTopic=args.snsTopic
accountId=args.accountId
base_url = "https://api.compose.io/2016-07/"
headers = {
    'Content-Type': "application/json",
    'Authorization': "Bearer " + apiToken,
}


for deployment in get_redis_deployments():
    get_alerts(deployment['Id'])
    connections = get_connection_strings(deployment['Id'])
    for connection in connections:
        if redis_ping(connection) == False:
            sns_invoke(deployment['Name'] + ' ' + str(connection.split("@")[-1]) + ' is failing')
