# -*- coding: utf-8 -*-

import json
import os
import sys
from datetime import datetime, timedelta
from time import sleep
from typing import Dict, Final, Iterable, List, Optional, Union

import spotipy
from rich import print
from rich.progress import Progress
from spotipy import Spotify, SpotifyOAuth


def is_playing(spotify: Spotify) -> bool:
    """check to be playing music

    Args:
        spotify (spotipy.Spotify): no descriptions.
    Returns:
        bool: playing music now -> True, else -> False
    """
    current_playing_track = spotify.currently_playing()
    if current_playing_track is None:
        return False
    return current_playing_track["is_playing"]


def total_microseconds(time: timedelta) -> int:
    """ convert from timedelta to microseconds

    Args:
        time (timedelta): timedelta object
    """
    return int(time / timedelta(microseconds=1))


def sleep_timer(
    username: str,
    client_id: str,
    client_secret: str,
    scope: Iterable[str],
    redirect_uri: str,
    music_stop_time: Union[int, float, datetime, timedelta],
    elapced_time_check_interval: Union[int, float] = 1.0,
) -> None:
    """Spotify sleep timer

    Args:
        username (str): spotify username code
        client_id (str): spotify client id code
        client_secret (str): spotify client secret code
        scope (Iterable[str]): spotify authorization scope
        redirect_uri (str): spotify client redirect uri
        music_stop_time (int|float|datetime|timedelta): timer setting
        elapsed_time_check_interval(int|float, optional): time check interval
    Raises:
        ValueError: cannot convert from music_stop_time to timedelta object
    """

    auth_manager: SpotifyOAuth = spotipy.SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=" ".join(scope),
        username=username,
    )
    spotify: Spotify = spotipy.Spotify(auth_manager=auth_manager)

    if not is_playing(spotify):
        print("does not play songs.")
        return

    stop_time: Optional[timedelta] = None
    if isinstance(music_stop_time, (int, float)):
        stop_time = timedelta(seconds=music_stop_time)
    elif isinstance(music_stop_time, datetime):
        stop_time = music_stop_time - datetime.now()
    elif isinstance(music_stop_time, timedelta):
        stop_time = music_stop_time
    else:
        raise ValueError("cannot convert stop time.")
    if stop_time < timedelta(days=0):
        raise ValueError("stopping time is before now.")

    print("start sleep timer")

    start_time: Final[datetime] = datetime.now()
    print(
        "start {} -> {} end.".format(
            start_time.strftime("%H:%M:%S"),
            (datetime.now() + stop_time).strftime("%H:%M:%S"),
        )
    )

    with Progress() as progress:
        pbar = progress.add_task(
            "will stop playing at...", total=int(stop_time / timedelta(microseconds=1))
        )

        while True:
            elapsed_time: timedelta = datetime.now() - start_time
            progress.update(pbar, completed=elapsed_time / timedelta(microseconds=1))

            if elapsed_time > stop_time:
                break

            sleep(elapced_time_check_interval)

    if is_playing(spotify):
        spotify.pause_playback()
        print("stop playing")


def get_config() -> Dict[str, Union[str, List[str]]]:
    """loads config file
    loads configs from './config.json'

    if './config.json' file does not exist,
    creates new './config.json' file with default configs
    and raises FileNotFoundException.

    Returns:
        Dict[str, str|list[str]]: loaded configs from 'config.json' file.
    Raises:
        FileNotFoundException: does not find './config.json'
    """
    if not os.path.isfile("./config.json"):
        default_config: Dict[str, Union[str, List[str]]] = {
            "username": "",
            "client_id": "",
            "client_secret": "",
            "scope": ["user-modify-playback-state", "user-read-currently-playing"],
            "redirect_uri": "http://localhost:8080",
        }
        with open("./config.json", "w", encoding="utf-8") as fp:
            json.dump(
                default_config, fp, indent=4,
            )
        raise FileNotFoundError("creates './config.json' file. please, sets values.")

    with open("./config.json", "r", encoding="utf-8") as fp:
        config: Dict[str, Union[str, List[str]]] = json.load(fp)

    return config


if __name__ == "__main__":
    stop_time: Optional[float] = None
    try:
        stop_time = float(sys.argv[1])
    except ValueError as err:
        raise ValueError(f"cannot convert input. input={sys.argv[1]}") from err
    except IndexError as err:
        raise IndexError("please input stop time") from err
    if stop_time is None:
        raise ValueError("please input stop time")

    config: Dict[str, Union[str, List[str]]] = get_config()

    sleep_timer(
        val if isinstance((val := config["username"]), str) else "",
        val if isinstance((val := config["client_id"]), str) else "",
        val if isinstance((val := config["client_secret"]), str) else "",
        val if isinstance((val := config["scope"]), Iterable) else "",
        val if isinstance((val := config["redirect_uri"]), str) else "",
        stop_time,
    )
