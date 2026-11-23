from bs4 import BeautifulSoup
from datetime import datetime
from utilities.WebScraper.retrieve_urls import retrieve_urls
from utilities.WebScraper.fetch import generate_urls_combination, scraping_players_stats, fetch
import time
import asyncio
import aiohttp
import pandas as pd
import requests
# import boto3
import io


stats_titles = {
    "maps": "Maps Played",
    "rnd": "Rounds Played",
    "rating": "Rating",
    "acs": "Average Combat Score",
    "kd": "Kills:Deaths",
    "kast": "Kill, Assist, Trade, Survive %",
    "adr": "Average Damage Per Round",
    "kpr": "Kills Per Round",
    "apr": "Assists Per Round",
    "fkfd": "First Kills: First Deaths",
    "fkpr": "First Kills Per Round",
    "fdpr": "First Deaths Per Round",
    "hsp": "Headshot %",
    "clp": "Clutch Success %",
    "cl": "Clutches (won/played)",
    "kmax": "Maximum Kills in a Single Map",
    "k": "Kills",
    "d": "Deaths",
    "a": "Assists",
    "fk": "First Kills",
    "fd": "First Deaths"
}

async def main():
    year = input(f"Input the VCT year: ")
    # year = 2025
    start_time = time.time()

    now = datetime.now()

    current_time = now.strftime("%H:%M:%S")
    print("Current Time =", current_time)
    team_df = pd.read_csv(f"vct_{year}/matches/team_mapping.csv")
    df = pd.read_csv(
        f"vct_{year}/matches/overview.csv",
        usecols=[
            "Player",
            "Team",
            "Tournament",
            "Stage",
            "Match Type",
            "Match Name"
        ],
        dtype=str
    )
    tournament_ids = {}
    team_player_df = df[["Player", "Team", "Tournament", "Stage", "Match Type", "Match Name"]].drop_duplicates()
    team_player_df["Match Type"] = team_player_df["Match Type"].str.strip()
    pick_rates_df = pd.read_csv(f"vct_{year}/agents/agents_pick_rates.csv")

    pick_rates_df["Pick Rate Numeric"] = pd.to_numeric(
        pick_rates_df["Pick Rate"]
        .astype(str)
        .str.replace("%", "", regex=False),
        errors="coerce"
    )

    for column in ["Tournament", "Stage", "Match Type", "Map", "Agent"]:
        pick_rates_df[column] = pick_rates_df[column].astype(str).str.strip()

    pick_rates_df["Agent"] = (
        pick_rates_df["Agent"]
        .str.lower()
        .str.replace(r"[/\s-]", "", regex=True)
    )

    filtered_urls = {}
    stages_ids = {}
    match_types_ids = {}
    # s3_client = boto3.client(
    #     's3'
    # )

    async with aiohttp.ClientSession() as session:

        url = f"https://www.vlr.gg/vct-{year}"
        page = await fetch(url, session)
        soup = BeautifulSoup(page, "html.parser")
        tournament_cards = soup.find("div", class_="events-container").find_all("div", class_="events-container-col")[-1].find_all("a", class_="wf-card mod-flex event-item")
        urls = {}

        retrieve_urls(urls, tournament_ids, tournament_cards, "/event/", "/event/stats/")

    # if os.path.exists("all_ids/all_tournaments_stages_match_types_ids.csv"):
    #     all_tournaments_df = pd.read_csv("all_ids/all_tournaments_stages_match_types_ids.csv")
    #     filtered_df = all_tournaments_df[all_tournaments_df['Year'] == int(year)]
    #     all_tournaments = set(filtered_df["Tournament"].unique())
    #     current_tournaments = set(urls.keys())
    #     new_tournaments = list(all_tournaments ^ current_tournaments)
    #     if new_tournaments:
    #         filtered_urls = {tournament: url for tournament, url in urls.items() if tournament not in all_tournaments}
    #         urls = filtered_urls
    #     else:
    #         print("No new data")
    #         sys.exit(0)


        # urls = {'Valorant Champions 2026': 'https://www.vlr.gg/event/stats/2766/valorant-champions-2026'}




        # Generate tournament/stage/match-type URLs
        tasks = [
            generate_urls_combination(
                tournament_name,
                stages_ids,
                match_types_ids,
                url,
                filtered_urls,
                session
            )
            for tournament_name, url in urls.items()
        ]

        await asyncio.gather(*tasks)

        # Collect player statistics
        tasks = [
            scraping_players_stats(
                tournament_name,
                stages,
                team_player_df,
                pick_rates_df,
                session
            )
            for tournament_name, stages in filtered_urls.items()
        ]

        results = await asyncio.gather(*tasks)
    
    all_result = []

    for result in results:
        for inner_list in result:
            for dictionary in inner_list:
                for tournament_name, stages in dictionary.items():
                    for stage_name, match_types in stages.items():
                        for match_type, teams in match_types.items():
                            for team_name, players in teams.items():
                                for player_name, agents in players.items():
                                    for agent_name, maps in agents.items():
                                        for map_name, sides in maps.items():
                                            for side_name, stats in sides.items():
                                                all_result.append({
                                                    "Tournament": tournament_name,
                                                    "Stage": stage_name,
                                                    "Match Type": match_type,
                                                    "Player": player_name,
                                                    "Teams": team_name,
                                                    "Agent": agent_name,
                                                    "Map": map_name,
                                                    "Side": side_name,
                                                    **stats
                                                })

    columns = [
        "Tournament",
        "Stage",
        "Match Type",
        "Player",
        "Teams",
        "Agent",
        "Map",
        "Side",
        "Maps Played",
        "Agent Pick Rate %",
        *[
            title
            for title in stats_titles.values()
            if title != "Maps Played"
        ]
    ]

    players_stats_df = pd.DataFrame(all_result).reindex(columns=columns)


    # Calculate agent pick rates for every stage, match type, and map
    group_cols = [
        "Tournament",
        "Stage",
        "Match Type",
        "Player",
        "Teams",
        "Map"
    ]

    # Only use Both because Maps Played is the same across sides
    both_df = players_stats_df[
        players_stats_df["Side"] == "Both"
    ].copy()

    both_df["Maps Played"] = pd.to_numeric(
        both_df["Maps Played"],
        errors="coerce"
    )

    # Total maps played for each player within the selected filters
    totals = both_df[
        both_df["Agent"] == "All Agents"
    ][group_cols + ["Maps Played"]].rename(
        columns={"Maps Played": "Total Maps Played"}
    )

    if totals.duplicated(group_cols).any():
        raise ValueError("Duplicate All Agents records found")

    # Individual-agent maps played
    agent_rows = both_df[
        both_df["Agent"] != "All Agents"
    ][group_cols + ["Agent", "Maps Played"]].copy()

    agent_rows = agent_rows.merge(
        totals,
        on=group_cols,
        how="left",
        validate="many_to_one"
    )

    # Ensure every individual agent has a matching All Agents record
    if agent_rows["Total Maps Played"].isna().any():
        raise ValueError(
            "Missing All Agents records for some agent statistics"
        )

    agent_rows["Agent Pick Rate %"] = (
        agent_rows["Maps Played"]
        .div(agent_rows["Total Maps Played"].replace(0, float("nan")))
        .mul(100)
        .round(2)
    )

    # Apply the calculated rates to Both, Attack, and Defense
    players_stats_df = players_stats_df.drop(
        columns=["Agent Pick Rate %"]
    ).merge(
        agent_rows[
            group_cols + ["Agent", "Agent Pick Rate %"]
        ],
        on=group_cols + ["Agent"],
        how="left",
        validate="many_to_one"
    )

    players_stats_df = players_stats_df.reindex(columns=columns)


    players_stats_df.to_csv(f"vct_{year}/players_stats/players_stats.csv", encoding="utf-8", index=False)

    end_time = time.time()
    elasped_time = end_time - start_time

    hours, remainder = divmod(elasped_time, 3600)
    minutes, seconds = divmod(remainder, 60)

    print(f"Datascraping time: {int(hours)} hours, {int(minutes)} minutes, {int(seconds)} seconds")

    current_time = now.strftime("%H:%M:%S")
    print("End Time =", current_time)

if __name__ == "__main__":
    asyncio.run(main())

