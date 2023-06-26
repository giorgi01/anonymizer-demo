import argparse
import boto3

def get_instance_status(db_identifier):
    rds = boto3.client('rds')
    try:
        response = rds.describe_db_instances(DBInstanceIdentifier=db_identifier)
        status = response['DBInstances'][0]['DBInstanceStatus']
        return status
    except Exception as e:
        print(f"Error retrieving status for RDS instance '{db_identifier}': {e}")
        return None

def stop_rds_instance(db_identifier):
    rds = boto3.client('rds')
    try:
        response = rds.stop_db_instance(DBInstanceIdentifier=db_identifier)
        print(f"RDS instance '{db_identifier}' is stopping...")
        print(response)
    except Exception as e:
        print(f"Error stopping RDS instance '{db_identifier}': {e}")

def start_rds_instance(db_identifier):
    rds = boto3.client('rds')
    try:
        response = rds.start_db_instance(DBInstanceIdentifier=db_identifier)
        print(f"RDS instance '{db_identifier}' is starting...")
        print(response)
    except Exception as e:
        print(f"Error starting RDS instance '{db_identifier}': {e}")

def reboot_rds_instance(db_identifier):
    rds = boto3.client('rds')
    try:
        response = rds.reboot_db_instance(DBInstanceIdentifier=db_identifier)
        print(f"RDS instance '{db_identifier}' is rebooting...")
        print(response)
    except Exception as e:
        print(f"Error rebooting RDS instance '{db_identifier}': {e}")

def main():
    parser = argparse.ArgumentParser(description="RDS instance control script")
    parser.add_argument("DBInstanceIdentifier", metavar="DBInstanceIdentifier", type=str, help="RDS DB instance identifier")
    parser.add_argument("-status", metavar="status", type=str, choices=["stop", "start", "reboot"], help="Operation to perform on the RDS instance")

    args = parser.parse_args()

    db_identifier = args.DBInstanceIdentifier
    desired_status = args.status

    current_status = get_instance_status(db_identifier)
    if current_status is None:
        return

    if current_status == desired_status:
        print(f"RDS instance '{db_identifier}' is already in '{desired_status}' status.")
        return

    if desired_status == "stop":
        stop_rds_instance(db_identifier)
    elif desired_status == "start":
        start_rds_instance(db_identifier)
    elif desired_status == "reboot":
        reboot_rds_instance(db_identifier)
    else:
        print("Invalid status option. Use 'stop', 'start', or 'reboot'.")

if __name__ == "__main__":
    main()
