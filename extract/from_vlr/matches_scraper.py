from utilities.WebScraper.fetch import scraping_matches_data, fetch
from utilities.WebScraper.retrieve_urls import retrieve_urls
from datetime import datetime
from bs4 import BeautifulSoup
import requests
import time
import io
# import boto3
import pandas as pd
import asyncio
import aiohttp
import sys

async def main():
    print(sys.path)
    year = input(f"Input the VCT year: ")
    # year = 2025
    start_time = time.time()

    now = datetime.now()

    current_time = now.strftime("%H:%M:%S")
    print("Current Time =", current_time)

    ### testing code
    # with open("overview_card.html", "r", encoding="utf-8") as file:
    #     soup = BeautifulSoup(file, "html.parser")
    #     card = soup.find('a')
    ### testing code ends
    # print(card)

    #original code don't forget to uncomment it

    url = f"https://www.vlr.gg/vct-{year}"
    page = requests.get(url)
    soup = BeautifulSoup(page.content, "html.parser")

    urls = {}

    tournaments_ids = {}

    # s3_client = boto3.client(
    #     's3'
    # )

    tournament_cards = soup.find("div", class_="events-container").find_all("div", class_="events-container-col")[-1].find_all("a", class_="wf-card mod-flex event-item")

    retrieve_urls(urls, tournaments_ids, tournament_cards, "/event/", "/event/matches/")

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

    matches_cards = {}

    stages_ids = {}
    async with aiohttp.ClientSession() as session:
        for tournament, url in urls.items():
            page = await fetch(url, session)
            soup = BeautifulSoup(page, "html.parser")
            stages = soup.find("div", class_="col mod-1").find_all("a")
            stages_ids[tournament] = {}
            for stage in stages:
                stage_name = stage.text.strip()
                stage_id = stage.get("href").split("/")[-1].split("=")[-1]
                stages_ids[tournament][stage_name] = stage_id
            all_cards = soup.select('div.wf-card:not([class*=" "])')
            modules = []
            for cards in all_cards:
                all_modules = cards.find_all("a")
                modules.extend(all_modules)
            matches_cards[tournament] = modules

    ###original code ends

    #remember to remove this
    # matches_cards_test = {'Valorant Champions 2026': [card]}
    # print(f"This is matches cards: {matches_cards_test}")
    #end of testing code

    dataframes = {}
    all_results = {"scores": [],
                   "maps_played": [],
                   "maps_scores": [],
                   "draft_phase": [],
                   "win_loss_methods_count": [],
                   "win_loss_methods_round_number": [],
                   "overview": [],
                   "kills": [],
                   "kills_stats": [],
                   "rounds_kills": [],
                   "eco_stats": [],
                   "eco_rounds": [],
                   "player_loadouts": [],
                   "team_mapping": {},
                   "teams_ids": {},
                   "players_ids": {},
                   "tournaments_stages_matches_games_ids": []}
    # test = {"Champions Tour Turkey Stage 1: Challengers 3": matches_cards["Champions Tour Turkey Stage 1: Challengers 3"]}

    # async with aiohttp.ClientSession() as session:
    #     tasks = [scraping_matches_data(tournament_name, cards, tournaments_ids, stages_ids, matches_semaphore, session) for tournament_name, cards in test.items()]
    #     results = await asyncio.gather(*tasks)


    async with aiohttp.ClientSession() as session:
        tasks = [
            scraping_matches_data(
                tournament_name,
                cards,
                tournaments_ids,
                stages_ids,
                session
            )
            for tournament_name, cards in matches_cards.items()
        ]

        results = await asyncio.gather(*tasks)



    for result in results:
        for dictionary in result:
            for name, data in dictionary.items():
                # if name == "maps_scores":
                #     all_results[name].extend(data)
                if name == "team_mapping" or name == "teams_ids" or name == "players_ids":
                    all_results[name].update(data)
                else:
                    all_results[name].extend(data)


    # # team_mapping = all_results["team_mapping"]

    dataframes["scores"] = pd.DataFrame(all_results["scores"],
                                        columns=["Tournament", "Stage", "Match Type", "Match Name", "Team A", "Team B", "Team A Score", "Team B Score", "Match Result"])
    dataframes["maps_played"] = pd.DataFrame(all_results["maps_played"],
                                             columns=["Tournament", "Stage", "Match Type", "Match Name", "Map"])
    dataframes["maps_scores"] = pd.DataFrame(all_results["maps_scores"],
                                                columns=["Tournament", "Stage", "Match Type", "Match Name", "Map", "Team A", "Team A Score",
                                                        "Team A Attacker Score", "Team A Defender Score", "Team A Overtime Score",
                                                        "Team B", "Team B Score", "Team B Attacker Score", "Team B Defender Score",
                                                        "Team B Overtime Score", "Duration"])
    dataframes["draft_phase"] = pd.DataFrame(all_results["draft_phase"],
                                                columns=["Tournament", "Stage", "Match Type", "Match Name", "Team", "Action", "Map"])
    dataframes["win_loss_methods_count"] = pd.DataFrame(all_results["win_loss_methods_count"],
                                                   columns=["Tournament", "Stage", "Match Type", "Match Name", "Map", "Team",
                                                           "Elimination", "Detonated", "Defused", "Time Expiry (No Plant)", "Eliminated",
                                                            "Defused Failed", "Detonation Denied", "Time Expiry (Failed to Plant)"])
    dataframes["win_loss_methods_round_number"] = pd.DataFrame(all_results["win_loss_methods_round_number"],
                                                   columns=["Tournament", "Stage", "Match Type", "Match Name", "Map", "Round Number", "Team",
                                                           "Method", "Outcome"])
    dataframes["overview"] = pd.DataFrame(all_results["overview"],
                                            columns=["Tournament", "Stage", "Match Type", "Match Name", "Map", "Player", "Team",
                                                    "Agents", "Rating", "Average Combat Score", "Kills", "Deaths",
                                                    "Assists", "Kills - Deaths (KD)", "Kill, Assist, Trade, Survive %",
                                                    "Average Damage Per Round", "Headshot %", "First Kills", "First Deaths",
                                                    "Kills - Deaths (FKD)", "Side"])
    dataframes["kills"] = pd.DataFrame(all_results["kills"],
                                        columns=["Tournament", "Stage", "Match Type", "Match Name", "Map", "Player Team",
                                                "Player", "Enemy Team", "Enemy", "Player Kills", "Enemy Kills",
                                                "Difference", "Kill Type"])
    dataframes["kills_stats"] = pd.DataFrame(all_results["kills_stats"],
                                                columns=["Tournament", "Stage", "Match Type", "Match Name", "Map", "Team",
                                                        "Player", "Agents", "2k", "3k", "4k", "5k", "1v1",
                                                        "1v2", "1v3", "1v4", "1v5", "Econ", "Spike Plants",
                                                        "Spike Defuses"])
    dataframes["rounds_kills"] = pd.DataFrame(all_results["rounds_kills"],
                                                columns=["Tournament", "Stage", "Match Type", "Match Name", "Map", "Round Number",
                                                        "Eliminator Team", "Eliminator", "Eliminator Agent", 
                                                        "Eliminated Team", "Eliminated", "Eliminated Agent", "Kill Type"])
    dataframes["eco_stats"] = pd.DataFrame(all_results["eco_stats"],
                                            columns=["Tournament", "Stage", "Match Type", "Match Name", "Map", "Team", "Type", "Initiated", "Won"])
    dataframes["eco_rounds"] = pd.DataFrame(all_results["eco_rounds"],
                                            columns=["Tournament", "Stage", "Match Type", "Match Name", "Map", "Round Number", "Team", "Loadout Value", "Remaining Credits", "Type", "Outcome"])
    dataframes["player_loadouts"] = pd.DataFrame(all_results["player_loadouts"],
                                            columns=["Tournament", "Stage", "Match Type", "Match",
                                                     "Map", "Round", "Team", "Player", "Side",
                                                     "Agent", "Credits Spent", "Credits Remaining",
                                                     "Armor", "Weapon"])
    dataframes["team_mapping"] = pd.DataFrame(list(all_results["team_mapping"].items()),
                                              columns=["Abbreviated", "Full Name"])
    dataframes["teams_ids"] = pd.DataFrame(list(all_results["teams_ids"].items()),
                                           columns=["Team", "Team ID"])
    dataframes["players_ids"] = pd.DataFrame(list(all_results["players_ids"].items()),
                                           columns=["Player", "Player ID"])
    dataframes["tournaments_stages_matches_games_ids"] = pd.DataFrame(all_results["tournaments_stages_matches_games_ids"],
                                                            columns=["Tournament", "Tournament ID", "Stage", "Stage ID",
                                                                      "Match Type", "Match Name", "Match ID", "Map", "Game ID"])

        
    end_time = time.time()
    elasped_time = end_time - start_time

    hours, remainder = divmod(elasped_time, 3600)
    minutes, seconds = divmod(remainder, 60)

    print(f"Datascraping time: {int(hours)} hours, {int(minutes)} minutes, {int(seconds)} seconds")


    start_time = time.time()

    for file_name, dataframe in dataframes.items():
        # csv_buffer = io.StringIO()
        # dataframe.to_csv(csv_buffer, index=False)
        if "ids" in file_name:
            # directory = f"vct_{year}/ids/{file_name}.csv"
            dataframe.to_csv(f"vct_{year}/ids/{file_name}.csv", encoding="utf-8", index=False)
        else:
            # directory = f"vct_{year}/matches/{file_name}.csv"
            dataframe.to_csv(f"vct_{year}/matches/{file_name}.csv", encoding="utf-8", index=False)
            # dataframe.to_csv(f"vct_{year}_TEST/ids/{file_name}_TEST.csv", encoding="utf-8", index=False)
        # else:
        #     dataframe.to_csv(f"vct_{year}_TEST/matches/{file_name}_TEST.csv", encoding="utf-8", index=False)
        # dataframe.to_csv(f"test/{file_name}.csv", encoding="utf-8", index=False)
        # csv_buffer.seek(0)
        # s3_client.put_object(Bucket="raw-data-vct", Key=directory, Body=csv_buffer.getvalue())

    end_time = time.time()

    elasped_time = end_time - start_time

    hours, remainder = divmod(elasped_time, 3600)
    minutes, seconds = divmod(remainder, 60)

    print(f"Data to CSV time: {int(hours)} hours, {int(minutes)} minutes, {int(seconds)} seconds")

    now = datetime.now()


    current_time = now.strftime("%H:%M:%S")
    print("End Time =", current_time)

if __name__ == "__main__":
    asyncio.run(main())


