import boto3
from botocore.exceptions import ClientError
import os, paramiko
from projeto_funcoes import *

ec2_client_2 = boto3.client('ec2', region_name = 'us-east-2')
ec2_resource_2 = boto3.resource('ec2', region_name = 'us-east-2')
ec2_client = boto3.client('ec2')
ec2_resource = boto3.resource('ec2')
ec2_lb = boto3.client('elbv2')
ec2_as = boto3.client('autoscaling')

KEY_NAME_OHIO = 'giulia_OHIO'
SECURITY_GROUP_DB = 'giu_db'
SECURITY_GROUP_OH = 'giu_ohio'
KEY_NAME = 'giulia_projeto'
SECURITY_GROUP1 = 'APS_giu'
SECURITY_GROUP_LB = 'SG_LB_giu'
SECURITY_GROUP_RD = 'SG_RD_giu'
AMI_NAME = 'AMI_giu_projeto'
LB_NAME = 'LB-giu-projeto'
TG_NAME = 'TG-giu-projeto'
LC_NAME = 'LC-giu-projeto'
AS_NAME = 'AS-giu-projeto'
POL_NAME = 'POL-giu-projeto'

PublicIp_NV = '3.219.122.232'
PublicIp_OHIO = '18.188.197.225'

# DELETANDO INSTANCIAS
del_inst(ec2_resource_2)
del_inst(ec2_resource)

# DELETANDO AUTO SCALLING
del_as(ec2_as, AS_NAME)

# DELETANDO LAUNCH CONFIGURATION
del_lc(ec2_as, LC_NAME)

# DELETANDO LISTENER
del_listener(ec2_lb, LB_NAME)

# DELETANDO LOAD BALANCER
del_lb(ec2_lb, LB_NAME)

# DELETANDO TARGET GROUP
del_tg(ec2_lb, TG_NAME)

# CRIANDO UMA KEY PAIR
waiter = ec2_client.get_waiter('key_pair_exists')
create_key(ec2_client_2, KEY_NAME_OHIO, "ohio_key.pem")
create_key(ec2_client, KEY_NAME, "projeto_key.pem")
waiter.wait(KeyNames=[KEY_NAME])

# CRIANDO SECURITY GROUPS
security_group_id = create_security_group(ec2_client, SECURITY_GROUP1)
security_group_id_LB = create_security_group(ec2_client, SECURITY_GROUP_LB)
security_group_id_RD =  create_security_group(ec2_client, SECURITY_GROUP_RD)

security_group_id_db = create_security_group(ec2_client_2, SECURITY_GROUP_DB)
security_group_id_oh = create_security_group(ec2_client_2, SECURITY_GROUP_OH)

# CRIANDO INSTANCIAS
cmds = """#! /bin/bash
git clone https://github.com/GiuPassarelli/Service-REST
sh /Service-REST/install.sh
"""

cmds_RD = """#! /bin/bash
git clone https://github.com/GiuPassarelli/Service-REST
sh /Service-REST/install.sh
"""

instance = create_instance(ec2_resource, ec2_client, 'ami-04b9e92b5572fa0d1', cmds, KEY_NAME, SECURITY_GROUP1)
IP_privado = instance.private_ip_address
print("Private IP: ", IP_privado)
instance_RD = create_instance(ec2_resource, ec2_client, 'ami-04b9e92b5572fa0d1', cmds_RD, KEY_NAME, SECURITY_GROUP_RD)
IP_privado_RD = instance_RD.private_ip_address
print("Private IP rd: ", IP_privado_RD)

#OHIO

cmds_db = """#! /bin/bash
git clone https://github.com/GiuPassarelli/Service-REST
sh /Service-REST/install.sh
sudo snap install couchdb
sudo cp /Service-REST/local.ini /var/snap/couchdb/current/etc -f
sudo reboot
"""
instancia_db = create_instance(ec2_resource_2, ec2_client_2, 'ami-0d5d9d301c853a04a', cmds_db, KEY_NAME_OHIO, SECURITY_GROUP_DB)
IP_privado_db = instancia_db.private_ip_address
print("Private IP db: ", IP_privado_db)

cmds_elastic_OH = """#! /bin/bash
git clone https://github.com/GiuPassarelli/Service-REST
sh /Service-REST/install.sh
"""
instancia_oh = create_instance(ec2_resource_2, ec2_client_2, 'ami-0d5d9d301c853a04a', cmds_elastic_OH, KEY_NAME_OHIO, SECURITY_GROUP_OH)
IP_privado_oh = instancia_oh.private_ip_address
print("Private IP OHIO: ", IP_privado_oh)

# ASSOCIANDO ELASTIC IP
ec2_client_2.associate_address(
    InstanceId = instancia_oh.id,
    PublicIp = PublicIp_OHIO
)
ec2_client.associate_address(
    InstanceId = instance_RD.id,
    PublicIp = PublicIp_NV
)

# LIBERANDO AS PORTAS
try:
    # OHIO
	ec2_client_2.authorize_security_group_ingress(
		GroupId = security_group_id_db,
		IpPermissions = [
			{'IpProtocol': 'tcp',
				'FromPort': 5000,
				'ToPort': 5000,
				'IpRanges': [{'CidrIp': IP_privado_oh + '/32'}]},
            {'IpProtocol': 'tcp',
				'FromPort': 22,
				'ToPort': 22,
				'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}
		]
	)
	ec2_client_2.authorize_security_group_ingress(
        GroupId = security_group_id_oh,
		IpPermissions = [
			{'IpProtocol': 'tcp',
				'FromPort': 22,
				'ToPort': 22,
				'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
            {'IpProtocol': 'tcp',
				'FromPort': 5000,
				'ToPort': 5000,
				'IpRanges': [{'CidrIp': PublicIp_NV + '/32'}]},
		]
	)
	# NORTH VIRGINIA
	ec2_client.authorize_security_group_ingress(
		GroupId = security_group_id,
		IpPermissions = [
			{'IpProtocol': 'tcp',
				'FromPort': 22,
				'ToPort': 22,
				'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
			{'IpProtocol': 'tcp',
				'FromPort': 5000,
				'ToPort': 5000,
				'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}
		]
	)
	ec2_client.authorize_security_group_ingress(
		GroupId = security_group_id_LB,
		IpPermissions = [
			{'IpProtocol': 'tcp',
				'FromPort': 80,
				'ToPort': 80,
				'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
		]
	)
	ec2_client.authorize_security_group_ingress(
		GroupId = security_group_id_RD,
		IpPermissions = [
			{'IpProtocol': 'tcp',
				'FromPort': 22,
				'ToPort': 22,
				'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
            {'IpProtocol': 'tcp',
				'FromPort': 5000,
				'ToPort': 5000,
				'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
		]
	)
except ClientError as e:
    print(e)

# CRIANDO O BANCO DE DADOS NA INSTANCIA BD
try:
    prk_client = paramiko.SSHClient()
    prk_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    key = paramiko.RSAKey.from_private_key_file("./ohio_key.pem")
    prk_client.connect(hostname = PublicIp_OHIO, username="ubuntu", pkey=key)

    cmd = "sudo tmux new -d -s execution 'export IPDB={};python3 /Service-REST/redirect.py'".format(IP_privado_db)

    # Execute a command(cmd) after connecting/ssh to an instance
    stdin, stdout, stderr = prk_client.exec_command(cmd)
    print (stdout.read())

    # close the client connection once the job is done
    prk_client.close()
except ClientError as e:
    print (e)

# REDIRECIONANDO
try:
    prk_client = paramiko.SSHClient()
    prk_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    key = paramiko.RSAKey.from_private_key_file("./projeto_key.pem")
    prk_client.connect(hostname = instance.public_ip_address, username="ubuntu", pkey=key)

    cmd = "sudo tmux new -d -s execution 'export IPNEXT={};python3 /Service-REST/servidor.py'".format(IP_privado_RD)

    # Execute a command(cmd) after connecting/ssh to an instance
    stdin, stdout, stderr = prk_client.exec_command(cmd)
    print (stdout.read())

    # close the client connection once the job is done
    prk_client.close()
except ClientError as e:
    print (e)

try:
    prk_client = paramiko.SSHClient()
    prk_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    key = paramiko.RSAKey.from_private_key_file("./projeto_key.pem")
    prk_client.connect(hostname = instance_RD.public_ip_address, username="ubuntu", pkey=key)

    cmd = "sudo tmux new -d -s execution 'export IPNEXT={};python3 /Service-REST/servidor.py'".format(PublicIp_OHIO)

    # Execute a command(cmd) after connecting/ssh to an instance
    stdin, stdout, stderr = prk_client.exec_command(cmd)
    print (stdout.read())

    # close the client connection once the job is done
    prk_client.close()
except ClientError as e:
    print (e)

#CRIANDO AMI
ami_image = create_ami(ec2_client, instance, AMI_NAME)

#CRIANDO LOAD BALANCER
load_balancer = create_lb(ec2_lb, LB_NAME, security_group_id_LB)

# CRIANDO TARGET GROUP
target_group = create_tg(ec2_lb, load_balancer, TG_NAME)

# CRIANDO LAUNCH CONFIGURATION
create_lc(ec2_as, LC_NAME, ami_image, KEY_NAME, security_group_id)

# CRIANDO AUTO SCALLING GROUP
create_as(ec2_as, target_group, AS_NAME, LC_NAME)

# CRIANDO UMA POLICY PARA O ASG
create_policy(ec2_lb, ec2_as, LB_NAME, TG_NAME, AS_NAME, POL_NAME)

# ec2_resource.instances.filter(InstanceIds=[instance.id]).terminate()
# instance.wait_until_terminated()
# print(instance.id)
