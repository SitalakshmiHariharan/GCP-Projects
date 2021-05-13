from flask import Flask
from flask import render_template
from flask import request, redirect, url_for, response

from werkzeug.utils import secure_filename

from google.cloud import storage

from flask_bootstrap import Bootstrap

import os
import logging

import hashlib 
import psycopg2  
from flask_mail import Message
from datetime import datetime

import sqlalchemy


# Database creds - for local
#t_host = "localhost"
#t_port = "5432" #default postgres port
#t_dbname = "postgres"
#t_user = "postgres"
#t_pw = "Varshiya"
#db_conn = psycopg2.connect(host=t_host, port=t_port, dbname=t_dbname, user=t_user, password=t_pw)

# Database connection for GCP


db_cursor = db_conn.cursor()

app = Flask(__name__)
Bootstrap(app)
app.static_folder = 'static'

CLOUD_STORAGE_BUCKET = os.environ['CLOUD_STORAGE_BUCKET']


@app.route("/")
def index():
    return render_template("public/index.html")     


@app.route("/upload-files", methods=["GET","POST"])
def upload_files():
    """Process the uploaded file and upload it to Google Cloud Storage."""
    print("Inside the upload files route")
    regEmail = request.form.get("email")
    print(regEmail)
    uploaded_file1 = request.files.get("filename1")
    uploaded_file2 = request.files.get("filename2")

    if regEmail == "":
        e_message = "Please fill in your email address"
        return render_template("index.html", message = e_message)
    else:
        print("********** 1. Before the query ************") 
        # Get user ID from PostgreSQL users table
        s = ""
        s += "SELECT user_id FROM users"
        s += " WHERE"
        s += " ("
        s += " user_email ='" + regEmail + "'"        
        s += " )"
        print(s)
        db_cursor.execute(s)
        print("*********** 1. Query is executed **************")
       
        try:
            array_row = db_cursor.fetchone()
        except psycopg2.Error as e:
            t_message = "Database error: " + e + "/n SQL: " + s
            return render_template("public/index.html", message = t_message)       
        
        print("it is above array_row", array_row)
        if array_row is None:
            t_message = "Your credentials does not exist. Please register !!"
            return render_template("public/index.html", message = t_message, scroll="serviceModal1")                
        else:
            ID_user = array_row[0]
        db_cursor.close()
        db_conn.close()    

    if not uploaded_file1:
        return 'No file uploaded.', 400
    if not uploaded_file2:
        return 'No file uploaded.', 400
        
    # Create a Cloud Storage client.
    gcs1 = storage.Client()

    # Get the bucket that the file will be uploaded to.
    #bucket = gcs1.get_bucket(CLOUD_STORAGE_BUCKET)
    
    # Create a new blob and upload the file's content.
    blob = bucket.blob(uploaded_file1.filename)

    blob.upload_from_string(
        uploaded_file1.read(),
        content_type=uploaded_file1.content_type
    )
    
     # Create a Cloud Storage client.
    gcs2 = storage.Client()

    # Get the bucket that the file will be uploaded to.
    #bucket = gcs2.get_bucket(CLOUD_STORAGE_BUCKET)
    
    # Create a new blob and upload the file's content.
    blob1 = bucket.blob(uploaded_file2.filename)

    blob1.upload_from_string(
        uploaded_file2.read(),
        content_type=uploaded_file2.content_type
    )
    print("The below are the two urls")
    url1 = blob.public_url
    print(url1)
    url2 = blob1.public_url
    print(url2)

    # The public URL can be used to directly access the uploaded file via HTTP.
    #return '{} {}'.format(url1, url2)
    return render_template("public/landing.html", url1 = url1, url2 = url2, url3="Dummy")
    
@app.route("/candidate-relevancy", methods=["GET","POST"])
def candidate_relevancy():
    print("The 2 urls are passed to fullscreen")
    url1 = request.form.get("url1")
    url2 = request.form.get("url2")
    print(url1)
    print(url2)
    return render_template("public/sample.html", url = url1) 
    
@app.errorhandler(500)
def server_error(e):
    logging.exception('An error occurred during a request.')
    return """
    An internal error occurred: <pre>{}</pre>
    See logs for full stacktrace.
    """.format(e), 500
    
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)
