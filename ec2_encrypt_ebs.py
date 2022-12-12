import boto3
import argparse
import sys

def parser() -> dict:
    parser = argparse.ArgumentParser()
    parser.add_argument('--profile', type=str, required=True)
    parser.add_argument('--region', type=str, required=True)
    #parser.add_argument('--volume', type=str, required=True)
    parser.add_argument('--instance', type=str, required=True)
    parser.add_argument('--kms', type=str, required=True)
    return parser.parse_args()

def get_instance_volumes(instanceId: str) -> list:
    volume_list=[]
    ec2 = boto3.client('ec2')
    response = ec2.describe_volumes(Filters=[
        {
            'Name': 'attachment.instance-id',
            'Values': [
                instanceId,
            ]
        },
    ])
    for v in response['Volumes']:
        volume_list.append(v['VolumeId'])

    return volume_list

def get_instance_az(instanceId: str) -> str:
    ec2 = boto3.client('ec2')
    response = ec2.describe_instances()
    for r in response['Reservations']:
        for i in r['Instances']:
                if i["InstanceId"] == instanceId:
                    az= i["Placement"]["AvailabilityZone"]
    return az

def get_device(instanceId: str, volumeId: str) -> str:
    ec2 = boto3.client('ec2')
    response = ec2.describe_volumes(Filters=[
        {
            'Name': 'attachment.instance-id',
            'Values': [
                instanceId,
            ]
        },
    ])
    for v in response['Volumes']:
        for a in v['Attachments']:
            if a['VolumeId'] == volumeId:
                device = a['Device']
    return device

def is_encripted(VolumeId: str) -> bool:
    ec2 = boto3.client('ec2')
    response = ec2.describe_volumes(VolumeIds=[VolumeId])
    encryption_status = response['Volumes'][0]['Encrypted']
    return encryption_status

def create_volume_snapshot(instanceId: str, volumeId: str) -> str:
    description= 'Encryption snapshot for volume '+ volumeId + 'for instance ' + instanceId
    ec2 = boto3.client('ec2')
    response = ec2.create_snapshot(
        Description=description,
        VolumeId=volumeId,
    )
    return response['SnapshotId']

def snapshot_state(snapshotId: str) -> str:
    ec2 = boto3.client('ec2')
    response = ec2.describe_snapshots(
        SnapshotIds=[snapshotId]
    )
    return response['Snapshots'][0]['State']
    
def snapshot_progress(snapshotId: str) -> str:
    ec2 = boto3.client('ec2')
    response = ec2.describe_snapshots(
        SnapshotIds=[snapshotId]
    )
    return response['Snapshots'][0]['Progress']

def create_volume_from_snapshot(instanceId: str, snapshotId: str, kmsKeyId: str, instanceAz: str) -> str:
    print(instanceAz)
    ec2 = boto3.client('ec2')
    response = ec2.create_volume(AvailabilityZone=instanceAz,Encrypted=True,KmsKeyId=kmsKeyId,SnapshotId=snapshotId,VolumeType='gp3',)
    return response['VolumeId']

def detach_volume(instanceId: str, device: str, volumeId: str ):
    ec2 = boto3.client('ec2')
    response = ec2.detach_volume( Device=device,InstanceId=instanceId,VolumeId=volumeId)

def attach_volume(instanceId: str, device: str, volumeId: str ):
    ec2 = boto3.client('ec2')
    response = ec2.attach_volume( Device=device,InstanceId=instanceId,VolumeId=volumeId)

def stop_instance(instanceID: str):
    ec2 = boto3.client('ec2')
    response = ec2.stop()

def start_instance(instanceID: str):
    ec2 = boto3.client('ec2')
    response = ec2.start()

def get_volume_status(volumeId):
    ec2 = boto3.client('ec2')
    response = ec2.describe_volumes(VolumeIds=[volumeId])
    volume_state = response['Volumes'][0]['State']
    return volume_state

def main():
    args = parser()
    boto3.setup_default_session(profile_name=args.profile, region_name=args.region)
    instanceId=args.instance
    kms_key=args.kms
    print("Working on instance")
    print(instanceId)
    print("Instance Availability Zone:")
    print(get_instance_az(instanceId))
    print("Instance volumes:")
    number_of_volumes=len(get_instance_volumes(instanceId))
    volumes_list=get_instance_volumes(instanceId)
    print(volumes_list)
    print(number_of_volumes)
    for n in range(number_of_volumes):
        print("Working on volume")
        print(volumes_list[n-1])
        print(get_device(instanceId,volumes_list[n-1]))
        device=get_device(instanceId,volumes_list[n-1])
        print("Encryption status:")
        print(is_encripted(volumes_list[n-1]))
        if is_encripted(volumes_list[n-1]) == False:
    ##st    op instance before creating snapshot
    ##st    op_instance(instanceId)
            print("Creating volume snapshot")
            snapshotId = create_volume_snapshot(instanceId,volumes_list[n-1])
            while snapshot_state(snapshotId) != 'completed':
                print(snapshot_progress(snapshotId))
            print(snapshot_state(snapshotId))
            print("Creating volume from snapshot")
            new_volume_id=create_volume_from_snapshot(instanceId,snapshotId,kms_key,get_instance_az(instanceId))
            print("New volume created. This is the volume ID:")
            print(new_volume_id)
            print("Detaching old volume")
            detach_volume(instanceId, device ,volumes_list[n-1])
            print("Attaching new volume")
            while get_volume_status(new_volume_id) != 'available':
                print(get_volume_status(new_volume_id))
            print(get_volume_status(new_volume_id))
            attach_volume(instanceId, device ,new_volume_id)
    #start instance after snapshot is created
    ##start_instance(instanceId)
        else:
            print("Already encrypted")
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f'Unexpected error: {e}')
    