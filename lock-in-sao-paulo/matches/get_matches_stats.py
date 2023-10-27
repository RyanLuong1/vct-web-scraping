import requests
from bs4 import BeautifulSoup, Tag, NavigableString, Comment
import re
import time
import pprint
import csv


def remove_special_characters(input_string, pattern):
    
    # Use the sub() method to replace all matched characters with an empty string
    cleaned_string = re.sub(pattern, '', input_string)
    return cleaned_string

url = "https://www.vlr.gg/vct-2023"
page = requests.get(url)
soup = BeautifulSoup(page.content, "html.parser")

urls = {}

tournament_cards = soup.find_all("a", class_="wf-card mod-flex event-item")

for card in tournament_cards:
    href = card.get("href")
    matches_url = "https://www.vlr.gg" + href.replace("/event/", "/event/matches/")
    tournament = card.find("div", class_="event-item-title").text.strip().split(": ")
    if len(tournament) == 2:
        tournament_name = tournament[1]
    else:
        tournament_name = tournament[0]
    if tournament_name == "LOCK//IN São Paulo":
        tournament_name = "Lock-In Sao Paulo"

    urls[tournament_name] = matches_url

matches_cards = {}

for tournament, url in urls.items():
    page = requests.get(url)

    soup = BeautifulSoup(page.content, "html.parser")

    all_cards = soup.select('div.wf-card:not([class*=" "])')
    modules = []
    for cards in all_cards:
        all_modules = cards.find_all("a")
        modules.extend(all_modules)
    matches_cards[tournament] = modules


matches_stats = {}

overview_stats_titles = []
performance_stats_title = []
economy_stats_title = []
overview, performance, economy = "Overview", "Performance", "Economy"
specific_kills_name = ["All Kills", "First Kills", "Op Kills"]
eco_types = {"": "Eco: 0-5k", "$": "Semi-eco: 5-10k", "$$": "Semi-buy: 10-20k", "$$$": "Full buy: 20k+"}


for tournament, cards in matches_cards.items():
    tournament_dict = matches_stats.setdefault(tournament, {})
    for module in cards[:2]:
        match_type, stage = module.find("div", class_="match-item-event text-of").text.strip().splitlines()
        match_type = match_type.strip("\t")
        stage = stage.strip("\t")
        if match_type == "Showmatch":
            continue
        else:
            loser, loser_flag, loser_score = module.find("div", class_="match-item-vs").select('div.match-item-vs-team:not([class*=" "])')[0].find_all("div")
            loser = loser.text.strip("\n").strip("\t")
            loser_score = loser_score.text.strip("\n").strip("\t")

            winner, winner_flag, winner_score = module.find("div", class_="match-item-vs").find("div", class_="match-item-vs-team mod-winner").find_all("div")
            winner = winner.text.strip("\n").strip("\t")
            winner_score = winner_score.text.strip("\n").strip("\t")

            teams = module.find("div", class_="match-item-vs").find_all(recursive=False)

            team_a = teams[0].find("div").text.strip("\n").strip("\t")

            team_b = teams[1].find("div").text.strip("\n").strip("\t")


            match_name = f"{team_a} vs {team_b}"
            stage_dict = tournament_dict.setdefault(stage, {})

            match_type_dict = stage_dict.setdefault(match_type, {})
            match_dict = match_type_dict.setdefault(match_name, {})

            match_dict["Winner"] = winner
            match_dict["Loser"] = loser
            match_dict["Score"] = {winner: winner_score, loser: loser_score}

            url = module.get("href")
            match_page = requests.get(f'https://vlr.gg{url}')
            match_soup = BeautifulSoup(match_page.content, "html.parser")

            if not overview_stats_titles:
                overview_stats_titles = ["", ""]

                all_ths = match_soup.find("tr").find_all("th")[2:]
                for th in all_ths:
                    title = th.get("title")
                    overview_stats_titles.append(title)
                overview_stats_titles[7] += " (KD)"
                overview_stats_titles[13] += " (FKD)"
                print(overview_stats_titles)
            maps_id = {}
            
            maps_id_divs = match_soup.find("div", class_="vm-stats-gamesnav").find_all("div")
            for div in maps_id_divs:
                if div.get("data-game-id"):
                    id = div.get("data-game-id")
                else:
                    id = ""
                map = re.sub(r"\d+|\t|\n", "", div.text.strip())
                maps_id[id] = map

            maps_notes = match_soup.find("div", class_="match-header-note").text.strip().split("; ")

            for note in maps_notes:
                if "ban" in note or "pick" in note:
                    team, action, map = note.split()
                    draft_phase_dict = match_dict.setdefault(action, {})
                    team_dict = draft_phase_dict.setdefault(team, [])
                    team_dict.append(map)

            overview_dict = match_dict.setdefault(overview, {})
            overview_stats = match_soup.find_all("div", class_="vm-stats-game")
            for stats in overview_stats:
                id = stats.get("data-game-id")
                map = maps_id[id]
                map_dict = overview_dict.setdefault(map, {})
                tds = stats.select("table tbody tr td")
                for index, td in enumerate(tds):
                    td_class = td.get("class") or ""
                    class_name = " ".join(td_class)
                    if class_name == "mod-player":
                        player, team = td.find("a").find_all("div")
                        player, team =  player.text.strip(), team.text.strip()
                        team_dict = map_dict.setdefault(team, {})
                        player_dict = team_dict.setdefault(player, {})
                    elif class_name == "mod-agents":
                        imgs = td.find_all("img")
                        agents_played = []
                        for img in imgs:
                            agent = img.get("alt")
                            agents_played.append(agent)
                        agents = ", ".join(agents_played)
                        player_dict["agents"] = agents
                    elif class_name in ["mod-stat mod-vlr-kills", "mod-stat", "mod-stat mod-vlr-assists", "mod-stat mod-kd-diff",
                                        "mod-stat mod-fb", "mod-stat mod-fd", "mod-stat mod-fk-diff"]:
                        stats = td.find("span").find_all("span")
                        if len(stats) == 3:
                            all_stat, attack_stat, defend_stat = stats
                            all_stat, attack_stat, defend_stat = all_stat.text.strip(), attack_stat.text.strip(), defend_stat.text.strip()
                            stat_name = overview_stats_titles[index % len(overview_stats_titles)]
                            player_dict[stat_name] = {"all": all_stat, "attack": attack_stat, "defend": defend_stat}
                        else:
                            all_stat = stats[0]
                            all_stat = all_stat.text.strip()
                            stat_name = overview_stats_titles[index % len(overview_stats_titles)]
                            player_dict[stat_name] = {"all": all_stat, "attack": "", "defend": ""}
                    elif class_name == "mod-stat mod-vlr-deaths":
                        stats = td.find("span").find_all("span")[1].find_all("span")
                        if len(stats) == 3:
                            all_stat, attack_stat, defend_stat = td.find("span").find_all("span")[1].find_all("span")
                            all_stat, attack_stat, defend_stat = all_stat.text.strip(), attack_stat.text.strip(), defend_stat.text.strip()
                            stat_name = overview_stats_titles[index % len(overview_stats_titles)]
                            player_dict[stat_name] = {"all": all_stat, "attack": attack_stat, "defend": defend_stat}
                        else:
                            all_stat = stats[0]
                            all_stat = all_stat.text.strip()
                            stat_name = overview_stats_titles[index % len(overview_stats_titles)]
                            player_dict[stat_name] = {"all": all_stat, "attack": "", "defend": ""}

            performance_page = requests.get(f'https://vlr.gg{url}/?game=all&tab=performance')
            performance_soup = BeautifulSoup(performance_page.content, "html.parser")
            performance_stats_div = performance_soup.find_all("div", class_="vm-stats-game")

            if not performance_stats_title:
                performance_stats_title = ["", ""]
                print(tournament, stage, match_type, match_name)
                all_ths = performance_soup.find("table", class_="wf-table-inset mod-adv-stats").find("tr").find_all("th")[2:]
                for th in all_ths:
                    title = th.text.strip()
                    performance_stats_title.append(title)
            

            team_b_div = performance_stats_div[1].find("div").find("tr").find_all("div", class_="team")
            team_b_players = [""]
            team_b_players_lookup = {}
            team_a_players_lookup = {}
            for player in team_b_div:
                player = player.text.strip().replace("\t", "").replace("\n", "").strip(f"{team}")
                team_b_players_lookup[player] = team
                team_b_players.append(player)

            players_to_players_kills = {}
            players_kills = {}

            for div in performance_stats_div:
                kills_table = div.find("table", "wf-table-inset mod-adv-stats")
                if kills_table != None:
                    id = div.get("data-game-id")
                    players_to_players_kills[id] = []
                    players_kills[id] = []
                    players_to_players_kills_tables = div.find("div").find_all("table")
                    kills_trs = kills_table.find_all("tr")[1:]
                    for table in players_to_players_kills_tables:
                        trs = table.find_all("tr")[1:]
                        for tr in trs:
                            tds = tr.find_all("td")
                            players_to_players_kills[id].append(tds)
                    for tr in kills_trs:
                        tds = tr.find_all("td")
                        players_kills[id].extend(tds)
                else:
                    continue
            
            performance_dict = match_dict.setdefault(performance, {})

            for kill_name in specific_kills_name:
                performance_dict[kill_name] = {}

            for id, tds_list in players_to_players_kills.items():
                map = maps_id[id]
                for index, td_list in enumerate(tds_list):
                    for team_b_player_index, td in enumerate(td_list):
                        if td.find("img") != None:
                            player, team = td.text.strip().replace("\t", "").split("\n")
                            kill_name = specific_kills_name[index // (len(team_b_players) - 1)]
                            map_dict = performance_dict[kill_name].setdefault(map, {})
                            team_a_players_lookup[player] = team_a
                            team_a_dict = map_dict.setdefault(team, {})
                            team_a_player_kills_dict = team_a_dict.setdefault(player , {})
                            team_b_dict = team_a_player_kills_dict.setdefault(team_b, {})
                        else:
                            kills_div = td.find("div").find_all("div")
                            team_a_player_kills, team_b_player_kills, difference = kills_div[0].text.strip(), kills_div[1].text.strip(), kills_div[2].text.strip()
                            team_b_player = team_b_players[team_b_player_index]
                            team_b_dict[team_b_player] = {"Kills to": team_a_player_kills, "Death by": team_b_player_kills, "Difference": difference}
            
            kill_stats_dict = performance_dict.setdefault("Kill Stats", {})

            for id, td_list in players_kills.items():
                map = maps_id[id]
                map_dict = kill_stats_dict.setdefault(map, {})
                for index, td in enumerate(td_list):
                    img = td.find("img")
                    if img != None:
                        class_name = " ".join(td.find("div").get("class"))
                        if class_name == "team":
                            player, team = td.text.strip().replace("\t", "").split("\n")
                            team_dict = map_dict.setdefault(team, {})
                        elif class_name == "stats-sq":
                            src = img.get("src")
                            agent = re.search(r'/(\w+)\.png', src).group(1)
                            player_dict = team_dict.setdefault(player, {})
                            player_dict["agent"] = agent
                        else:
                            stat = td.text.split()[0]
                            stat_name = performance_stats_title[index % len(performance_stats_title)]
                            rounds_divs = td.find("div").find("div").find("div").find_all("div")
                            stat_dict = player_dict.setdefault(stat_name, {})
                            stat_dict["amount"] = stat
                            for round_div in rounds_divs:
                                kills_div = round_div.find_all("div")
                                for div in kills_div:
                                    img = div.find("img")
                                    if img == None:
                                        round_stat = div.text.strip()
                                        round_dict = stat_dict.setdefault(round_stat, {})
                                    else:
                                        src = img.get("src")
                                        agent = re.search(r'/(\w+)\.png', src).group(1)
                                        victim = div.text.strip()
                                        team = team_a_players_lookup.get(victim) or team_b_players_lookup.get(victim)
                                        round_dict["team"] = team
                                        round_dict[victim] = {"agent": agent}
                                        # print(player, agent)

                    else:
                        stat = td.text.strip()
                        stat_name = performance_stats_title[index % len(performance_stats_title)]
                        player_dict[stat_name] = stat
            
            economy_page = requests.get(f'https://vlr.gg{url}/?game=all&tab=economy')
            economy_soup = BeautifulSoup(economy_page.content, "html.parser")

            economy_stats_div = economy_soup.find_all("div", class_="vm-stats-game")

            if not economy_stats_title:
                economy_stats_title = [""]
                all_ths = economy_soup.find("tr").find_all("th")[1:]
                for th in all_ths:
                    economy_stats_title.append(th.text.strip())
            

            economy_dict = match_dict.setdefault(economy, {})
            eco_stats_dict = economy_dict.setdefault("Eco Stats", {})
            eco_rounds_dict = economy_dict.setdefault("Eco Rounds", {})        
            eco_stats = {}
            eco_rounds_stats = {}

            for div in economy_stats_div:
                id = div.get("data-game-id")
                stats_div = div.find_all(recursive=False)
                if len(stats_div) == 3:
                    eco_stats[id] = []
                    eco_rounds_stats[id] = []
                    eco_stats_trs = stats_div[0].find_all("tr")[1:]
                    eco_rounds_trs = stats_div[2].find_all("tr")
                    for tr in eco_stats_trs:
                        tds = tr.find_all("td")
                        eco_stats[id].extend(tds)
                    for tr in eco_rounds_trs:
                        tds = tr.find_all("td")
                        eco_rounds_stats[id].extend(tds)
                
                elif len(stats_div) == 2:
                    eco_stats[id] = []
                    eco_rounds_stats[id] = []
                    eco_stats_trs = stats_div[0].find_all("tr")[1:]
                    for tr in eco_stats_trs:
                        tds = tr.find_all("td")
                        eco_stats[id].extend(tds)
            
            for id, td_list in eco_stats.items():
                map = maps_id[id]
                map_dict = eco_stats_dict.setdefault(map, {})
                for index, td in enumerate(td_list):
                    class_name = td.find("div").get("class")[0]
                    if class_name == "team":
                        team = td.text.strip()
                        team_dict = map_dict.setdefault(team, {})
                    else:
                        stats = td.text.strip().replace("(", "").replace(")", "").split()
                        if len(stats) > 1:
                            initiated, won = stats[0], stats[1]
                        else:
                            initiated, won = "", stats[0]
                        stat_name = economy_stats_title[index % len(economy_stats_title)]
                        team_dict[stat_name] = {"Initiated": initiated, "Won": won}

            for id, td_list in eco_rounds_stats.items():
                map = maps_id[id]
                for index, td in enumerate(td_list):
                    teams = td.find_all("div", class_="team")
                    if teams:
                        team_a, team_b = teams[0].text.strip(), teams[1].text.strip()
                        map_dict = eco_rounds_dict.setdefault(map, {})
                    else:
                        stats = td.find_all("div")
                        round = stats[0].text.strip()
                        team_a_bank = stats[1].text.strip()
                        team_a_eco_type = eco_types[stats[2].text.strip()]
                        team_b_eco_type = eco_types[stats[3].text.strip()]
                        team_b_bank = stats[4].text.strip()
                        if "mod-win" in stats[2]["class"]:
                            team_a_outcome = "Win"
                            team_b_outcome = "Lost"
                        else:
                            team_a_outcome = "Lost"
                            team_b_outcome = "Win"
                        map_dict[f"Round {round}"] = {team_a: {"Credits": team_a_bank, "Eco Type": team_a_eco_type, "Outcome": team_a_outcome}
                                                                , team_b: {"Credits": team_b_bank, "Eco Type": team_b_eco_type, "Outcome": team_b_outcome}}
    break

sides = ["all", "attack", "defend"]

with open("overview.csv", "w") as file:
    writer = csv.writer(file)
    writer.writerow(["Tournament", "Stage", "Match Type", "Player", "Team", "Agents", "Rating", "Average Combat Score",
                     "Kills", "Deaths", "Assists", "Kill - Deaths (KD)", "Kill, Assist, Trade, Survive %", "Average Damage per Round",
                     "Headshot %", "First Kills", "First Deaths", "Kills - Deaths (FKD)", "Side"])
    for tournament, stage in matches_stats.items():
        for stage_name, match_type in stage.items():
            for match_type_name, match in match_type.items():
                for match_name, values in match.items():
                    winner, loser, match_type, stage= values["Winner"], values["Loser"], match_type_name, stage_name
                    winner_score, loser_score = values["Score"].values()

                    overview = values["Overview"]

                    for map, team in overview.items():
                        for team_name, player in team.items():
                            for player_name, data in player.items():
                                agents = data["agents"]
                                rating = data["Rating"]
                                acs = data["Average Combat Score"]
                                kills = data["Kills"]
                                deaths = data["Deaths"]
                                assists = data["Assists"]
                                kills_deaths_fd = data["Kills - Deaths (KD)"]
                                kats = data["Kill, Assist, Trade, Survive %"]
                                adr = data["Average Damage per Round"]
                                headshot = data["Headshot %"]
                                first_kills = data["First Kills"]
                                first_deaths = data["First Deaths"]
                                kills_deaths_fkd = data["Kills - Deaths (FKD)"]
                                for side in sides:
                                    writer.writerow([tournament, stage, match_type, player_name, team_name, agents, rating[side],
                                                     acs[side], kills[side], deaths[side], assists[side], kills_deaths_fd[side],
                                                     kats[side], adr[side], headshot[side], first_kills[side], first_deaths[side],
                                                     kills_deaths_fkd[side], side])


                    performance = values["Performance"]
                    economy = values["Economy"]


# with open("scores.csv", "r") as file:
#     writer = csv.writer(file)
#     writer.writerow(["Winner", "Loser", "Match Type", "Stage", "Tournament", "Winner's Score", "Loser's Score"])
#     for 
# with open("scores.csv", "w") as file:
#     writer = csv.writer(file)
#     writer.writerow(["Tournament", "Stage", "Match Type", "Winner", "Loser", "Winner's Score", "Loser's Score"])
#                     writer.writerow([tournament, stage, match_type, winner, loser, winner_score, loser_score])