import argparse
import boto3
import requests
from os import getenv
from dotenv import load_dotenv

load_dotenv()


def aws_client(param, region=getenv("aws_region_name")):
    return boto3.client(param,
                        aws_access_key_id=getenv("aws_access_key_id"),
                        aws_secret_access_key=getenv("aws_secret_access_key"),
                        aws_session_token=getenv("aws_session_token"),
                        region_name=region)


parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(dest="command", help="Available commands")

ec2_parser = subparsers.add_parser("ec2")
ec2_parser.add_argument("-launch_instance",
                        action="store_true",
                        help="launch instance")
ec2_parser.add_argument("-ssh_my_ip", action="store_true", help="add ssh access in my ip")
ec2_parser.add_argument("-security_group_id", type=str, help="security group id")

s3_parser = subparsers.add_parser("s3")
s3_parser.add_argument("-organize",
                       action="store_true",
                       help="organize s3 objects")
s3_parser.add_argument("-upload_file",
                       type=str,
                       help="upload file to s3 bucket")
s3_parser.add_argument("-bucket", type=str, help="bucket name")

rds_parser = subparsers.add_parser("rds")
rds_parser.add_argument("-new_pass", type=str)
rds_parser.add_argument("-dbInstanceId", type=str)

vpc_parser = subparsers.add_parser("vpc")
vpc_parser.add_argument("-vpc", type=str, help="vpc id")
vpc_parser.add_argument("-create_private_subnet", type=str, help="cidr_block")

args = parser.parse_args()


def organize_objects(client, bucket_name):
    counter = {}
    response = client.list_objects_v2(Bucket=bucket_name)
    if response is not None:
        contents = response.get('Contents', [])
        for obj in contents:
            key = obj['Key']
            if '.' in key:
                extension_name = key.split(".")[-1]
                if not counter.get(extension_name):
                    counter[extension_name] = 1
                    destination_key = extension_name + '/' + key
                    client.put_object(Bucket=bucket_name, Key=extension_name + '/')
                    client.copy_object(Bucket=bucket_name, CopySource={'Bucket': bucket_name, 'Key': key},
                                       Key=destination_key)
                    client.delete_object(Bucket=bucket_name, Key=key)
                else:
                    counter[extension_name] += 1
                    destination_key = extension_name + '/' + key
                    client.copy_object(Bucket=bucket_name, CopySource={'Bucket': bucket_name, 'Key': key},
                                       Key=destination_key)
                    client.delete_object(Bucket=bucket_name, Key=key)
    print(counter)


def update_rds_pass(rds_cient, identifer, password):
    rds_cient.modify_db_instance(DBInstanceIdentifier=identifer, MasterUserPassword=password)


def run_ec2(client):
    client.run_instances(
        BlockDeviceMappings=[
            {
                "DeviceName": "/dev/sda1",
                "Ebs": {
                    "DeleteOnTermination": True,
                    "VolumeSize": 10,
                    "VolumeType": "gp2",
                    "Encrypted": False
                },
            },
        ],
        ImageId="ami-053b0d53c279acc90",
        InstanceType="t2.micro",
        MaxCount=1,
        MinCount=1,
        Monitoring={"Enabled": True},
        UserData="""#!/bin/bash
echo "Hello I am from user data" > info.txt
""",
        InstanceInitiatedShutdownBehavior="stop",
    )


def upload_file(client, bucket_name, file):
    with open(file, 'rb') as f:
        client.upload_fileobj(f, bucket_name, file)


def create_subnet(client, vpc_id, cidr_block):
    response = client.create_subnet(VpcId=vpc_id, CidrBlock=cidr_block)
    subnet = response.get("Subnet")
    print(subnet)


def add_ssh_access_sg(sg_id, ip):
    ip = f"{ip}/32"

    response = ec2_client.authorize_security_group_ingress(
        CidrIp=ip,
        FromPort=22,
        GroupId=sg_id,
        IpProtocol='tcp',
        ToPort=22,
    )
    if response.get("Return"):
        print("Rule added successfully")


if args.command == "s3":
    s3_client = aws_client("s3")
    if args.organize:
        organize_objects(s3_client, args.bucket)
    elif args.upload_file:
        upload_file(s3_client, args.bucket, args.upload_file)
elif args.command == "ec2":
    ec2_client = aws_client("ec2")
    if args.launch_instance:
        run_ec2(ec2_client)
    elif args.ssh_my_ip:
        ip_address = requests.get("https://ident.me").text
        add_ssh_access_sg(args.security_group_id, ip_address)
elif args.command == "rds":
    client = aws_client("rds")
    if len(args.new_pass) >= 4 and args.dbInstanceId:
        update_rds_pass(client, args.dbInstanceId, args.new_pass)
elif args.command == "vpc":
    ec2_client = aws_client("ec2")
    create_subnet(ec2_client, args.vpc, args.create_private_subnet)