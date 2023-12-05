import json
from flask import Flask, jsonify, render_template, redirect, url_for, request
from prediction import predict
import webbrowser
import threading
import os
import queue
import datetime
import backend_handeler
from backend_handeler import UserInputData
from back_end.api_counter import (InternalServerError,
                                  NetatmoGeneralError, NoActiveTokenError,
                                  NoApiCallsLeftError, InvalidInputError)

from babel.numbers import *  # Included due to hidden imports tkcalendar
from babel.dates import format_date, parse_date, get_day_names, get_month_names
import calendar
import openpyxl


app = Flask(__name__)


@app.route('/')
def home():
    #return "Hello, Flask!"
    return redirect(url_for("login"))

@app.route("/login/", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        auth_key = request.form["auth"]
        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")
        print(auth_key, "\n", start_date, "\n"
              , end_date)
        
        input_data = UserInputData(
                auth_token,
                latitude,
                longitude,
                date_begin,
                date_end,
                scale,
                amount,
                directory
            )

        backend_handeler.run_program(input_data)

        return redirect(url_for("user", usr=auth_key))
    else: 
        return render_template("login.html")

@app.route("/<usr>")
def user(usr):
    return f"<h1>{usr}</h1>"


@app.route('/predictions', methods=['POST'])
def create_prediction():
    data = request.data or '{}'
    body = json.loads(data)
    return jsonify(predict(body))

print(app.url_map)

if __name__=="__main__":
    app.run(debug=True)
