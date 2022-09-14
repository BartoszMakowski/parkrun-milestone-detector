from enum import Enum
import logging
from typing import Dict, List, Optional, TypedDict

from bs4 import BeautifulSoup
import requests
from tabulate import tabulate


class LocationEnum(Enum):
    CYTADELA = "poznan"
    LAS_DEBINSKI = "lasdebinski"


Parkrunner = TypedDict("Parkrunner", {"data-runs": int, "data-name": str, "data-agegroup": str, "data-event-id": int})

PARKRUN_BASE_URL = "http://www.parkrun.pl/"  # adjust to your country
LATEST_RESULTS_URL_TEMPLATE = PARKRUN_BASE_URL + "{location}/results/latestresults/"
EVENT_RESULTS_URL_TEMPLATE = PARKRUN_BASE_URL + "{location}/results/{event_id}/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36"
}

SUPPORTED_MILESTONES = {25, 50, 100, 250, 500}
SUPPORTED_JUNIOR_MILESTONES = {10}

logger = logging.getLogger()


def generate_key(parkrunner: Parkrunner) -> str:
    return f"{parkrunner['data-runs']}-{parkrunner['data-name']}-{parkrunner['data-agegroup']}"


def check_milestone(parkrunner: Parkrunner) -> bool:
    runs_count = int(parkrunner["data-runs"]) + 1
    return (
            runs_count in SUPPORTED_MILESTONES  # senior age group
            or (  # junior/unknown age group
                    (parkrunner["data-agegroup"].startswith("J") or not parkrunner["data-agegroup"])
                    and runs_count in SUPPORTED_JUNIOR_MILESTONES)
    )


def fetch_upcoming_milestones_from_event(location: LocationEnum, event_id: Optional[int]) -> (List[Dict], int):
    """
    Fetch the results for given location and event_id. Detect upcoming milestones. Return celebrants an event ID.
    The latest event is used when no event_id is given.
    """
    if event_id:
        url = EVENT_RESULTS_URL_TEMPLATE.format(location=location.value, event_id=event_id)
        logger.debug(f"fetching Parkrun #{event_id}...", url)
    else:
        url = LATEST_RESULTS_URL_TEMPLATE.format(location=location.value)
        logger.debug("fetching Parkrun #LATEST", url)

    response = requests.get(url, headers=HEADERS)
    assert response.status_code == 200, response.status_code
    soup = BeautifulSoup(response.content, features="lxml")
    table = soup.find("table", {"class": "Results-table"})
    next_celebrants = [
        finisher for finisher in table.find_all("tr", {"class": "Results-table-row"}) if check_milestone(finisher)
    ]
    if not event_id:
        event_str = soup.find("div", {"class": "Results-header"}).find("h3").find_all("span")[-1]
        event_id = int(event_str.string[1:])
    return next_celebrants, event_id


def detect_milestones(location: LocationEnum, events_limit: int) -> List[Parkrunner]:
    """
    Iterate through last "events_limit" events of given Parkrun location and detect milestones.
    """
    event_id = None
    all_celebrants = dict()
    for _ in range(events_limit):
        next_celebrants, event_id = fetch_upcoming_milestones_from_event(location=location, event_id=event_id)
        for celebrant in sorted(next_celebrants, key=lambda x: int(x["data-runs"])):
            parkrunner_key = generate_key(celebrant)
            if parkrunner_key not in all_celebrants:
                celebrant["data-event-id"] = event_id
                all_celebrants[parkrunner_key] = celebrant
        event_id -= 1
        if not event_id:
            break

    return list(all_celebrants.values())


def print_celebrants(celebrants: List[Parkrunner]) -> None:
    table = [
        [parkrunner["data-runs"], parkrunner["data-name"], parkrunner["data-agegroup"], parkrunner["data-event-id"]]
        for parkrunner in sorted(celebrants, key=lambda x: -int(x["data-runs"]))
    ]
    print(tabulate(table, headers=["Events", "Parkrunner", "Age group", "Last event ID"]))


if __name__ == "__main__":
    LOCATION = LocationEnum.CYTADELA
    EVENTS_LIMIT = 5

    milestoners = detect_milestones(location=LOCATION, events_limit=EVENTS_LIMIT)
    print_celebrants(milestoners)
