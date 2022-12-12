#!/usr/bin/python3
# Check ssm agent by ec2 state.
import boto3
import argparse
import re

def ec2_get_info(instanceId: str) -> dict:
  client = boto3.client('ec2')
  filters = "InstanceIds"= [instanceId]
  paginator = client.get_paginator("describe_instances")
  for result in paginator.paginate(Filters= L[InstanceIds=[instanceId]):
    if 'Reservations' not in result:
      continue
    for instances in result["Reservations"]:
      for instance in instances["Instances"]:
        yield instance


def parser() -> dict:
  parser = argparse.ArgumentParser()
  parser.add_argument('--id', type=str, required=True)
  parser.add_argument('--profile', type=str,required=True)
  parser.add_argument('--region', type=str, required=True)
  return parser.parse_args()

def main():
  args = parser()
  boto3.setup_default_session(profile_name=args.profile, region_name=args.region)
  
  for instance in ec2_get_info(args.id):
    print(instance)

if __name__ == '__main__':
  try:
    main()
  except Exception as e:
    print(f'Unexpected error: {e}')
