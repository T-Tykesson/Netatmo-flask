# -*- coding: utf-8 -*-
"""
Created on Thu Jul 13 11:54:19 2023

@author: tagtyk0616
"""
from datetime import datetime
import numpy as np
import pandas as pd
from tqdm import tqdm
from back_end import rain_data
from back_end.api_counter import (InternalServerError, NoDataInStationError,
                                  NetatmoGeneralError, NoActiveTokenError,
                                  NoApiCallsLeftError, InvalidInputError)
# from api_counter import api_counter
# from api_counter import MaxApiCallReachedError


def quickselect_median(lst):
    """


    Parameters
    ----------
    lst : TYPE
        DESCRIPTION.

    Raises
    ------
    ValueError
        DESCRIPTION.

    Returns
    -------
    TYPE
        DESCRIPTION.
    TYPE
        DESCRIPTION.

    """
    if len(lst[0]) != len(lst[1]):
        raise ValueError(
            "Error in quickselect: Mismatched lengths between names and values")

    if len(lst[1]) == 0:
        raise ValueError("Error int quickselect: Empty list provided")

    if len(lst[1]) % 2 == 1:
        return quickselect(lst, len(lst[1]) // 2)

    lower_median = quickselect(lst, len(lst[1]) // 2 - 1)
    upper_median = quickselect(lst, len(lst[1]) // 2)
    median_value = (float(lower_median[1]) + float(upper_median[1])) / 2
    # name = f"{lower_median[0].get_name()}, {upper_median[0].get_name()}"
    name = (lower_median[0], upper_median[0])
    return name, median_value


def quickselect(lst, k):
    """


    Parameters
    ----------
    lst : TYPE
        DESCRIPTION.
    k : TYPE
        DESCRIPTION.

    Returns
    -------
    TYPE
        DESCRIPTION.

    """
    if len(lst[1]) == 1:
        return [lst[0][0], lst[1][0]]

    pivot_index = len(lst[1]) // 2
    pivot = lst[1][pivot_index]
    lows = [[name, value] for name, value in
            zip(lst[0], lst[1]) if value < pivot]
    highs = [[name, value] for name, value in
             zip(lst[0], lst[1]) if value > pivot]
    pivots = [[name, value] for name, value in
              zip(lst[0], lst[1]) if value == pivot]
    if k < len(lows):
        return quickselect(list(zip(*lows)), k)

    if k < len(lows) + len(pivots):
        if len(pivots) == 1:
            return pivots[0]

        return pivots[k - len(lows)]

    return quickselect(list(zip(*highs)), k - len(lows) - len(pivots))


def convert_to_unix_from_stations(station_data_list):
    """


    Parameters
    ----------
    station_data_list : TYPE
        DESCRIPTION.

    Returns
    -------
    unix_from_stations : TYPE
        DESCRIPTION.

    """
    unix_from_stations = []
    try:
        for station_data in station_data_list:
            station_data_array = np.array(station_data)
            if station_data != []:
                unix_from_station = station_data_array[2, :]
                unix_from_station = unix_from_station.astype(int)
                unix_from_stations.append(unix_from_station)
            else:
                unix_from_stations.append([])
    except IndexError as exc:
        print(station_data_array)
        raise IndexError from exc

    unix_from_stations = np.array(unix_from_stations, dtype=object)
    return unix_from_stations


def find_what_data_each_time_step(station_data_list, station_list,
                                  unix_from_stations, time_step_list):
    """


    Parameters
    ----------
    station_data_list : TYPE
        DESCRIPTION.
    station_list : TYPE
        DESCRIPTION.
    unix_from_stations : TYPE
        DESCRIPTION.
    time_step_list : TYPE
        DESCRIPTION.

    Returns
    -------
    data_dict : TYPE
        DESCRIPTION.

    """
    data_dict = {}
    counter = 0
    counter2 = 0
    for time_step in tqdm(time_step_list):
        for i, unix in enumerate(unix_from_stations):
            try:
                j = (np.abs(unix[:] - time_step)).argmin()
                if (np.abs(time_step - int(station_data_list[i][2, j]))) < 449:
                    # 15 min both ways
                    if time_step in data_dict:
                        if np.abs(time_step - int(station_data_list[i][2, j])) != 0:
                            print("inte noll utan:",
                                  (time_step - int(station_data_list[i][2, j])))

                        data_dict[time_step].append(
                            [station_list[i],
                             float(station_data_list[i][1, j])])
                    else:
                        data_dict[time_step] = \
                            [[station_list[i],
                              float(station_data_list[i][1, j])]]
            except IndexError:
                counter += 1
                #print("station_list_i", station_data_list[i])
                #print("station_list", station_data_list)
                continue
            except ValueError:
                counter2 += 1
                # print(unix)
                # print(time_step)
                continue

    print("counter 1", counter)
    print("counter 2", counter)
    return data_dict


def format_median_data_view(data_dict, reference_coordinate):

    median_array = []
    for time_step, values in tqdm(data_dict.items()):
        if values:
            data = data_dict[time_step]
            # Transforming data
            stations = [item[0] for item in data]
            values = [item[1] for item in data]
            transformed_data = [stations, values]

            time_step_station, time_step_median_value = \
                quickselect_median(transformed_data)

            if isinstance(time_step_station, tuple):
                name = [station.get_name()
                        for station in time_step_station]
                distance = [int(1000*round(station.get_distance(), 3))
                            for station in time_step_station]
            else:
                name = time_step_station.get_name()
                distance = int(
                    1000*round(time_step_station.get_distance(), 3))

            time_step = datetime.utcfromtimestamp(
                int(time_step)).strftime('%Y-%m-%d %H:%M:%S')
            median_array.append(
                [time_step, time_step_median_value, name, distance])

    median_array = np.array(median_array, dtype=object)

    try:
        median_data_frame = pd.DataFrame(median_array, columns=[
            "Datum",
            "Medianvärde regn [mm]",
            "Stationsnamn",
            f"Avstånd från punkt {reference_coordinate} [m]"])
    except ValueError as exc:
        print(median_array)
        raise ValueError(exc) from exc

    return median_data_frame


def format_standard_data_view(data_dict):
    """
    Format the data in a certain way for excel 3d map function.

    Parameters
    ----------
    data_dict : TYPE
        DESCRIPTION.

    Returns
    -------
    pandas_array_sheet_3 : TYPE
        DESCRIPTION.
    """

    station_names = list(set(station.get_name() for data in data_dict.values()
                         for station, _ in data))
    data_rows = {station_name: [] for station_name in station_names}
    time_steps = data_dict.keys()

    for station_name in station_names:
        for time_step in time_steps:
            if time_step in data_dict:
                data = data_dict[time_step]

                # Get the rain value for the current station and time step
                rain_value = next(
                    (value for station,
                     value in data if station.get_name() == station_name), '-')
            else:
                # The station doesn't have data for the current time step
                rain_value = '-'
            data_rows[station_name].append(rain_value)

    standard_view_df = pd.DataFrame(data_rows)
    dates = [datetime.utcfromtimestamp(int(time_step)).strftime('%Y-%m-%d %H:%M:%S')
             for time_step in time_steps]
    standard_view_df.index = pd.Index(dates, name="Datum")

    return standard_view_df


def format_data_for_map_view(input_data, data_dict):
    """
    Format the data in a certain way for excel 3d map function.

    Parameters
    ----------
    data_dict : TYPE
        DESCRIPTION.

    Returns
    -------
    pandas_array_sheet_3 : TYPE
        DESCRIPTION.

    """
    data_rows = []
    for i, (time_step, values) in tqdm(enumerate(data_dict.items())):

        time_step_utc = datetime.utcfromtimestamp(
            time_step).strftime('%Y-%m-%d %H:%M:%S')

        if i == 0:
            row = {
                'Datum': time_step_utc,
                'Stationsnamn': "Referenspunkt",
                'Latitud': input_data.latitude,
                'Longitud': input_data.longitude,
                'Regnvärde [mm]': 0
            }
            data_rows.append(row)

        if values:
            data = data_dict[time_step]
            for station, rain_value in data:
                row = {
                    'Datum': time_step_utc,
                    'Stationsnamn': station.get_name(),
                    'Latitud': station.get_latitude(),
                    'Longitud': station.get_longitude(),
                    'Regnvärde [mm]': rain_value
                }
                data_rows.append(row)

    pandas_array_sheet_3 = pd.DataFrame(data_rows)

    return pandas_array_sheet_3


def collect_station_data(input_data, rain_station_list, start_stop_list, gui=None):
    rain_data_list = []
    for i, station in enumerate(rain_station_list):
        if gui is not None:
            gui.event_queue.put((
                "message", f"Hämtar stationsdata: {station.get_name()}"))
            gui.event_queue.put(("progress", np.ceil(
                100 / (len(rain_station_list) + 1))))

        try:
            station_data = rain_data.get_measure(
                input_data,
                station,
                start_stop_list,
                save_calls=True,
                gui=gui
            )

            rain_data_list.append(station_data)

        except NoApiCallsLeftError:
            if i > 0:
                if gui is not None:
                    gui.event_queue.put((
                        "message", "För många förfrågningar till Netatmo, sparar fil med redan hämtad data..."))
                return rain_data_list

            raise NoApiCallsLeftError

    return rain_data_list


def create_data_views_for_excel(input_data, rain_station_list, start_stop_list,
                                reference_coordinate, gui=None):

    rain_data_list = collect_station_data(
        input_data,
        rain_station_list,
        start_stop_list,
        gui=gui
    )
    # (rain_data_list)
    time_step_list = np.arange(
        start_stop_list[0][0], start_stop_list[-1][1], 900, dtype=int
    )

    rain_station_list = rain_station_list[0:len(rain_data_list)]
    # print(rain_station_list)
    indices_to_delete = []
    for i, value in enumerate(rain_data_list):
        if value == []:
            indices_to_delete.append(i)

    for index in reversed(indices_to_delete):
        del rain_data_list[index]
        del rain_station_list[index]

    # print(rain_data_list)
    unix_from_stations = convert_to_unix_from_stations(rain_data_list)

    data_time_step_dict = find_what_data_each_time_step(
        rain_data_list,
        rain_station_list,
        unix_from_stations,
        time_step_list
    )
    # print(data_time_step_dict)
    if gui is not None:
        gui.event_queue.put(("progress", 100 // (len(rain_station_list) + 1)))
        gui.event_queue.put(("message", "Räknar ut median från stationer"))

    standard_view_df = format_standard_data_view(data_time_step_dict)
    median_df = format_median_data_view(
        data_time_step_dict, reference_coordinate)
    map_view_df = format_data_for_map_view(input_data, data_time_step_dict)

    return standard_view_df, median_df, map_view_df
