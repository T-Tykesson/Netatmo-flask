# -*- coding: utf-8 -*-
"""
Created on Fri Aug  4 08:16:24 2023

@author: tagtyk0616
"""

# deprecated functions


def convert_to_unix(date, string_format):
    """
    Convert date to unix.

    Parameters
    ----------
        date : string
            The date that should be converted to UNIX format 
            string_format inserted into datetime.strptime.
        string_format : string
            How the date string is formated,
            for example "%Y-%m-%d" or "%Y-%m-%d %H:%M:%S"
    """
    formated_date = datetime.strptime(date, string_format)
    unix_timestamp = datetime.timestamp(formated_date)
    return unix_timestamp


def get_median_data(auth_token, rain_station_list, date_begin, date_end,
                    scale, start_stop_list, gui=None):
    """
    From a rainstation list caluclate median data

    Parameters
    ----------
    auth_token : TYPE
        DESCRIPTION.
    rain_station_list : TYPE
        DESCRIPTION.
    date_begin : TYPE
        DESCRIPTION.
    date_end : TYPE
        DESCRIPTION.
    scale : TYPE
        DESCRIPTION.
    start_stop_list : TYPE
        DESCRIPTION.
    gui : TYPE, optional
        DESCRIPTION. The default is None.

    Returns
    -------
    final_array : TYPE
        DESCRIPTION.

    """

    station_data_list = []
    station_list = []
    for station in rain_station_list:

        if gui is not None:
            gui.progress_window.update_text_box(
                f"Hämtar stationsdata: {station.get_name()}")
            gui.progress_window.uppdate_progress_bar(
                100 // (len(rain_station_list) + 1))

        print(api_counter.get_count())
        if api_counter.get_count() > 450:
            print("Amount of calls soon exceeded")

        station_data = rain_data.get_measure(
            auth_token,
            station.get_device_id(),
            station.get_module_id(),
            date_begin,
            date_end,
            scale,
            start_stop_list,
            save_calls=True,
            gui=gui
        )

        station_data_list.append(station_data)
        station_list.append(station)

    time_step_list = np.arange(
        start_stop_list[0][0], start_stop_list[-1][1], 900, dtype=int
    )

    unix_from_stations = convert_to_unix(station_data_list)
    data_dict = find_what_data_each_time_step(
        station_data_list, station_list, unix_from_stations, time_step_list)

    final_array = []
    gui.progress_window.uppdate_progress_bar(
        100 // (len(rain_station_list) + 1))
    gui.progress_window.update_text_box("Räknar ut median från stationer")
    #update_gui("Räknar ut median från stationer")
    for time_step, values in tqdm(data_dict.items()):
        if values:
            data = data_dict[time_step]
            # Transforming data
            stations = [item[0] for item in data]
            values = [item[1] for item in data]
            #distances = [item[2] for item in data]
            transformed_data = [stations, values]

            time_step_station, time_step_median_value = \
                quickselect_median(transformed_data)

            if isinstance(time_step_station, tuple):
                name = [station.get_name() for station in time_step_station]
                distance = [int(1000*round(station.get_distance(), 3))
                            for station in time_step_station]
            else:
                name = time_step_station.get_name()
                distance = int(1000*round(time_step_station.get_distance(), 3))

            # if test:
            #    time_step = datetime.utcfromtimestamp(
            #       time_step).strftime('%Y-%m-%d %H:%M:%S')
                # final_array.append(
                #    [time_step, time_step_median_value, time_step_station,
                # station_names, station_distances
                #     names, values])

            time_step = datetime.utcfromtimestamp(
                time_step).strftime('%Y-%m-%d %H:%M:%S')
            final_array.append(
                [time_step, time_step_median_value, name, distance])

    return final_array
