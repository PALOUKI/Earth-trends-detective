"""Small client for CUAHSI HIS Central and registered WaterOneFlow services."""

from __future__ import annotations

import ipaddress
import socket
import xml.etree.ElementTree as ET
from urllib.parse import urlparse

import httpx

CATALOG_URL = "https://hiscentral.cuahsi.org/webservices/hiscentral.asmx/GetSeriesCatalogForBox3"


def _text(record: ET.Element, name: str) -> str:
    for element in record.iter():
        if element.tag.rsplit("}", 1)[-1].casefold() == name.casefold():
            return (element.text or "").strip()
    return ""


async def search_series(
    bounds: tuple[float, float, float, float],
    start: str,
    end: str,
    keyword: str,
) -> list[dict[str, str | float | int]]:
    west, south, east, north = bounds
    params = {
        "xmin": west,
        "xmax": east,
        "ymin": south,
        "ymax": north,
        "sampleMedium": "",
        "dataType": "",
        "valueType": "",
        "conceptKeyword": keyword,
        "networkIDs": "",
        "beginDate": start,
        "endDate": end,
    }
    async with httpx.AsyncClient(timeout=25, follow_redirects=False) as client:
        response = await client.get(CATALOG_URL, params=params)
        response.raise_for_status()
    root = ET.fromstring(response.content)
    results = []
    for record in root.iter():
        if record.tag.rsplit("}", 1)[-1] != "SeriesRecordFull":
            continue
        try:
            latitude = float(_text(record, "latitude"))
            longitude = float(_text(record, "longitude"))
        except ValueError:
            continue
        results.append(
            {
                "id": _text(record, "SeriesCode"),
                "site": _text(record, "Sitename") or _text(record, "location"),
                "location": _text(record, "location"),
                "variable": _text(record, "VarName"),
                "variable_code": _text(record, "VarCode"),
                "unit": _text(record, "VariableUnitsAbbrev") or _text(record, "timeunits"),
                "start": _text(record, "beginDate"),
                "end": _text(record, "endDate"),
                "latitude": latitude,
                "longitude": longitude,
                "service": _text(record, "ServCode"),
                "service_url": _text(record, "ServURL"),
                "organization": _text(record, "Organization") or _text(record, "SourceOrg"),
                "value_count": int(_text(record, "ValueCount") or "0"),
            }
        )
    return results[:100]


def _public_service_url(service_url: str) -> str:
    parsed = urlparse(service_url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("This CUAHSI data service does not provide a secure HTTPS endpoint.")
    hostname = parsed.hostname.casefold()
    if not (hostname == "cuahsi.org" or hostname.endswith(".cuahsi.org")):
        raise ValueError("This series is hosted outside the CUAHSI service network.")
    try:
        addresses = {item[4][0] for item in socket.getaddrinfo(hostname, None)}
        if not addresses or any(
            not ipaddress.ip_address(address).is_global for address in addresses
        ):
            raise ValueError("The data service host is not a public address.")
    except socket.gaierror as exc:
        raise ValueError("The CUAHSI data service host could not be resolved.") from exc
    return service_url.split("?", 1)[0].rstrip("/")


async def retrieve_values(
    service_url: str,
    location: str,
    variable: str,
    start: str,
    end: str,
) -> tuple[list[str], list[float | None]]:
    base_url = _public_service_url(service_url)
    async with httpx.AsyncClient(timeout=35, follow_redirects=False) as client:
        response = await client.get(
            f"{base_url}/GetValues",
            params={
                "location": location,
                "variable": variable,
                "startDate": start,
                "endDate": end,
                "authToken": "",
            },
        )
        response.raise_for_status()
    root = ET.fromstring(response.content)
    if root.tag.rsplit("}", 1)[-1].casefold() == "string" and root.text:
        root = ET.fromstring(root.text)
    dates: list[str] = []
    values: list[float | None] = []
    for element in root.iter():
        if element.tag.rsplit("}", 1)[-1].casefold() != "value":
            continue
        raw_date = element.attrib.get("dateTime") or element.attrib.get("date")
        raw_value = element.attrib.get("dateValue") or element.attrib.get("value") or element.text
        if not raw_date:
            continue
        dates.append(raw_date)
        try:
            values.append(float(raw_value or ""))
        except ValueError:
            values.append(None)
    if not dates:
        raise ValueError("The selected CUAHSI series returned no observations for this period.")
    return dates, values
