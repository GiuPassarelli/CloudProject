import boto3, time
from botocore.exceptions import ClientError

# DELETANDO INSTANCIAS
def del_inst(ec2_resource):
	instance_dying = ec2_resource.instances.filter(
		Filters=[{'Name': 'tag:Name',
				'Values': ['Owner: Giulia']}]
	)
	for inst in instance_dying:
		print(inst)
		ec2_resource.instances.filter(InstanceIds=[inst.id]).terminate()
		inst.wait_until_terminated()
		print(inst.state)

# DELETANDO AUTO SCALLING
def del_as(ec2_as, AS_NAME):
	try:
		ec2_as.delete_auto_scaling_group(
			AutoScalingGroupName = AS_NAME,
			ForceDelete = True
		)
		response = ec2_as.describe_auto_scaling_groups(AutoScalingGroupNames=[AS_NAME])
		while response['AutoScalingGroups']:
			print("deletando AS")
			time.sleep(15)
			response = ec2_as.describe_auto_scaling_groups(AutoScalingGroupNames=[AS_NAME])
	except ClientError as e:
		print(e)

# DELETANDO LAUNCH CONFIGURATION
def del_lc(ec2_as, LC_NAME):
	try:
		ec2_as.delete_launch_configuration(LaunchConfigurationName = LC_NAME)

		response = ec2_as.describe_launch_configurations(LaunchConfigurationNames=[LC_NAME])
		while response['LaunchConfigurations']:
			print("deletando LC")
			time.sleep(15)
			response = ec2_as.describe_launch_configurations(LaunchConfigurationNames=[LC_NAME])
	except ClientError as e:
		print(e)

# DELETANDO LISTENER
def del_listener(ec2_lb, LB_NAME):
	try:
		load_balancers = ec2_lb.describe_load_balancers(Names=[LB_NAME])
		for lb in load_balancers['LoadBalancers']:
			listeners = ec2_lb.describe_listeners(LoadBalancerArn = lb['LoadBalancerArn'])
			for lis in listeners['Listeners']:
				ec2_lb.delete_listener(ListenerArn = lis['ListenerArn'])
				while listeners['Listeners']:
					print("deletando Listener")
					time.sleep(15)
					listeners = ec2_lb.describe_listeners(LoadBalancerArn = lb['LoadBalancerArn'])
	except ClientError as e:
		print(e)

# DELETANDO LOAD BALANCER
def del_lb(ec2_lb, LB_NAME):
	waiter = ec2_lb.get_waiter('load_balancers_deleted')

	try:
		load_balancers = ec2_lb.describe_load_balancers(Names=[LB_NAME])
		for lb in load_balancers['LoadBalancers']:
			ec2_lb.delete_load_balancer(LoadBalancerArn = lb['LoadBalancerArn'])
			waiter.wait(LoadBalancerArns=[lb['LoadBalancerArn']])
	except ClientError as e:
		print(e)

# DELETANDO TARGET GROUP
def del_tg(ec2_lb, TG_NAME):
	#waiter = ec2_lb.get_waiter('target_deregistered')
	try:
		target_groups = ec2_lb.describe_target_groups(Names=[TG_NAME])
		for tg in target_groups['TargetGroups']:
			ec2_lb.delete_target_group(TargetGroupArn = tg['TargetGroupArn'])
			while target_groups['TargetGroups']:
				print("deletando Target Group")
				time.sleep(15)
				target_groups = ec2_lb.describe_target_groups(Names=[TG_NAME])
			#waiter.wait(TargetGroupArn = tg['TargetGroupArn'])
	except ClientError as e:
		print(e)

# CRIANDO UM KEY PAIR
def create_key(ec2_client, KEY_NAME, filename):
	try:
		ec2_client.describe_key_pairs(KeyNames = [KEY_NAME])
		ec2_client.delete_key_pair(KeyName = KEY_NAME)
	except ClientError as e:
		print(e)

	response = ec2_client.create_key_pair(KeyName = KEY_NAME)
	f = open(filename, "w")
	f.write(response["KeyMaterial"])
	f.close()

# CRIANDO SECURITY GROUPS
def create_security_group(ec2_client, SECURITY_GROUP):
	try:
		ec2_client.delete_security_group(GroupName = SECURITY_GROUP)
	except ClientError as e:
		print(e)
	try:
		response = ec2_client.create_security_group(
			Description = 'Security group for giu cloud',
			GroupName = SECURITY_GROUP
		)
		security_group_id = response['GroupId']
		print('Security Group Created ', security_group_id)
	except ClientError as e:
		print(e)

	return security_group_id

# CRIANDO INSTANCIA
def create_instance(ec2_resource, ec2_client, ami, cmds, KEY_NAME, SECURITY_GROUP):
	instance = ec2_resource.create_instances(
		ImageId = ami,
		InstanceType = 't2.micro',
		KeyName = KEY_NAME,
		MaxCount = 1,
		MinCount = 1,
		UserData = cmds,
		SecurityGroups = [SECURITY_GROUP],
		TagSpecifications=[
			{
				'ResourceType': 'instance',
				'Tags': [
					{
						'Key': 'Name',
						'Value': 'Owner: Giulia'
					},
				]
			},
		]
	)

	id_instance = instance[0].id
	print(id_instance)
	instance = ec2_resource.Instance(id_instance)
	instance.wait_until_running()
	instance.load()
	print(instance.placement)
	print(instance.public_ip_address)
	waiter = ec2_client.get_waiter('instance_status_ok')
	waiter.wait(InstanceIds=[instance.id])

	return instance

#CRIANDO AMI
def create_ami(ec2_client, instance, AMI_NAME):
	describe_amis = ec2_client.describe_images(
		Filters=[
			{
				'Name': 'tag:Name',
				'Values': ['Owner: Giulia']
			},
		]
	)

	try:
		for ami in describe_amis["Images"]:
			ec2_client.deregister_image(ImageId = ami["ImageId"])
	except ClientError as e:
		print(e)

	ami_image = ec2_client.create_image(
		InstanceId = instance.id,
		Name = AMI_NAME,
	)

	ami_tags = ec2_client.create_tags(
		Resources=[
			ami_image['ImageId'],
		],
		Tags=[
			{
				'Key': 'Name',
				'Value': 'Owner: Giulia'
			},
		]
	)
	return ami_image

#CRIANDO LOAD BALANCER
def create_lb(ec2_lb, LB_NAME, security_group_id_LB):
	load_balancer = ec2_lb.create_load_balancer(
		Name = LB_NAME,
		Subnets = [
			'subnet-21328c0f',
			'subnet-adbffce7',
			'subnet-c551ed99',
			'subnet-a4c371c3',
			'subnet-0084453e',
			'subnet-4f9bed40',
		],
		SecurityGroups = [
			security_group_id_LB,
		],
		Tags = [
			{
				'Key': 'Name',
				'Value': 'Owner: Giulia'
			},
		]
	)
	return load_balancer

# CRIANDO TARGET GROUP
def create_tg(ec2_lb, load_balancer, TG_NAME):
	for lb in load_balancer['LoadBalancers']:
		ec2_lb.create_target_group(
			Name = TG_NAME,
			Protocol = 'HTTP',
			Port = 5000,
			TargetType = 'instance',
			VpcId = lb['VpcId']
		)

	target_group = ec2_lb.describe_target_groups(Names=[TG_NAME])

	for tg in target_group['TargetGroups']:
		ec2_lb.create_listener(
			LoadBalancerArn = lb['LoadBalancerArn'],
			Protocol = 'HTTP',
			Port = 80,
			DefaultActions=[{
				'Type': 'forward',
				'TargetGroupArn': tg['TargetGroupArn']
			}]
		)
	return target_group

# CRIANDO LAUNCH CONFIGURATION
def create_lc(ec2_as, LC_NAME, ami_image, KEY_NAME, security_group_id):
	ec2_as.create_launch_configuration(
		LaunchConfigurationName = LC_NAME,
		ImageId = ami_image['ImageId'],
		KeyName = KEY_NAME,
		SecurityGroups = [security_group_id],
		InstanceType = 't2.micro'
	)

# CRIANDO AUTO SCALLING GROUP
def create_as(ec2_as, target_group, AS_NAME, LC_NAME):
	for tg in target_group['TargetGroups']:
		ec2_as.create_auto_scaling_group(
			AutoScalingGroupName = AS_NAME,
			LaunchConfigurationName = LC_NAME,
			MinSize = 1,
			MaxSize = 5,
			AvailabilityZones = ['us-east-1a', 'us-east-1b', 'us-east-1c', 'us-east-1d', 'us-east-1e', 'us-east-1f'],
			TargetGroupARNs = [tg['TargetGroupArn']],
			HealthCheckGracePeriod = 300,
			Tags = [
				{
					'Key': 'Name',
					'Value': 'Owner: Giulia',
					'PropagateAtLaunch' : True
				},
			]
		)

# CRIANDO UMA POLICY PARA O ASG
def create_policy(ec2_lb, ec2_as, LB_NAME, TG_NAME, AS_NAME, POL_NAME):
	load_balancers = ec2_lb.describe_load_balancers(Names=[LB_NAME])
	lb = (load_balancers['LoadBalancers'][0]['LoadBalancerArn']).split("app")
	lb = "app" + lb[-1]

	target_groups = ec2_lb.describe_target_groups(Names=[TG_NAME])
	tg = (target_groups['TargetGroups'][0]['TargetGroupArn']).split("targetgroup")
	tg = "/targetgroup" + tg[-1]

	ec2_as.put_scaling_policy(
		AutoScalingGroupName = AS_NAME,
		PolicyName = POL_NAME,
		PolicyType = 'TargetTrackingScaling',
		TargetTrackingConfiguration={
			'PredefinedMetricSpecification': {
				'PredefinedMetricType': 'ALBRequestCountPerTarget',
				'ResourceLabel': lb + tg
			},
			'TargetValue': 3000.0
		}
	)

