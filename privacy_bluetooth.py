""" THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, TITLE AND
NON-INFRINGEMENT. IN NO EVENT SHALL THE COPYRIGHT HOLDERS OR ANYONE
DISTRIBUTING THE SOFTWARE BE LIABLE FOR ANY DAMAGES OR OTHER LIABILITY,
WHETHER IN CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE. """

# -*- coding: utf-8 -*-
# pylint: disable=C0116, W0621, W1203, C0103, C0301, W1201
# C0116: Missing function or method docstring
# W0621: Redefining name %r from outer scope (line %s)
# W1203: Use % formatting in logging functions and pass the % parameters as arguments
# C0103: Constant name "%s" doesn't conform to UPPER_CASE naming style
# C0301: Line too long (%s/%s)
# W1201: Specify string format arguments as logging function parameters

"""This script scans for nearby Bluetooth devices, storing information about them in a dataframe. 
It calculates the distance to each device based on its RSSI (signal strength) and updates the dataframe as new devices are discovered 
or existing devices are seen again. 
It then prints the dataframe to the screen, sorted by distance from the device running the script.
"""

# Description: Scan for nearby Bluetooth devices and print their information to the screen
# Author: James Sawyer
# Email: githubtools@jamessawyer.co.uk
# Website: http://www.jamessawyer.co.uk/

import asyncio
import datetime

import pandas as pd
from bleak import BleakScanner
from tabulate import tabulate

# create an empty DataFrame to store device information
df = pd.DataFrame(
    columns=[
        "name",
        "rssi",
        "address",
        "last_seen",
        "count",
        "distance"])


def calc_distance(rssi, rssi_0=0, n=2):
    # rough distance calculation based on RSSI
    distance = 10 ** ((rssi_0 - rssi) / (10 * n))
    # return the distance in whole meters
    return int(distance)


async def main():

    global df

    while True:
        try:
            # scan for BLE devices and update the DataFrame
            devices = await BleakScanner.discover()

            for d in devices:
                # print(d.name, d.rssi, d.address)
                if d.address not in df.index:
                    # add it to the DataFrame
                    df = pd.concat([df,
                                    pd.DataFrame({"name": d.name,
                                                  "rssi": d.rssi,
                                                  "address": d.address,
                                                  "last_seen": datetime.datetime.now()},
                                                 index=[d.address])],
                                   ignore_index=False)
                    df.loc[d.address, "distance"] = calc_distance(d.rssi)
                    df.loc[d.address, "count"] = 1
                else:
                    df.loc[d.address, "last_seen"] = datetime.datetime.now()
                    df.loc[d.address, "rssi"] = d.rssi
                    df.loc[d.address, "distance"] = calc_distance(d.rssi)
                    # increment the count
                    df.loc[d.address, "count"] += 1

            # remove stale devices (i.e. those that haven't been seen in the last
            # 30 seconds)
            # df = df[df["last_seen"] > datetime.datetime.now() -
            #         datetime.timedelta(seconds=30)]

            # adjust last_seen to be relative to now
            df["last_seen"] = datetime.datetime.now() - df["last_seen"]

            # sort the dataframe by distance lowest to highest

            df = df.sort_values(by="distance")

            # print the DataFrame using the tabulate library
            print(tabulate(df, headers="keys", tablefmt="psql"))

        except Exception as e:
            print(e)
            pass

if __name__ == "__main__":
    asyncio.run(main())
