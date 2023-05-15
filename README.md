# nginx_serverHide
# gdd_do.py

This script performs various operations related to managing domains and droplets using the GoDaddy API and DigitalOcean API.

## Prerequisites

- Python 3.9 or higher
- DigitalOcean API token with necessary permissions
- GoDaddy API credentials (public key and secret key)

## Installation

1. Clone the repository: `git clone https://github.com/bartaadalbert/nginx_serverHide.git`
2. Navigate to the project directory: `cd nginx_serverHide`
3. Create a Python virtual environment:
   ```shell 
      python3 -m venv envgdd_do
   
    For Linux/Mac:
    source envgdd_do/bin/activate
    ```

4. Install dependencies: `pip3 install -r requirements.txt`

## Usage

Run the script using the following command:

```shell
   python3 gdd_do.py [options] [arguments]
```
Available options:

    -h, --Help: Show the help menu and usage instructions.
    -d, --Droplet: Display available droplets.
    -s, --Subdomains: Display domains.
    -k, --Keys: Display SSH keys.
    -m, --Make_nginx_conf: Create an nginx configuration file.
    -i, --Input_file: Read arguments from a file and setup the DO server with nginx reverse proxy.
   
Example usages:
    python3 gdd_do.py -d
    or full path to the Python virtual environment
    /path/to/envgdd_do/bin/python3 gdd_do.py -d
    
Create an nginx configuration file:
    /path/to/envgdd_do/bin/python3 gdd_do.py -m example.com hide.example.com 80,8000,8080 /
    /path/to/envgdd_do/bin/python3 gdd_do.py -m example.com 1.1.1.1 80,8000,8080 /
    
Read arguments from a file and setup a server with domain:
     /path/to/envgdd_do/bin/python3 gdd_do.py -i arguments.txt
     
Please replace `/path/to/` with the actual full path to your Python virtual environment.

Setting up a Cron Job

You can set up a cron job to automatically recreate the server with a new droplet. Certainly! Here's an updated version of the cron job configuration to recreate the server after 3 days at 3:00 AM:

    Open the crontab for editing:
    crontab -e
    0 3 */3 * * /path/to/nginx_serverHide/envgdd_do/bin/python3 /path/to/nginx_serverHide/gdd_do.py -i /path/to/nginx_serverHide/arguments.txt
    Make sure to save the crontab file after making the changes. The script will then be executed automatically by the cron job according to the specified schedule.

   
