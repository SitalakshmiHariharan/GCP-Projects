from flask import Flask
from flask import render_template
from flask import request, redirect, url_for

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


app = Flask(__name__)
Bootstrap(app)
app.static_folder = 'static'

CLOUD_STORAGE_BUCKET = os.environ['CLOUD_STORAGE_BUCKET']

def init_connection_engine():
    db_config = {
        'pool_size': 5,
        'max_overflow': 2,
        'pool_timeout': 30,
        'pool_recycle': 1800,
    }
    if os.environ.get("DB_HOST"):
        return init_tcp_connection_engine(db_config)
    else:
        return init_unix_connection_engine(db_config)    

def init_tcp_connection_engine(db_config):
   
    db_user = os.environ["DB_USER"]
    db_pass = os.environ["DB_PASS"]
    db_name = os.environ["DB_NAME"]
    db_host = os.environ["DB_HOST"]

    # Extract host and port from db_host
    host_args = db_host.split(":")
    db_hostname, db_port = host_args[0], int(host_args[1])

    pool = sqlalchemy.create_engine(
        # Equivalent URL:
        # postgres+pg8000://<db_user>:<db_pass>@<db_host>:<db_port>/<db_name>
        sqlalchemy.engine.url.URL(
            drivername="postgresql+pg8000",
            username=db_user,  # e.g. "my-database-user"
            password=db_pass,  # e.g. "my-database-password"
            host=db_hostname,  # e.g. "127.0.0.1"
            port=db_port,  # e.g. 5432
            database=db_name  # e.g. "my-database-name"
        ),
        **db_config
    )
    # [END cloud_sql_postgres_sqlalchemy_create_tcp]
    pool.dialect.description_encoding = None
    return pool


def init_unix_connection_engine(db_config):
    
    db_user = os.environ["DB_USER"]
    db_pass = os.environ["DB_PASS"]
    db_name = os.environ["DB_NAME"]
    db_socket_dir = os.environ.get("DB_SOCKET_DIR", "/cloudsql")
    cloud_sql_connection_name = os.environ["CLOUD_SQL_CONNECTION_NAME"]

    pool = sqlalchemy.create_engine(

        # Equivalent URL:
        # postgres+pg8000://<db_user>:<db_pass>@/<db_name>?
        # unix_sock=<socket_path>/<cloud_sql_instance_name>/.s.PGSQL.5432
        sqlalchemy.engine.url.URL(
            drivername="postgresql+pg8000",
            username=db_user,  # e.g. "my-database-user"
            password=db_pass,  # e.g. "my-database-password"
            database=db_name,  # e.g. "my-database-name"
            query={
                "unix_sock": "{}/{}/.s.PGSQL.5432".format(
                    db_socket_dir,  # e.g. "/cloudsql"
                    cloud_sql_connection_name)  # i.e "<PROJECT-NAME>:<INSTANCE-REGION>:<INSTANCE-NAME>"
            }
        ),
        **db_config
    )
    # [END cloud_sql_postgres_sqlalchemy_create_socket]
    pool.dialect.description_encoding = None
    return pool

# This global variable is declared with a value of `None`, instead of calling
# `init_connection_engine()` immediately, to simplify testing. In general, it
# is safe to initialize your database connection pool when your script starts
# -- there is no need to wait for the first request.
db = None

@app.route("/")
def index():
    return render_template("public/index.html")     


@app.route("/upload-files", methods=["GET","POST"])
def upload_files():
    global db
    db = init_connection_engine()
    """Process the uploaded file and upload it to Google Cloud Storage."""
    print("Inside the upload files route")
    regEmail = request.form.get("email")
    print(regEmail)
    uploaded_file1 = request.files.get("filename1")
    uploaded_file2 = request.files.get("filename2")

    if regEmail == "":
        print("*******regEmail is not having any value*******")
        e_message = "Please fill in your email address"
        return render_template("index.html", message = e_message)
    else:
        print("********Inside the DB Connect********")
        with db.connect() as conn:        
            # Construct the query
            print("********** 1. Before the query ************") 
            s = ""
            s += "SELECT user_id FROM users"
            s += " WHERE"
            s += " ("
            s += " user_email ='" + regEmail + "'"        
            s += " )"
            print(s)
            try:
                array_row = conn.execute(s).fetchone()
                print("*********** 1. Query is executed **************")       
            except:
                t_message = "Database error: " + e + "/n SQL: " + s
                return render_template("public/index.html", message = t_message) 
      
        print("it is above array_row", array_row)
        if array_row is None:
            t_message = "Your credentials does not exist. Please register !!"
            return render_template("public/index.html", message = t_message)                
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
    bucket = gcs1.get_bucket(CLOUD_STORAGE_BUCKET)
    
    # Create a new blob and upload the file's content.
    blob = bucket.blob(uploaded_file1.filename)

    blob.upload_from_string(
        uploaded_file1.read(),
        content_type=uploaded_file1.content_type
    )
    
     # Create a Cloud Storage client.
    gcs2 = storage.Client()

    # Get the bucket that the file will be uploaded to.
    bucket = gcs2.get_bucket(CLOUD_STORAGE_BUCKET)
    
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
