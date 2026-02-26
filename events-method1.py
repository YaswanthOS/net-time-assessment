#%%
# EVENT-BASED NET PLAYING TIME PIPELINE
# DFL Tracking & Event Dataset
# ==========================================

import os
import pandas as pd
import numpy as np
import warnings

warnings.filterwarnings("ignore")

from floodlight.io.dfl import read_event_data_xml, read_teamsheets_from_mat_info_xml
# %%
# Path to folder containing:
# matchinformation XML
# events_raw XML

DATA_PATH = "C:/Users/thakk/Downloads/Bassek data/"
# %%
def load_team_sheets(path):
    info_files = [x for x in os.listdir(path) if "matchinformation" in x]

    team_sheets_all = pd.DataFrame()

    for file in info_files:
        team_sheets = read_teamsheets_from_mat_info_xml(os.path.join(path, file))
        combined = pd.concat([
            team_sheets["Home"].teamsheet,
            team_sheets["Away"].teamsheet
        ])
        team_sheets_all = pd.concat([team_sheets_all, combined])

    return team_sheets_all
# %%
def load_event_data(path):

    info_files = sorted([x for x in os.listdir(path) if "matchinformation" in x])
    event_files = sorted([x for x in os.listdir(path) if "events_raw" in x])

    all_events = pd.DataFrame()

    for events_file, info_file in zip(event_files, info_files):

        events, _, _ = read_event_data_xml(
            os.path.join(path, events_file),
            os.path.join(path, info_file)
        )

        events_fullmatch = pd.DataFrame()

        for half in events:
            for team in events[half]:
                events_fullmatch = pd.concat([
                    events_fullmatch,
                    events[half][team].events
                ])

        all_events = pd.concat([all_events, events_fullmatch])

    return all_events
# %%
def prepare_half_events(events_dict, half="firstHalf", team="Home"):

    events_df = events_dict[half][team].events.copy()

    events_df = events_df.sort_values("gameclock").reset_index(drop=True)

    events_df["timestamp"] = pd.to_datetime(events_df["timestamp"])

    return events_df
# %%
RESTART_EVENT_PATTERNS = [
    "ThrowIn",
    "FreeKick",
    "GoalKick",
    "CornerKick",
    "Penalty"
]
# %%
def extract_decision_time(q):

    if isinstance(q, dict) and "DecisionTimestamp" in q:
        return pd.to_datetime(q["DecisionTimestamp"])

    return pd.NaT
# %%
def compute_restart_stoppages(events_df):

    restart_mask = events_df["eID"].str.contains("|".join(RESTART_EVENT_PATTERNS))

    restart_events = events_df[restart_mask].copy()

    restart_events["decision_time"] = restart_events["qualifier"].apply(extract_decision_time)
    restart_events["event_time"] = restart_events["timestamp"]

    restart_events["stoppage_duration"] = (
        restart_events["event_time"] - restart_events["decision_time"]
    ).dt.total_seconds()

    restart_stoppages = restart_events.dropna(subset=["stoppage_duration"])

    return restart_stoppages
# %%
def compute_goal_stoppages(events_df):

    goals = events_df[events_df["eID"] == "ShotAtGoal_SuccessfulShot"]
    kickoffs = events_df[events_df["eID"].str.contains("KickOff")]

    goal_stoppages = []

    for _, goal in goals.iterrows():

        next_kickoff = kickoffs[kickoffs["gameclock"] > goal["gameclock"]].head(1)

        if not next_kickoff.empty:
            duration = next_kickoff.iloc[0]["gameclock"] - goal["gameclock"]
            goal_stoppages.append(duration)

    return pd.Series(goal_stoppages)
# %%
def extract_var_start(q):
    if isinstance(q, dict) and "TimestampStartAction" in q:
        return pd.to_datetime(q["TimestampStartAction"])
    return pd.NaT

def extract_var_end(q):
    if isinstance(q, dict) and "TimestampEndAction" in q:
        return pd.to_datetime(q["TimestampEndAction"])
    return pd.NaT
# %%
def compute_var_stoppages(events_df):

    var_events = events_df[events_df["eID"] == "VideoAssistantAction"].copy()

    var_events["start_time"] = var_events["qualifier"].apply(extract_var_start)
    var_events["end_time"] = var_events["qualifier"].apply(extract_var_end)

    var_events["stoppage_duration"] = (
        var_events["end_time"] - var_events["start_time"]
    ).dt.total_seconds()

    var_stoppages = var_events.dropna(subset=["stoppage_duration"])

    return var_stoppages
# %%
def compute_event_based_npt(events_df):

    restart_stoppages = compute_restart_stoppages(events_df)
    goal_stoppages = compute_goal_stoppages(events_df)
    var_stoppages = compute_var_stoppages(events_df)

    total_restart = restart_stoppages["stoppage_duration"].sum()
    total_goal = goal_stoppages.sum()
    total_var = var_stoppages["stoppage_duration"].sum()

    total_stoppage_time = total_restart + total_goal + total_var

    half_duration = events_df["gameclock"].max()

    net_playing_time = half_duration - total_stoppage_time

    return {
        "half_duration": half_duration,
        "total_restart": total_restart,
        "total_goal": total_goal,
        "total_var": total_var,
        "total_stoppage": total_stoppage_time,
        "net_playing_time": net_playing_time,
        "restart_distribution": restart_stoppages["stoppage_duration"].describe(),
        "goal_distribution": goal_stoppages.describe(),
        "var_distribution": var_stoppages["stoppage_duration"].describe(),
    }
# %%
# Load dataset
all_events = load_event_data(DATA_PATH)

# Example: use one match file via floodlight again
from floodlight.io.dfl import read_event_data_xml

file_name_infos = "DFL_02_01_matchinformation_DFL-COM-000002_DFL-MAT-J03WOH.xml"
file_name_events = "DFL_03_02_events_raw_DFL-COM-000002_DFL-MAT-J03WOH.xml"

events_dict, _, _ = read_event_data_xml(
    os.path.join(DATA_PATH, file_name_events),
    os.path.join(DATA_PATH, file_name_infos)
)

events_df = prepare_half_events(events_dict, half="firstHalf", team="Home")

results = compute_event_based_npt(events_df)
# %%
print("\n===== EVENT-BASED NET PLAYING TIME =====")

print(f"Half duration (min): {results['half_duration']/60:.2f}")

print("\nRestart stoppage (min):", results["total_restart"]/60)
print("Goal stoppage (min):", results["total_goal"]/60)
print("VAR stoppage (min):", results["total_var"]/60)

print("\nTotal stoppage (min):", results["total_stoppage"]/60)
print("Net playing time (min):", results["net_playing_time"]/60)

print("\nRestart distribution:\n", results["restart_distribution"])
print("\nGoal distribution:\n", results["goal_distribution"])
print("\nVAR distribution:\n", results["var_distribution"])
# %%
