"""Read the original NASA and CALCE files into the same cycle table."""

import io
import zipfile
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from scipy.io import loadmat


def load_nasa(path):
    """Read four NASA cells. Count discharge attempts, not charge/impedance rows."""
    rows = []
    cutoffs = {"B0005": 2.7, "B0006": 2.5, "B0007": 2.2, "B0018": 2.5}
    with zipfile.ZipFile(path) as outer:
        name = next(
            n for n in outer.namelist() if n.endswith("BatteryAgingARC-FY08Q4.zip")
        )
        with zipfile.ZipFile(io.BytesIO(outer.read(name))) as archive:
            for battery, cutoff in cutoffs.items():
                records = loadmat(
                    io.BytesIO(archive.read(battery + ".mat")), simplify_cells=True
                )[battery]["cycle"]
                cycle_number = 0
                for record in records:
                    if record["type"] != "discharge":
                        continue
                    cycle_number += 1
                    data = record["data"]
                    voltage = np.asarray(data["Voltage_measured"])
                    current = np.asarray(data["Current_measured"])
                    # The last sample can be resting voltage after discharge.
                    active_voltage = voltage[current < -0.1]
                    complete = bool(
                        len(active_voltage) and active_voltage[-1] <= cutoff + 0.1
                    )
                    y, m, day, hour, minute, second = record["time"]
                    time = datetime(int(y), int(m), int(day), int(hour), int(minute))
                    time += timedelta(seconds=float(second))
                    rows.append(
                        {
                            "dataset": "NASA",
                            "battery": battery,
                            "cycle": cycle_number,
                            "original_cycle": cycle_number,
                            "time": time,
                            "capacity_Ah": float(data["Capacity"]),
                            "rated_Ah": 2.0,
                            "complete": complete,
                            "source_file": battery + ".mat",
                        }
                    )
    return pd.DataFrame(rows)


def load_calce(path, battery):
    """Read CS2_35/36. Local cycle counters restart between Excel exports."""
    rows = []
    with zipfile.ZipFile(path) as archive:
        for name in sorted(archive.namelist()):
            if not name.endswith(".xlsx"):
                continue
            print("Reading", name)
            book = pd.ExcelFile(io.BytesIO(archive.read(name)), engine="calamine")
            sheet = next(s for s in book.sheet_names if s.startswith("Channel_"))
            frame = pd.read_excel(book, sheet_name=sheet)
            frame["Date_Time"] = pd.to_datetime(frame["Date_Time"])
            for local_cycle, group in frame.groupby("Cycle_Index", sort=False):
                group = group.sort_values("Date_Time").reset_index(drop=True)
                discharge = group[
                    (group["Step_Index"] == 7) & (group["Current(A)"] < -0.01)
                ]
                if discharge.empty:
                    continue
                first = int(discharge.index[0])
                # This channel is cumulative: a maximum alone is NOT cycle capacity.
                counter = discharge["Discharge_Capacity(Ah)"].to_numpy()
                capacity = (
                    counter[-1] - group.loc[first - 1, "Discharge_Capacity(Ah)"]
                    if first > 0
                    else np.nan
                )
                complete = first > 0 and discharge["Voltage(V)"].iloc[-1] <= 2.72
                complete = complete and np.all(np.diff(counter) >= -1e-6)
                # Cross-check the counter difference against measured current.
                times = discharge["Step_Time(s)"].to_numpy()
                currents = -discharge["Current(A)"].to_numpy()
                valid_time = (
                    len(times) >= 2 and times[0] <= 65 and np.all(np.diff(times) > 0)
                )
                if valid_time:
                    integrated = (
                        np.trapezoid(np.r_[currents[0], currents], np.r_[0, times])
                        / 3600
                    )
                    complete = (
                        complete
                        and integrated > 0
                        and abs(capacity - integrated) / integrated <= 0.04
                    )
                else:
                    complete = False
                rows.append(
                    {
                        "dataset": "CALCE",
                        "battery": battery,
                        "original_cycle": int(local_cycle),
                        "time": discharge["Date_Time"].iloc[0],
                        "capacity_Ah": capacity,
                        "rated_Ah": 1.1,
                        "complete": bool(complete),
                        "source_file": name,
                    }
                )
    result = pd.DataFrame(rows).sort_values("time").reset_index(drop=True)
    # Same timestamp in repeated exports receives the same cycle number.
    # This counts observed discharge attempts, not unrecorded cycles between files.
    result["cycle"] = pd.factorize(result["time"], sort=True)[0] + 1
    return result
