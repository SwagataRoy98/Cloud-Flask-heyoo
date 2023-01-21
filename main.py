# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import datetime
import pytz
# [START gae_python38_render_template]
# [START gae_python3_render_template]
# import datetime

# from flask import Flask, render_template

# app = Flask(__name__)


# @app.route('/')
# def root():
#     # For the sake of example, use static information to inflate the template.
#     # This will be replaced with real information in later steps.

#     return "hello_world"


# if __name__ == '__main__':
#     # This is used when running locally only. When deploying to Google App
#     # Engine, a webserver process such as Gunicorn will serve the app. This
#     # can be configured by adding an `entrypoint` to app.yaml.
#     # Flask's development server will automatically serve static files in
#     # the "static" directory. See:
#     # http://flask.pocoo.org/docs/1.0/quickstart/#static-files. Once deployed,
#     # App Engine itself will serve those files as configured in app.yaml.
#     app.run(host='127.0.0.1', port=8080, debug=True)
# # [END gae_python3_render_template]
# # [END gae_python38_render_template]
import os
import logging
from heyoo import WhatsApp
from dotenv import load_dotenv
from flask import Flask, request, make_response,session
from flask_session import Session
from datetime import datetime,timezone
import tempfile
import pymysql
db_user = os.environ.get('CLOUD_SQL_USERNAME')
db_password = os.environ.get('CLOUD_SQL_PASSWORD')
db_name = os.environ.get('CLOUD_SQL_DATABASE_NAME')
db_connection_name = os.environ.get('CLOUD_SQL_CONNECTION_NAME')
ist_tz = pytz.timezone('Asia/Kolkata')
# Initialize Flask App
app = Flask(__name__)
app.config['SESSION_TYPE'] = 'memcached'
app.config['SECRET_KEY'] = 'super secret key'
sess = Session()
tmp_dir = tempfile.gettempdir()
# Load .env file
load_dotenv()
messenger = WhatsApp(os.getenv("TOKEN"), phone_number_id=os.getenv("PHONE_NUMBER_ID"))
VERIFY_TOKEN = "polley"

# Logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


@app.route("/", methods=["GET", "POST"])
def hook():
    if request.method == "GET":
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            logging.info("Verified webhook")
            response = make_response(request.args.get("hub.challenge"), 200)
            response.mimetype = "text/plain"
            return response
        return "Hello World"




    # Handle Webhook Subscriptions
    data = request.get_json()
    logging.info("Received webhook data: %s", data)
    changed_field = messenger.changed_field(data)
    if changed_field == "messages":
        new_message = messenger.get_mobile(data)
        if new_message:
            mobile = messenger.get_mobile(data)
            name = messenger.get_name(data)
            time = messenger.get_message_timestamp(data)
        if os.environ.get('GAE_ENV') == 'standard':
            logging.info("In here part 1")
        # If deployed, use the local socket interface for accessing Cloud SQL
            unix_socket = '/cloudsql/{}'.format(db_connection_name)
            cnx = pymysql.connect(user=db_user, password=db_password,unix_socket=unix_socket, db=db_name)
        with cnx.cursor() as cursor:
            logging.info("In here part 3")
            sql = "SELECT * FROM `Customers` WHERE `phone_no`= %s"
            cursor.execute(sql, mobile)
            result = cursor.fetchone()
        if result is None:
            with cnx.cursor() as cursor:
                logging.info("In here part 1")
                sql = "INSERT INTO `Customers` (`name`, `phone_no`,`InsertTS`) VALUES (%s, %s)"
                cursor.execute(sql, (name, mobile, datetime.now(ist_tz).strftime('%Y-%m-%d %H:%M:%S'),)))
                cnx.commit()
        message_type = messenger.get_message_type(data)
        logging.info("In here part 4")
        logging.info(f"New Message; sender:{mobile} name:{name} type:{message_type}")
        if message_type == "text":
            message = messenger.get_message(data)
            name = messenger.get_name(data)
            logging.info("Message: %s", message)
            if message is not None:
                if 'Hi' in message or 'hi' in message or 'HI' in message:
                    messenger.send_message(f"Hi {name}, Welcome to Prince Pipe Customer Outreach Program", mobile)
                    messenger.send_message(f"Please enter your item", mobile)
                    with cnx.cursor() as cursor:
                        logging.info(time)
                        sql = "INSERT INTO `Customer_Log` (`Phone_No`,`ChatTS`,`Chat_Details`) VALUES (%s, %s, %s)"
                        cursor.execute(sql,(mobile, (datetime.now(ist_tz).strftime('%Y-%m-%d %H:%M:%S'),), message))
                        cnx.commit()
                elif 'T' in message:
                    logging.info(time)
                    messenger.send_message(f"Your item is {message}", mobile)
                    messenger.send_message(f"Please enter your address", mobile)
                    with cnx.cursor() as cursor:
                        logging.info("In here part 6")
                        sql = "INSERT INTO `Customer_Log` (`Phone_No`,`ChatTS`,`Chat_Details`, `Chat_Type`) VALUES (%s, %s, %s, %s)"
                        cursor.execute(sql, (mobile, (datetime.now(ist_tz).strftime('%Y-%m-%d %H:%M:%S'),), message, 'item'))
                        cnx.commit()
                elif 'A' in message:
                    logging.info(time)
                    messenger.send_message(f"Your address is {message}", mobile)
                    messenger.send_message(f"Please type end", mobile)
                    with cnx.cursor() as cursor:
                        logging.info("In here part 7")
                        sql = "INSERT INTO `Customer_Log` (`Phone_No`,`ChatTS`,`Chat_Details`,`Chat_Type`) VALUES (%s, %s, %s, %s)"
                        cursor.execute(sql, (mobile, (datetime.now(ist_tz).strftime('%Y-%m-%d %H:%M:%S'),), message, 'address'))
                        cnx.commit()
                elif 'end' in message:
                    with cnx.cursor() as cursor:
                        logging.info("In here part 3")
                        sql = "SELECT * FROM `Customer_Log` WHERE `Phone_No`= %s and `Chat_Type` in (%s,%s)"
                        cursor.execute(sql, (mobile, 'item', 'address'))
                        result = cursor.fetchall()
                        logging.info('The result Set is: ')
                        logging.info(result)
                        for row in result:
                            if row[4] == 'item':
                                item_order = row[2]
                            elif row[4] == 'address':
                                add_order = row[2]
                    messenger.send_message(f"You have ordered {item_order}, which will be delivered to {add_order}", mobile)
                    with cnx.cursor() as cursor:
                        logging.info("In here part 8")
                        sql = "INSERT INTO `Order_Table` (`OrderNo`,`CancelFlag`,`ItemDesc`,`CustomerName`,`CustomerPhoneNo`,`ShippingAddress`,`InsertTimeStamp`) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                        cursor.execute(sql, ('OR001', 'N', item_order, name, mobile, add_order, (datetime.now(ist_tz).strftime('%Y-%m-%d %H:%M:%S'),)))
                        cnx.commit()

            else:
                messenger.send_message(f"gar marao", mobile)
        else:
            print("No new message")
    return "ok"


if __name__ == "__main__":
    app.run(port=5000, debug=True)
