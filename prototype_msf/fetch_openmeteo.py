"""
Fetch real Open-Meteo daily weather for Quebec City (lat=46.8139, lon=-71.2082).
Window: last 30 days + next 7 days.

Uses the /v1/forecast endpoint with an explicit start_date/end_date that spans
into the recent past — Open-Meteo supports this for up to ~92 past days.
"""

import json
import urllib.request
from datetime import datetime, timedelta

today = datetime.now()
start = (today - timedelta(days=30)).strftime("%Y-%m-%d")
end = (today + timedelta(days=7)).strftime("%Y-%m-%d")

url = (
    f"https://api.open-meteo.com/v1/forecast?"
    f"latitude=46.8139&longitude=-71.2082"
    f"&daily=temperature_2m_max,temperature_2m_min,temperature_2m_mean,"
    f"precipitation_sum,shortwave_radiation_sum"
    f"&start_date={start}&end_date={end}"
    f"&timezone=America%2FToronto"
)

print(f"Fetching: {url}")
print()

with urllib.request.urlopen(url) as response:
    data = json.loads(response.read())

daily = data["daily"]
print("Date | Tmax | Tmin | Tmean | Precip | Radiation")
print("-" * 65)
for i, date in enumerate(daily["time"]):
    tmax = daily["temperature_2m_max"][i]
    tmin = daily["temperature_2m_min"][i]
    tmean = daily["temperature_2m_mean"][i]
    precip = daily["precipitation_sum"][i]
    radiation = daily["shortwave_radiation_sum"][i]

    tmax_s = f"{tmax:5.1f}" if tmax is not None else "  N/A"
    tmin_s = f"{tmin:5.1f}" if tmin is not None else "  N/A"
    tmean_s = f"{tmean:5.1f}" if tmean is not None else "  N/A"
    precip_s = f"{precip:6.1f} mm" if precip is not None else "   N/A"
    radiation_s = f"{radiation:6.1f} MJ/m2" if radiation is not None else "   N/A"

    print(f"{date} | {tmax_s} | {tmin_s} | {tmean_s} | {precip_s} | {radiation_s}")

print()
print(f"Rows: {len(daily['time'])}")
