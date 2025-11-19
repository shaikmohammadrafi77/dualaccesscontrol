#!/bin/bash

# Update system
dnf update -y

# Install Python, pip and git
dnf install -y python3.9 python3.9-pip git

# Upgrade pip
python3.9 -m pip install --upgrade pip

# Go to ec2-user home
cd /home/ec2-user

# Clone your repository
git clone https://github.com/shaikmohammadrafi77/dual-access-control-python.git

# Go into project folder
cd dual-access-control-python

# Create and activate virtual environment
python3.9 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Set Flask environment variables
export FLASK_APP=app.py
export FLASK_ENV=production

# Run the Flask app on port 5000
nohup flask run --host=0.0.0.0 --port=5000 &
