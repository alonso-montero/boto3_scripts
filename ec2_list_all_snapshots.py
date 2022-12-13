import boto3
import argparse

def parser() -> dict:
    parser = argparse.ArgumentParser()
    parser.add_argument('--profile', type=str, required=True)
    parser.add_argument('--region', type=str, required=True)

    return parser.parse_args()

def main():
    args = parser()
    boto3.setup_default_session(profile_name=args.profile, region_name=args.region)
    ec2 = boto3.client('ec2')
    response = ec2.describe_snapshots()
    for r in response['Snapshots']:
        print(r['SnapshotId'],',',r['StartTime'],',',r['VolumeSize'],',',r['Description'])

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f'Unexpected error: {e}')
    