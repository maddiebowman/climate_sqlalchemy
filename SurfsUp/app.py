#################################################
# Import Dependencies
#################################################

from flask import Flask, jsonify
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func, desc
import numpy as np
import pandas as pd
import datetime as dt
from datetime import datetime, date, timedelta

#################################################
# Database Setup
#################################################

engine = create_engine("sqlite:///../Resources/hawaii.sqlite")

# Reflect an existing database into a new model
Base = automap_base()

# Reflect the tables
Base.prepare(autoload_with=engine)

# Save references to each table
measurement = Base.classes.measurement
station = Base.classes.station

# Create our session (link) from Python to the DB
session = Session(engine)
session.close()

#################################################
# Flask Setup
#################################################

app = Flask(__name__)

#################################################
# Flask Routes
#################################################

@app.route("/")
def homepage():
    """List all available api routes and links."""
    return (
        f"Welcome to the Honolulu Climate App!<br/>"
        f"Available API Routes:<br/>"
        f"<a href='/api/v1.0/precipitation'>/api/v1.0/precipitation</a><br/>"
        f"<a href='/api/v1.0/stations'>/api/v1.0/stations</a><br/>"
        f"<a href='/api/v1.0/tobs'>/api/v1.0/tobs</a><br/>"
        f"<a href='/api/v1.0/&lt;start&gt;'>/api/v1.0/&lt;start&gt;</a><br/>"
        f"<a href='/api/v1.0/&lt;start&gt;/&lt;end&gt;'>/api/v1.0/&lt;start&gt;/&lt;end&gt;</a>"
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
    # Open session
    session = Session(engine)

    # Query to find last 12 months of precipitation data
    last_date_query = session.query(func.max(measurement.date)).scalar()
    last_date = dt.datetime.strptime(last_date_query, '%Y-%m-%d')

    one_year_ago = last_date - dt.timedelta(days=365)
    precipitation_data = session.query(measurement.date, measurement.prcp).filter(measurement.date >= one_year_ago).all()

    session.close()

    # Convert precipitation data into dictionary
    precipitation_dict = {}
    for date, prcp in precipitation_data:
        precipitation_dict[date] = prcp

    return jsonify(precipitation_dict)

@app.route("/api/v1.0/stations")
def stations():
    # Open session
    session = Session(engine)

    # Query to list all stations
    results = session.query(station.name).all()

    session.close()

    # Convert results into a list
    station_list = list(np.ravel(results))

    return jsonify(station_list)

@app.route("/api/v1.0/tobs")
def tobs():
    # Open session
    session = Session(engine)

    # Query to find most active station
    most_active_station = session.query(measurement.station, func.count(measurement.station)).\
        group_by(measurement.station).\
        order_by(func.count(measurement.station).desc()).first()[0]
   
   # Find the last date in the database
    last_date_query = session.query(func.max(measurement.date)).scalar()
    last_date = dt.datetime.strptime(last_date_query, '%Y-%m-%d')

    # Calculate the date one year ago from the last date
    one_year_ago = last_date - dt.timedelta(days=365)
    
    # Find temperature stats for most active station
    temp_stats = session.query(measurement.date, measurement.tobs).\
        filter(measurement.station == most_active_station).\
        filter(measurement.date >= one_year_ago).all()
    
    # Convert temperature stats into a list of dictionaries
    temp_list = []
    for date, tobs in temp_stats:
        temp_list.append({"date": date, "tobs": tobs})

    return jsonify(temp_list)

@app.route("/api/v1.0/<start>")
def start_date(start):
    # Open session
    session = Session(engine)

    # Find start date of dataset
    first_date = session.query(func.min(measurement.date)).scalar()


    # Query to find start date min, ave, and max temp
    temp_start_data = session.query(func.min(measurement.tobs), func.avg(measurement.tobs), func.max(measurement.tobs)).\
        filter(measurement.date == first_date)
    
    session.close()

    # Structure as JSON object
    start_temp_dict = {
        "start_date": first_date,
        "tmin": temp_start_data[0][0],
        "tavg": temp_start_data[0][1],
        "tmax": temp_start_data[0][2]
    }

    return jsonify(start_temp_dict)

@app.route("/api/v1.0/<start>/<end>")
def start_end_date(start, end):
    # Open session
    session = Session(engine)

    # Find start date of dataset
    first_date = session.query(func.min(measurement.date)).scalar()
    # Find end date of dataset
    last_date = session.query(func.max(measurement.date)).scalar()

    # Query to find min, ave, and  max temp from start to end
    all_temp_data = session.query(func.min(measurement.tobs), func.avg(measurement.tobs)
                             , func.max(measurement.tobs)).all()
    min_temp, avg_temp, max_temp = all_temp_data[0]

    session.close()

    # Structure as JSON object
    temp_dict = {
        "start_date": first_date,
        "end_date": last_date,
        "tmin": all_temp_data[0][0],
        "tavg": all_temp_data[0][1],
        "tmax": all_temp_data[0][2]
    }

    return jsonify(temp_dict)

# Run the app
if __name__ == "__main__":
    app.run(debug=True)