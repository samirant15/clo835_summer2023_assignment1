from flask import Flask, render_template, request
from pymysql import connections
import os
import random
import argparse
import boto3
from botocore.exceptions import ClientError


app = Flask(__name__)

DBHOST = os.environ.get("DBHOST") or "localhost"
DBUSER = os.environ.get("DBUSER") or "root"
DBPWD = os.environ.get("DBPWD") or "passwors"
DATABASE = os.environ.get("DATABASE") or "employees"
COLOR_FROM_ENV = os.environ.get('APP_COLOR') or "lime"
DBPORT = int(os.environ.get("DBPORT"))
BG_IMAGE_LOCAL_PATH = os.environ.get("BG_IMAGE_LOCAL_PATH", "/static/image.png")
HEADER_NAME = os.getenv("HEADER_NAME", "Samir,Liliana,Yasmin")
BUCKET_NAME = os.getenv("BUCKET_NAME")
BG_IMAGE_S3_KEY = os.getenv("BG_IMAGE_S3_KEY")

# Function to download background image from S3
def download_image_from_s3():
    # Create S3 client with explicit region (credentials come from environment variables)
    s3_client = boto3.client('s3', region_name=os.environ.get('AWS_DEFAULT_REGION', 'us-east-1'))
    s3_url = f"s3://{BUCKET_NAME}/{BG_IMAGE_S3_KEY}"
    app.logger.info(f"Background image URL: {s3_url}")
    app.logger.info(f"Downloading image from S3 bucket: {BUCKET_NAME}, key: {BG_IMAGE_S3_KEY}")
    s3_client.download_file(BUCKET_NAME, BG_IMAGE_S3_KEY, BG_IMAGE_LOCAL_PATH)
    app.logger.info(f"Successfully downloaded background image to: {BG_IMAGE_LOCAL_PATH}")

# Create a connection to the MySQL database
db_conn = connections.Connection(
    host= DBHOST,
    port=DBPORT,
    user= DBUSER,
    password= DBPWD, 
    db= DATABASE
)
output = {}
table = 'employee';

# Define the supported color codes
color_codes = {
    "red": "#e74c3c",
    "green": "#16a085",
    "blue": "#89CFF0",
    "blue2": "#30336b",
    "pink": "#f4c2c2",
    "darkblue": "#130f40",
    "lime": "#C1FF9C",
}


# Create a string of supported colors
SUPPORTED_COLORS = ",".join(color_codes.keys())

# Generate a random color
COLOR = random.choice(["red", "green", "blue", "blue2", "darkblue", "pink", "lime"])


@app.route("/", methods=['GET', 'POST'])
def home():
    s3_url = f"s3://{BUCKET_NAME}/{BG_IMAGE_S3_KEY}" if BUCKET_NAME and BG_IMAGE_S3_KEY else "N/A"
    app.logger.info(f"Background image URL (S3): {s3_url}")
    app.logger.info(f"Background image path (local): {BG_IMAGE_LOCAL_PATH}")
    return render_template('addemp.html', bg_image_path=BG_IMAGE_LOCAL_PATH, header_name=HEADER_NAME)

@app.route("/about", methods=['GET','POST'])
def about():
    return render_template('about.html', bg_image_path=BG_IMAGE_LOCAL_PATH)
    
@app.route("/addemp", methods=['POST'])
def AddEmp():
    emp_id = request.form['emp_id']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    primary_skill = request.form['primary_skill']
    location = request.form['location']

  
    insert_sql = "INSERT INTO employee VALUES (%s, %s, %s, %s, %s)"
    db_conn.ping(reconnect=True)
    cursor = db_conn.cursor()

    try:
        
        cursor.execute(insert_sql,(emp_id, first_name, last_name, primary_skill, location))
        db_conn.commit()
        emp_name = "" + first_name + " " + last_name

    finally:
        cursor.close()

    print("all modification done...")
    return render_template('addempoutput.html', name=emp_name, bg_image_path=BG_IMAGE_LOCAL_PATH)

@app.route("/getemp", methods=['GET', 'POST'])
def GetEmp():
    return render_template("getemp.html", bg_image_path=BG_IMAGE_LOCAL_PATH)


@app.route("/fetchdata", methods=['GET','POST'])
def FetchData():
    emp_id = request.form['emp_id']

    output = {}
    select_sql = "SELECT emp_id, first_name, last_name, primary_skill, location from employee where emp_id=%s"
    db_conn.ping(reconnect=True)
    cursor = db_conn.cursor()

    try:
        cursor.execute(select_sql,(emp_id))
        result = cursor.fetchone()
        
        # Add No Employee found form
        output["emp_id"] = result[0]
        output["first_name"] = result[1]
        output["last_name"] = result[2]
        output["primary_skills"] = result[3]
        output["location"] = result[4]
        
    except Exception as e:
        print(e)

    finally:
        cursor.close()

    return render_template("getempoutput.html", id=output["emp_id"], fname=output["first_name"],
                           lname=output["last_name"], interest=output["primary_skills"], location=output["location"], bg_image_path=BG_IMAGE_LOCAL_PATH)

if __name__ == '__main__':
    
    # Download background image from S3
    download_image_from_s3()
    
    # Check for Command Line Parameters for color
    parser = argparse.ArgumentParser()
    parser.add_argument('--color', required=False)
    args = parser.parse_args()

    if args.color:
        print("Color from command line argument =" + args.color)
        COLOR = args.color
        if COLOR_FROM_ENV:
            print("A color was set through environment variable -" + COLOR_FROM_ENV + ". However, color from command line argument takes precendence.")
    elif COLOR_FROM_ENV:
        print("No Command line argument. Color from environment variable =" + COLOR_FROM_ENV)
        COLOR = COLOR_FROM_ENV
    else:
        print("No command line argument or environment variable. Picking a Random Color =" + COLOR)

    # Check if input color is a supported one
    if COLOR not in color_codes:
        print("Color not supported. Received '" + COLOR + "' expected one of " + SUPPORTED_COLORS)
        exit(1)

    app.run(host='0.0.0.0',port=81,debug=True)
