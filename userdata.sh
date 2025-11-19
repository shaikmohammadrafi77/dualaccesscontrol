#!/bin/bash

# Update the machine
dnf update -y

# Install Python 3.9, pip, git
dnf install -y python3.9 python3.9-pip git

# Upgrade pip
python3.9 -m pip install --upgrade pip

# Change to ec2-user home
cd /home/ec2-user

# Clone the correct repo
git clone https://github.com/shaikmohammadrafi77/dualaccesscontrol.git

# Move into project directory
cd dualaccesscontrol

# Create virtual environment
python3.9 -m venv venv
source venv/bin/activate

# Install dependencies (ensure requirements.txt exists)
pip install -r requirements.txt

# Set flask environment variables
export FLASK_APP=app.py
export FLASK_ENV=production

# Run flask app on port 5000
nohup flask run --host=0.0.0.0 --port=5000 &
