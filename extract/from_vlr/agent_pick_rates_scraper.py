from bs4 import BeautifulSoup
from datetime import datetime
from bs4 import BeautifulSoup
from utilities.WebScraper.fetch import generate_urls_combination, scraping_agents_data, fetch
from utilities.WebScraper.retrieve_urls import retrieve_urls
import pandas as pd
import time
import asyncio
import time
import io
import aiohttp
import requests
# import boto3
import numpy as np

async def main():
    year = input(f"Input the VCT year: ")
    # year = 2025
    # s3_client = boto3.client(
    #     's3'
    # )

    start_time = time.time()

    now = datetime.now()

    current_time = now.strftime("%H:%M:%S")
    print("Current Time =", current_time)
    url = f"https://www.vlr.gg/vct-{year}"
    urls = {}
    tournaments_ids = {}
    stages_ids = {}
    match_types_ids = {}
    filtered_urls = {}
    async with aiohttp.ClientSession() as session:
        page = await fetch(url, session)
        soup = BeautifulSoup(page, "html.parser")


        tournament_cards = soup.find("div", class_="events-container").find_all("div", class_="events-container-col")[-1].find_all("a", class_="wf-card mod-flex event-item")

        retrieve_urls(urls, tournaments_ids, tournament_cards, "/event/", "/event/agents/")

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




        # Generate URLs
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

        # Collect agent pick rates
        tasks = [
            scraping_agents_data(
                tournament_name,
                stages,
                session
            )
            for tournament_name, stages in filtered_urls.items()
        ]

        results = await asyncio.gather(*tasks)

    all_results = {"maps_stats": [],
                   "agents_pick_rates": [],
                   "teams_picked_agents": [],
                   "tournaments_stages_match_types_ids": []}

    dataframes = {}
    for tournament_name, stages in match_types_ids.items():
        for stage_name, match_types in stages.items():
            for match_type_name, id in match_types.items():
                tournament_id = tournaments_ids[tournament_name]
                stage_id = stages_ids[tournament_name][stage_name]
                all_results["tournaments_stages_match_types_ids"].append([tournament_name, tournament_id, stage_name, stage_id, match_type_name, id])
    for result in results:
        for inner_list in result:
            for dictionary in inner_list:
                for tournament_name, stages in dictionary.items():
                    for stage_name, match_types in stages.items():
                            for match_type_name, stats in match_types.items():
                                if match_type_name != "Total":
                                    maps_stats = stats["Maps Stats"]
                                    agents_pick_rates = stats["Agents Pick Rates"]
                                    teams_pick_rates = stats["Teams Pick Rates"]

                                    for map_name, stats in maps_stats.items():
                                        combined_list = [tournament_name, stage_name, match_type_name, map_name] + list(stats.values())
                                        all_results["maps_stats"].append(combined_list)
                                    
                                    for map_name, agents in agents_pick_rates.items():
                                        for agent_name, pick_rate in agents.items():
                                            all_results["agents_pick_rates"].append([tournament_name, stage_name, match_type_name, map_name, agent_name, pick_rate])
                                    
                                    if stage_name != "All Stages" and match_type_name != "All Match Types":

                                        for map_name, matches in teams_pick_rates.items():
                                            for match in matches:
                                                all_results["teams_picked_agents"].append([
                                                    tournament_name,
                                                    stage_name,
                                                    match_type_name,
                                                    map_name,
                                                    match["Game ID"],
                                                    match["Team"],
                                                    match["Opponent"],
                                                    match["Result"],
                                                    match["Agent 1"],
                                                    match["Agent 2"],
                                                    match["Agent 3"],
                                                    match["Agent 4"],
                                                    match["Agent 5"]
                                                ])
    

    dataframes["maps_stats"] = pd.DataFrame(all_results["maps_stats"],
                                           columns=["Tournament", "Stage", "Match Type", "Map", "Total Maps Played",
                                                    "Attacker Side Win Percentage", "Defender Side Win Percentage"])
    dataframes["agents_pick_rates"] = pd.DataFrame(all_results["agents_pick_rates"],
                                                   columns=["Tournament", "Stage", "Match Type", "Map", "Agent", "Pick Rate"])
    dataframes["teams_picked_agents"] = pd.DataFrame(
        all_results["teams_picked_agents"],
        columns=[
            "Tournament",
            "Stage",
            "Match Type",
            "Map",
            "Game ID",
            "Team",
            "Opponent",
            "Result",
            "Agent 1",
            "Agent 2",
            "Agent 3",
            "Agent 4",
            "Agent 5"
        ]
    )
    dataframes["tournaments_stages_match_types_ids"] = pd.DataFrame(all_results["tournaments_stages_match_types_ids"],
                                                                    columns=["Tournament", "Tournament ID", "Stage", "Stage ID", "Match Type", "Match Type ID"])
    
    for name in ["maps_stats", "agents_pick_rates"]:
        df = dataframes[name]

        df["Aggregation Level"] = np.select(
            [
                df["Stage"] == "All Stages",
                df["Match Type"] == "All Match Types"
            ],
            [
                "Tournament",
                "Stage"
            ],
            default="Substage"
        )


    end_time = time.time()
    elasped_time = end_time - start_time

    hours, remainder = divmod(elasped_time, 3600)
    minutes, seconds = divmod(remainder, 60)

    print(f"Datascraping time: {int(hours)} hours, {int(minutes)} minutes, {int(seconds)} seconds")

    for file_name, dataframe in dataframes.items():
        # csv_buffer = io.StringIO()
        # dataframe.to_csv(csv_buffer, index=False)
        if "ids" in file_name:
            # directory = f"vct_{year}/ids/{file_name}.csv"
            dataframe.to_csv(f"vct_{year}/ids/{file_name}.csv", encoding="utf-8", index=False)
        else:
            # directory = f"vct_{year}/agents/{file_name}.csv"
            dataframe.to_csv(f"vct_{year}/agents/{file_name}.csv", encoding="utf-8", index=False)
        # csv_buffer.seek(0)
        # s3_client.put_object(Bucket="raw-data-vct", Key=directory, Body=csv_buffer.getvalue())
        #     dataframe.to_csv(f"vct_{year}_TEST/ids/{file_name}_TEST.csv", encoding="utf-8", index=False)
        # else:
        #     dataframe.to_csv(f"vct_{year}_TEST/agents/{file_name}_TEST.csv", encoding="utf-8", index=False)

    current_time = now.strftime("%H:%M:%S")
    print("End Time =", current_time)



if __name__ == "__main__":
    asyncio.run(main())
