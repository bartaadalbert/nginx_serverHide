#!/usr/bin/env python3


import sys, getopt, os, subprocess
from os.path import exists as file_exists
from godaddypy import Client, Account
import digitalocean
import tldextract
import random
import time
import paramiko
from paramiko.ssh_exception import BadHostKeyException, AuthenticationException, SSHException, NoValidConnectionsError
import nginx
from colorama import Fore, Style

# Define constants at the top of the script
ENV_NAME = 'envgdd_do'
ENV_PATH = f'{ENV_NAME}/bin/python3'

def show_error(message):
    print(f"{Fore.RED}{message}{Style.RESET_ALL}")

def show_success(message):
    print(f"{Fore.GREEN}{message}{Style.RESET_ALL}")

def show_info(message):
    print(f"{Fore.LIGHTYELLOW_EX}{message}{Style.RESET_ALL}")
# Check python3
try:
    python_version = subprocess.check_output(['python3', '--version'])
    show_success(python_version.decode('utf-8'))
except FileNotFoundError:
    show_info('python3 is not installed. Installing now...')
    try:
        subprocess.check_call(['sudo', 'apt', 'update'])
        subprocess.check_call(['sudo', 'apt', 'install', 'python3', '-y'])
        python_version = subprocess.check_output(['python3', '--version'])
        show_success(f'python3 installed successfully. {python_version.decode("utf-8")}')
    except subprocess.CalledProcessError:
        show_error('Could not install python3. Please check your internet connection or permissions.')
        sys.exit(1)

# Check pip3
try:
    pip_version = subprocess.check_output(['pip3', '--version'])
    # show_success(pip_version.decode('utf-8'))
except FileNotFoundError:
    show_info('pip3 is not installed. Installing now...')
    try:
        subprocess.check_call(['sudo', 'apt', 'update'])
        subprocess.check_call(['sudo', 'apt', 'install', 'python3-pip', '-y'])
        pip_version = subprocess.check_output(['pip3', '--version'])
        show_success(f'pip3 installed successfully. {pip_version.decode("utf-8")}')
    except subprocess.CalledProcessError:
        show_error('Could not install pip3. Please check your internet connection or permissions.')
        sys.exit(1)

def create_virtual_environment():
    # Check if python3-venv is installed
    try:
        subprocess.check_call(['apt', 'list', 'python3-venv'], stdout=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        show_error('python3-venv is not installed. Installing now...')
        try:
            subprocess.check_call(['sudo', 'apt', 'install', 'python3-venv', '-y'])
            show_success('python3-venv installed successfully.')
        except subprocess.CalledProcessError:
            show_error('Could not install python3-venv. Please check your internet connection or permissions.')
            sys.exit(1)
    # Create a virtual environment
    try:
        subprocess.check_call(['python3', '-m', 'venv', ENV_NAME])
        show_success('Python environment created successfully.')
    except subprocess.CalledProcessError:
        show_error('Could not create a Python environment. Please check your permissions.')
        sys.exit(1)
        
def activate_virtual_environment():
    # Activate the virtual environment
    activate_env_path = os.path.join(os.getcwd(), ENV_PATH)
    activate_command = f'bash -c "source {activate_env_path} && pip3install -r requirements.txt"'
    try:
        subprocess.check_call(activate_command, shell=True)
        show_success('Virtual environment activated and requirements installed successfully.')
    except subprocess.CalledProcessError:
        show_error('Could not activate the virtual environment or install requirements. Please check your permissions or the contents of requirements.txt.')
        sys.exit(1)

# Construct the path to the Python environment
env_path = os.path.join(os.getcwd(), ENV_PATH)

# Check python environment path
if not os.path.exists(env_path):
    show_info('Python environment not found. Creating one now...')
    create_virtual_environment()
    activate_virtual_environment()

def read_keys(file_name):
    keys = {}
    # If the file does not exist, create it with default values
    if not file_exists(file_name):
        with open(file_name, 'w') as f:
            f.write("GDD_PUBLIC_KEY=GDD_PUBLIC_KEY\n")
            f.write("GDD_SECRET_KEY=GDD_SECRET_KEY\n")
            f.write("DO_TOKEN=DO_TOKEN\n")
        show_info(f"{file_name} created with default values. Please edit the file with actual values.")
        exit(1)
    
    # If the file exists, read it and get the keys
    with open(file_name, 'r') as f:
        for line in f:
            key, value = line.strip().split('=')
            if key == value:  # Check if key is equal to value
                show_error(f"Invalid value for {key}. Please set a valid value.")
                exit(1)
            keys[key] = value
    return keys

keys = read_keys('keys.txt')

GDD_PUBLIC_KEY = keys.get('GDD_PUBLIC_KEY')
GDD_SECRET_KEY = keys.get('GDD_SECRET_KEY')
DO_TOKEN = keys.get('DO_TOKEN')

def get_droplets():
   manager = digitalocean.Manager(token=DO_TOKEN)
   droplets = manager.get_all_droplets()
   for droplet in droplets:
     show_info(f"Droplet Name is: {droplet.name}")
     show_info(f"Droplet ID is: {droplet.id}")
     show_info(f"Droplet Netvork is: {droplet.networks['v4']}")
     print("\n")
   # print(droplets)
   return droplets

def get_sshkeys():
   manager = digitalocean.Manager(token=DO_TOKEN)
   keys = manager.get_all_sshkeys()
   for key in keys:
     show_info(f"SSH Key ID is: {key.id}")
     show_info(f"SSH Key Name is: {key.name}")
     show_info("\n")
   return keys

def get_droplet_ip(droplet):
   ip=None
   for net in droplet.networks['v4']:
      if net['type'] == 'private':
            private_ip_address = net['ip_address']
      if net['type'] == 'public':
            ip = net['ip_address']
   return ip


def get_domains():
   my_acct = Account(api_key=GDD_PUBLIC_KEY, api_secret=GDD_SECRET_KEY)
   client = Client(my_acct)
   domains=client.get_domains()
   show_info(domains)
   return domains

def read_file(readfor):
   myvars = {}
   if not file_exists(readfor):
      show_error("invalid file given")
      return myvars
   with open(readfor) as myfile:
    for line in myfile:
        name, value = line.partition(" ")[::2]
        myvars[name.strip()] = value.replace("\n","")
   return myvars

def field_check(checkdict):
        keys=[
         'domain_name',
         'droplet_name',
         'nginx_conf_file'
        ]
        if all(key in checkdict for key in keys):
            return True
        return False
def disconnect(self):
      """Close SSH connection."""
      if self.connection:
         self.client.close()

def main(argv):
   arguments=read_file(argv[0])
   #We store our arguments to a file with space seperated
   if not arguments:
      show_error("Empty content")
      show_error("Try python3 gdd_do.py -h")
      return 
   #Check if all needed argumants are added to file
   if not field_check(arguments):
      show_error("Not all key set (domain_name,droplet_name,nginx_conf_file)")
      show_error("Try python3 gdd_do.py -h")
      return
   domain_name=arguments['domain_name']
   droplet_name=arguments['droplet_name']
   nginx_file=arguments['nginx_conf_file']
   #Create a GDD connection and get the domains list
   my_acct = Account(api_key=GDD_PUBLIC_KEY, api_secret=GDD_SECRET_KEY)
   client = Client(my_acct)
   domains=client.get_domains()
   #Try to extract the given domain 
   no_cache_extract = tldextract.TLDExtract(cache_dir=False)
   purl=no_cache_extract(domain_name)
   #Get the purl domain name like an object and get the sub an suffix elements
   parseurl=purl.domain+"."+purl.suffix 
   if parseurl not in domains:
      show_error("Domain not found return")
      return
   if not purl.subdomain or purl.subdomain=="":
         a_record="@"
   else:
         a_record=purl.subdomain
   #Connect to DO server and get my droplets
   manager = digitalocean.Manager(token=DO_TOKEN)
   droplets = manager.get_all_droplets()
   #Get the ssh keys from DO
   keys = manager.get_all_sshkeys()
   for droplet in droplets:
      if droplet.name==droplet_name:
         droplet.destroy()
         show_info("the droplet was exist and dleleted try to create a new")
   #Call the droplet create method and get the public ip from this droplet
   ip=create_droplet(droplet_name,keys)
   # ip=None
   if ip is None:
      show_error("ip get error")
      return
   #Remoute run need to be True
   remoute_run=run_cmd(ip,nginx_file)
   if not remoute_run:
     show_error("something bad with remoute command executing")
     return
   #Check the domain subdomain exist or not
   exist_domain=client.get_records(parseurl, record_type='A', name=a_record) 
   if not exist_domain:
      show_success(f"Add new subdomain A record {a_record}")
      client.add_record(parseurl, {'data':ip,'name':a_record,'ttl':600, 'type':'A'})
   else:
      show_success(f"Update domain name A record {a_record}")
      client.update_record_ip(ip, parseurl,a_record, 'A')
      

#Droplet Create with name and ssh keys
def create_droplet(name,keys):
   regions=['ams3','fra1'] # You can add more regions
   droplet = digitalocean.Droplet(  token=DO_TOKEN,
                                    name=name,
                                    #region='ams3', # Amster
                                    #region = 'fra1', # Frankfurt
                                    region = random.choice(regions), #Random choice  from regions Amstredam and Frankfurt
                                    image='ubuntu-20-04-x64', # Ubuntu 20.04 x64
                                    size_slug='s-1vcpu-1gb',  # 1GB RAM, 1 vCPU
                                    ssh_keys=keys, #Automatic conversion
                                    backups=False)
   droplet.create()
   actions = droplet.get_actions()
   for action in actions:
     while action.load()!= False:
       show_info(f"The droplet status is {action.status}. Waiting for Droplet")
       if action.status == "completed":
          break
       time.sleep(3)
       
     show_success('Droplet ready')
   manager = digitalocean.Manager(token=DO_TOKEN)
   droplets = manager.get_all_droplets()
   ip=None
   for onedroplet in droplets:
      if onedroplet.name==name:
         ip=get_droplet_ip(onedroplet)
   return ip



def run_cmd(host_ip,nginx_file):
        hostname=host_ip
        hostfile=nginx_file
        hostkey="ssh -i ~/.ssh/id_rsa"
        copy_command='sudo cp /home/{} /etc/nginx/sites-available/{}'.format(nginx_file,nginx_file)
        remouve_command='sudo rm -rf /home/{}'.format(nginx_file)
        link_command='ln -s /etc/nginx/sites-available/{} /etc/nginx/sites-enabled/{}'.format(nginx_file,nginx_file)
        cmd_list=[
            'sudo apt-get update -y',
            'sudo apt-get upgrade -y',
            'sudo apt install nginx -y',
            copy_command,
            link_command,
            'systemctl restart nginx',
            remouve_command,
        ]
        show_info(cmd_list)
        myuser   = 'root'
        mySSHK   = '/root/.ssh/id_rsa'
        try:
            sshcon   = paramiko.SSHClient()  # will create the object
            sshcon.load_system_host_keys()
            sshcon.set_missing_host_key_policy(paramiko.AutoAddPolicy()) # no known_hosts error
            sshcon.connect(host_ip, username=myuser, key_filename=mySSHK,timeout=5000) # no passwd needed
            show_success("connected ssh")
            #Put the nginx config file to remoute server
            ftp_client=sshcon.open_sftp()
            ftp_client.put('{}'.format(nginx_file),'/home/{}'.format(nginx_file))
            #FTP connection close
            ftp_client.close()
            for command in cmd_list:
               # print command
               print("> " + command)
               # execute commands
               stdin, stdout, stderr = sshcon.exec_command(command)
               show_info(stdout.read().decode())
               err = stderr.read().decode()
               if err:
                  show_error(err)
        #Catch exceptions
        except paramiko.ssh_exception.NoValidConnectionsError as e:
            print(e)
            show_error('SSH transport is not ready')
            return run_cmd(hostname,hostfile)
        except AuthenticationException:
              show_error("Authentication failed, please verify your credentials: %s")
        except SSHException as sshException:
              show_error("Unable to establish SSH connection: %s" % sshException)
        except BadHostKeyException as badHostKeyException:
              show_error("Unable to verify server's host key: %s" % badHostKeyException)
        except BrokenPipeError:
         # Python flushes standard streams on exit; redirect remaining output
         # to devnull to avoid another BrokenPipeError at shutdown
            devnull = os.open(os.devnull, os.O_WRONLY)
            os.dup2(devnull, sys.stdout.fileno())
            sys.exit(1)  # Python exits with error code 1 on EPIPE
        finally:
              # Close SSH connection
              sshcon.close() 
        return True
def make_nginx_server(server_name="_",hide_server_ip="",ports=[80, 8000, 8080],app_location="/"):
   c = nginx.Conf()
   s = nginx.Server()
   # u = nginx.Upstream('php',
   #   nginx.Key('server', 'unix:/tmp/php-fcgi.socket')
	# ) 
   # c.add(u)
   for port in ports:
        s.add(nginx.Key('listen', port))
   s.add(
     nginx.Key('server_name', server_name),
     
     nginx.Location(app_location,
          nginx.Key('proxy_pass', 'http://{}:{}'.format(hide_server_ip,ports[0])),
          nginx.Key('proxy_http_version', "1.1"),
          nginx.Key('proxy_cache_bypass', "$http_upgrade"),
          nginx.Key('proxy_set_header Upgrade', "$http_upgrade"),
          nginx.Key('proxy_set_header Connection', "upgrade"),
          nginx.Key('proxy_set_header Hoste', "$host"),
          nginx.Key('proxy_set_header X-Real-IP', "$remote_addr"),
          nginx.Key('proxy_set_header X-Forwarded-For', "$proxy_add_x_forwarded_for"),
          nginx.Key('proxy_set_header X-Forwarded-Proto', "$scheme"),
          nginx.Key('proxy_set_header X-Forwarded-Host', "$host"),
          nginx.Key('proxy_set_header X-Forwarded-Port', "$server_port"),
          nginx.Key('proxy_set_header X-Real-IP', "$http_upgrade"),
          nginx.Key('log_not_found', 'off'),
          nginx.Key('access_log', 'off')
     ),   
   
   )
   c.add(s)
   nginx.dumpf(c, server_name+".conf")
   show_success(c)

def show_help():
    show_info("This script requires a file with keys domain_name, droplet_name, nginx_conf_file. Each key should be on a new line, separated by space.")
    show_info("If the required file does not exist, the script can create one with default values. You must edit this file with the actual values before running the script again.")
    show_error("You can run the script directly using the Python interpreter from the virtual environment like this:")
    show_success(f"{os.path.join(os.getcwd(), ENV_PATH)} gdd_do.py -i arguments")
    show_info("Options:")
    print('\n')
    show_info("-h, --Help: Show this help message.")
    show_info("-d, --Droplet: Display available droplets.")
    show_info("-s, --Domains: Display domains.")
    show_info("-k, --Keys: Display SSH keys.")
    show_info("-m, --Make_nginx_conf: Make nginx configuration file. Required arguments: server_name(server.example.com), hide_server_ip(1.1.1.1 or hide.example.com), ports(80,...8080), app_location(/).")
    show_info("-i, --Input_file: Specify the input file. The script will create this file with default values if it does not exist.")

def handle_droplet():
    show_info("Displaying Available Droplets :")
    get_droplets()

def handle_domains():
    show_info("Displaying Domains:")
    get_domains()

def handle_keys():
    show_info("Displaying SSH keys:")
    get_sshkeys()

def handle_nginx_conf():
    if len(sys.argv)<6:
        show_error("You have to add arguments like server_name(server.example.com) hide_server_ip(1.1.1.1 or hide.example.com) ports(80,...8080) app_location(/) ")
        sys.exit(f"Usage: {sys.argv[0]} (-m  <server_name> <hide_server_ip> <port1,port2,...portn> <app_location>)")
    
    server_name = sys.argv[2]
    hide_server_ip = sys.argv[3]
    ports = [int(port) for port in sys.argv[4].split(',')]
    app_location = sys.argv[5]

    make_nginx_server(server_name, hide_server_ip, ports, app_location)

    show_success(f"Your nginx server conf ready: {server_name}.conf")
    # Create arguments.txt file with new data
    with open('arguments.txt', 'w') as f:
        droplet_name = "ubuntu_" + server_name.replace('.', '')
        f.write(f"droplet_name {droplet_name}\n")
        f.write(f"domain_name {server_name}\n")
        f.write(f"nginx_conf_file {server_name}.conf\n")
    show_success(f"arguments.txt file has been created with new data.")
    sys.exit()

def handle_input_file():
    file_add = sys.argv[2]
    show_info("Displaying file_name:", file_add)
    if not file_exists(file_add):
        show_error(f"{file_add} does not exist. Creating with default values. Please do not use without changing or call the create nginx conf")
        with open(file_add, 'w') as f:
            f.write("droplet_name ubuntu_domain\n")
            f.write("domain_name sub.exampledomain.com\n")
            f.write("nginx_conf_file sub.exampledomain.com.conf\n")
        show_info(f"Please edit {file_add} with actual values.")
        sys.exit(1)

if __name__ == "__main__":
   # main(sys.argv[1:])
   argumentList = sys.argv[1:]
   # Options
   options = "hdskmi:"
   # Long options
   long_options = ["Help", "Droplets", "Subdomains", "Keys", "Make_nginx_conf", "Input_file"]
   
   if len(sys.argv) == 1:
        show_help()
        sys.exit()

   try:
    # Parsing argument
    arguments, values = getopt.getopt(argumentList, options, long_options)
     
    # checking each argument
    for currentArgument, currentValue in arguments:
        if currentArgument in ("-h", "--Help"):
            show_help()
        elif currentArgument in ("-d", "--Droplet"):
            handle_droplet()
        elif currentArgument in ("-s", "--Subdomains"):
            handle_domains()
        elif currentArgument in ("-k", "--Keys"):
            handle_keys()
        elif currentArgument in ("-m", "--Make_nginx_conf"):
            handle_nginx_conf()
        elif currentArgument in ("-i", "--Input_file"):
            handle_input_file()
    if len(sys.argv)>2:
       main(sys.argv[2:])
   
             
   except getopt.error as err:
    # output error, and return with an error code
    show_error(str(err))
    raise SystemExit(f"Usage: {sys.argv[0]} (-h [help] | -d [droplets] | -s [domains] | -k [ssh keys] | -m [make nginx coonfig]|-i) <arguments>")

