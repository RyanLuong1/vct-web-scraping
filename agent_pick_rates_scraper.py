import requests
from bs4 import BeautifulSoup
import time
import asyncio
import pandas as pd
import time
from datetime import datetime
from WebScraper.fetch import generate_urls_combination, scraping_agents_data
from WebScraper.retrieve_urls import retrieve_urls
import aiohttp
async def main():
    semaphore_count = 25
    url_semaphore = asyncio.Semaphore(5)
    pick_rates_semaphore = asyncio.Semaphore(semaphore_count)
    year = input(f"Input the VCT year: ")

    start_time = time.time()

    now = datetime.now()

    current_time = now.strftime("%H:%M:%S")
    print("Current Time =", current_time)
    url = f"https://www.vlr.gg/vct-{year}"
    page = requests.get(url)
    soup = BeautifulSoup(page.content, "html.parser")

    urls = {}

    tournament_cards = soup.find("div", class_="events-container").find_all("div", class_="events-container-col")[-1].find_all("a", class_="wf-card mod-flex event-item")
    tournaments_ids = {}
    stages_ids = {}
    match_types_ids = {}
    retrieve_urls(urls, tournaments_ids, tournament_cards, "/event/", "/event/agents/")

    filtered_urls = {}

    async with aiohttp.ClientSession() as session:
        tasks = [generate_urls_combination(tournament_name, stages_ids, match_types_ids, url, filtered_urls, url_semaphore, session) for tournament_name, url in urls.items()]
        await asyncio.gather(*tasks)

    async with aiohttp.ClientSession() as session:
        tasks = [scraping_agents_data(tournament_name, stages, pick_rates_semaphore, session) for tournament_name, stages in filtered_urls.items()]
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
                                    
                                    for map_name, teams in teams_pick_rates.items():
                                            for team_name, totals in teams.items():
                                                total_maps_played = totals["Total Maps Played"]
                                                total_outcomes = totals["Total Outcomes"]
                                                for agent, outcome in total_outcomes.items():
                                                    all_results["teams_picked_agents"].append([tournament_name, stage_name, match_type_name, map_name, team_name,
                                                                                                agent, outcome["win"], outcome["loss"], total_maps_played])
    

    dataframes["maps_stats"] = pd.DataFrame(all_results["maps_stats"],
                                           columns=["Tournament", "Stage", "Match Type", "Map", "Total Maps Played",
                                                    "Attacker Side Win Percentage", "Defender Side Win Percentage"])
    dataframes["agents_pick_rates"] = pd.DataFrame(all_results["agents_pick_rates"],
                                                   columns=["Tournament", "Stage", "Match Type", "Map", "Agent", "Pick Rate"])
    dataframes["teams_picked_agents"] = pd.DataFrame(all_results["teams_picked_agents"],
                                                     columns=["Tournament", "Stage", "Match Type", "Map", "Team", "Agent",
                                                            "Total Wins By Map", "Total Loss By Map", "Total Maps Played"])
    dataframes["tournaments_stages_match_types_ids"] = pd.DataFrame(all_results["tournaments_stages_match_types_ids"],
                                                                    columns=["Tournament", "Tournament ID", "Stage", "Stage ID", "Match Type", "Match Type ID"])
    



    end_time = time.time()
    elasped_time = end_time - start_time

    hours, remainder = divmod(elasped_time, 3600)
    minutes, seconds = divmod(remainder, 60)

    print(f"Datascraping time: {int(hours)} hours, {int(minutes)} minutes, {int(seconds)} seconds")

    for file_name, dataframe in dataframes.items():
        if "ids" in file_name:
            dataframe.to_csv(f"vct_{year}/ids/{file_name}.csv", encoding="utf-8", index=False)
        else:
            dataframe.to_csv(f"vct_{year}/agents/{file_name}.csv", encoding="utf-8", index=False)

    current_time = now.strftime("%H:%M:%S")
    print("End Time =", current_time)



if __name__ == "__main__":
    asyncio.run(main())
