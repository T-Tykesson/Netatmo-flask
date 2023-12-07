import json
from flask import Flask, jsonify, render_template, redirect, url_for, request, send_file
from prediction import predict
import webbrowser
import threading
import os
import queue
import datetime
import backend_handler
from backend_handler import UserInputData
from back_end.api_counter import (InternalServerError,
                                  NetatmoGeneralError, NoActiveTokenError,
                                  NoApiCallsLeftError, InvalidInputError)
import calendar



application = Flask(__name__)


@application.route('/')
def home():
    return redirect(url_for("getdata"))

@application.route("/getdata/", methods=["POST", "GET"])
def getdata():
    if request.method == "POST":
        auth_token = request.form["auth"]
        start_date = str(request.form.get("start_date"))
        end_date = str(request.form.get("end_date"))
        latitude = float(request.form["latitude"])
        longitude = float(request.form["longitude"])
        amount = int(request.form["amount"])
        scale = "30 min"
        directory = ""
        print(auth_token, "\n", start_date, "\n"
              , end_date)
        
        input_data = UserInputData(
                auth_token,
                latitude,
                longitude,
                start_date,
                end_date,
                scale,
                amount,
                directory
            )

        name = backend_handler.run_program(input_data)

        return redirect(url_for("download_excel", excel_filename=name))
    else: 
        return render_template("login.html")

@application.route('/download_excel/<excel_filename>')
def download_excel(excel_filename):
    excel_filename = str(excel_filename)
    print("Downloading file", excel_filename)
    return send_file(excel_filename, as_attachment=True)

print(application.url_map)

if __name__=="__main__":
    application.run(debug=True)
