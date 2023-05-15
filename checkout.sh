#!/bin/bash

remoutehost=$1
remoutfille=$2

sudo apt-get update -y
sudo apt-get upgrade -y
sudo apt insall nginx -y
sudo scp /home/gdd_do/$2 /etc/nginx/sites-available/$2
sudo ln -s /etc/nginx/sites-available/$2 /etc/nginx/sites-enabled/$2
sudo systemctl restart nginx