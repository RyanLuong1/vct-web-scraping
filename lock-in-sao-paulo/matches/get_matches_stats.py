import requests
from bs4 import BeautifulSoup, Tag, NavigableString, Comment
import re
import time
import pprint


def remove_special_characters(input_string, pattern):
    
    # Use the sub() method to replace all matched characters with an empty string
    cleaned_string = re.sub(pattern, '', input_string)
    return cleaned_string

url = "https://www.vlr.gg/event/matches/1188/champions-tour-2023-lock-in-s-o-paulo"

matches_url = {}
matches_stats = {}
tournament = "Lock-In Sao Paulo"
matches_stats[tournament] = {}
pattern = r'/(\w+)\.png'
page = requests.get(url)

soup = BeautifulSoup(page.content, "html.parser")

all_cards = soup.select('div.wf-card:not([class*=" "])')

modules = []

for cards in all_cards:
    all_modules = cards.find_all("a")
    modules.extend(all_modules)

overview_stats_titles = []
performance_stats_title = []
economy_stats_title = []
all, attack, defend = "all", "attack", "defend"
overview, performance, economy = "overview", "performance", "economy"
specific_kills_name = ["All Kills", "First Kills", "Op Kills"]


for index, module in enumerate(modules):
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

        match_name = f"{loser} vs {winner}"

        stage_dict = matches_stats[tournament].setdefault(stage, {})

        match_type_dict = stage_dict.setdefault(match_type, {})
        match_type_dict[match_name] = {}

        url = module.get("href")
        match_page = requests.get(f'https://vlr.gg{url}')
        match_soup = BeautifulSoup(match_page.content, "html.parser")

        if not overview_stats_titles:
            overview_stats_titles = ["", ""]

            all_ths = match_soup.find("tr").find_all("th")[2:]
            for th in all_ths:
                title = th.get("title")
                overview_stats_titles.append(title)
        
        match_maps = match_soup.find("div", class_="vm-stats-gamesnav noselect").select('div[data-disabled="0"]')
        for index, map in enumerate(match_maps):
            # map = re.sub(r'\d+|\t|\n', '',map.text.strip())
            comments = map.find(string=lambda text: isinstance(text, Comment))
            comment_soup = BeautifulSoup(comments, "html.parser")
            who_picked = comment_soup.find("div", class_="pick ge-text-light").text.strip()
            if who_picked:
                who_picked = who_picked.split(":")[1].strip()
            # print(who_picked)
            match_maps[index] = (re.sub(r'\d+|\t|\n', '',map.text.strip()), who_picked)
        
        maps_id = {}
        
        maps_id_divs = match_soup.find("div", class_="vm-stats-gamesnav noselect").find_all("div")
        for div in maps_id_divs:
            if div.get("data-game-id"):
                id = div.get("data-game-id")
            else:
                id = ""
            map = re.sub(r"\d+|\t|\n", "", div.text.strip())
            maps_id[id] = map
        
        match_type_dict[match_name]["maps_picks"] = {}
        match_type_dict[match_name]["maps_bans"] = {}

        for map, team in match_maps[1:]:
            match_type_dict[match_name]["maps_picks"][team] = map

        match_type_dict[match_name][overview] = {}
        overview_stats = match_soup.find_all("div", class_="vm-stats-game")
        for stats in overview_stats:
            id = stats.get("data-game-id")
            map = maps_id[id]
            match_type_dict[match_name][overview][map] = {}
            tds = stats.select("table tbody tr td")
            for index, td in enumerate(tds):
                td_class = td.get("class") or ""
                class_name = " ".join(td_class)
                if class_name == "mod-player":
                    player, team = td.find("a").find_all("div")
                    player, team =  player.text.strip(), team.text.strip()
                    team_dict = match_type_dict[match_name][overview][map].setdefault(team, {})
                    team_dict[player] = {}
                elif class_name == "mod-agents":
                    imgs = td.find_all("img")
                    agents_played = []
                    for img in imgs:
                        agent = img.get("alt")
                        agents_played.append(agent)
                    agents = ", ".join(agents_played)
                    team_dict[player]["agents"] = agents
                elif class_name in ["mod-stat mod-vlr-kills", "mod-stat", "mod-stat mod-vlr-assists", "mod-stat mod-kd-diff",
                                    "mod-stat mod-fb", "mod-stat mod-fd", "mod-stat mod-fk-diff"]:
                    all_stat, attack_stat, defend_stat = td.find("span").find_all("span")
                    all_stat, attack_stat, defend_stat = all_stat.text.strip(), attack_stat.text.strip(), defend_stat.text.strip()
                    stat_name = overview_stats_titles[index % len(overview_stats_titles)]
                    team_dict[player][stat_name] = {"all": all_stat, "attack": attack_stat, "defend": defend_stat}
                elif class_name == "mod-stat mod-vlr-deaths":
                    all_stat, attack_stat, defend_stat = td.find("span").find_all("span")[1].find_all("span")
                    all_stat, attack_stat, defend_stat = all_stat.text.strip(), attack_stat.text.strip(), defend_stat.text.strip()
                    stat_name = overview_stats_titles[index % len(overview_stats_titles)]
                    team_dict[player][stat_name] = {"all": all_stat, "attack": attack_stat, "defend": defend_stat}
            # print(team_dict)
            # print(team_dict[player])

        # pprint.pprint(match_type_dict[match_name]["All Maps"]["KOI"])
        performance_page = requests.get(f'https://vlr.gg{url}/?game={all}&tab={performance}')
        performance_soup = BeautifulSoup(performance_page.content, "html.parser")
        # teams = performance_soup.select('div.team:not([class*=" "])')
        # print(teams)
        performance_stats_div = performance_soup.find_all("div", class_="vm-stats-game")

        if not performance_stats_title:
            performance_stats_title = ["", ""]
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

        team_b = team
        team_a = ""

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
        
        match_type_dict[match_name][performance] = {}

        for kill_name in specific_kills_name:
            match_type_dict[match_name][performance][kill_name] = {}

        for id, tds_list in players_to_players_kills.items():
            map = maps_id[id]
            for index, td_list in enumerate(tds_list):
                for team_b_player_index, td in enumerate(td_list):
                    if td.find("img") != None:
                        player, team = td.text.strip().replace("\t", "").split("\n")
                        team_a = team
                        kill_name = specific_kills_name[index // (len(team_b_players) - 1)]
                        map_dict = match_type_dict[match_name][performance][kill_name].setdefault(map, {})
                        team_a_players_lookup[player] = team_a
                        team_a_dict = map_dict.setdefault(team, {})
                        team_a_player_kills_dict = team_a_dict.setdefault(player , {})
                        team_b_dict = team_a_player_kills_dict.setdefault(team_b, {})
                    else:
                        kills_div = td.find("div").find_all("div")
                        team_a_player_kills, team_b_player_kills, difference = kills_div[0].text.strip(), kills_div[1].text.strip(), kills_div[2].text.strip()
                        team_b_player = team_b_players[team_b_player_index]
                        team_b_dict[team_b_player] = {"Kills to": team_a_player_kills, "Death by": team_b_player_kills, "Difference": difference}
        
        match_type_dict[match_name][performance]["Kill Stats"] = {}
        for id, td_list in players_kills.items():
            map = maps_id[id]
            kill_stats_dict = match_type_dict[match_name][performance]["Kill Stats"].setdefault(map, {})
            for index, td in enumerate(td_list):
                img = td.find("img")
                if img != None:
                    class_name = " ".join(td.find("div").get("class"))
                    if class_name == "team":
                        player, team = td.text.strip().replace("\t", "").split("\n")
                        team_dict = kill_stats_dict.setdefault(team, {})
                    elif class_name == "stats-sq":
                        src = img.get("src")
                        agent = re.search(r'/(\w+)\.png', src).group(1)
                        team_dict[player] = {}
                        team_dict[player]["agent"] = agent
                    else:
                        stat = td.text.split()[0]
                        stat_name = performance_stats_title[index % len(performance_stats_title)]
                        rounds_divs = td.find("div").find("div").find("div").find_all("div")
                        team_dict[player][stat_name] = {}
                        team_dict[player][stat_name]["amount"] = stat
                        for round_div in rounds_divs:
                            kills_div = round_div.find_all("div")
                            for div in kills_div:
                                img = div.find("img")
                                if img == None:
                                    round_stat = div.text.strip()
                                    team_dict[player][stat_name][round_stat] = {}
                                else:
                                    src = img.get("src")
                                    agent = re.search(r'/(\w+)\.png', src).group(1)
                                    victim = div.text.strip()
                                    team = team_a_players_lookup.get(victim) or team_b_players_lookup.get(victim)
                                    team_dict[player][stat_name][round_stat]["team"] = team
                                    team_dict[player][stat_name][round_stat][victim] = {"agent": agent}
                                    # print(player, agent)

                else:
                    stat = td.text.strip()
                    stat_name = performance_stats_title[index % len(performance_stats_title)]
                    team_dict[player][stat_name] = stat
        
        economy_page = requests.get(f'https://vlr.gg{url}/?game={all}&tab={economy}')
        economy_soup = BeautifulSoup(economy_page.content, "html.parser")

        economy_stats_div = economy_soup.find_all("div", class_="vm-stats-game")

        if not economy_stats_title:
            economy_stats_title = [""]
            all_ths = economy_soup.find("tr").find_all("th")[1:]
            for th in all_ths:
                economy_stats_title.append(th.text.strip())
        
        match_type_dict[match_name][economy] = {}
        match_type_dict[match_name][economy]["Eco Stats"] = {}
        match_type_dict[match_name][economy]["Eco Rounds"] = {}
        eco_stats = {}
        eco_rounds_stats = {}

        for div in economy_stats_div:
            id = div.get("data-game-id")
            stats_div = div.find_all(recursive=False)
            print(len(stats_div))
            if len(stats_div) == 3:
                eco_stats[id] = []
                eco_rounds_stats[id] = []
                eco_stats_trs = stats_div[0].find_all("tr")[1:]
                eco_rounds_trs = stats_div[2].find_all("tr")[1:]
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
            for index, td in enumerate(td_list):
                class_name = td.find("div").get("class")[0]
                if class_name == "team":
                    team = td.text.strip()
                    eco_stats_dict = match_type_dict[match_name][economy]["Eco Stats"].setdefault(team, {})
                else:
                    stats = td.text.strip().replace("(", "").replace(")", "").split()
                    if len(stats) > 1:
                        initiated, won = stats[0], stats[1]
                    else:
                        initiated, won = "", stats[0]
                    stat_name = economy_stats_title[index % len(economy_stats_title)]
                    eco_stats_dict[stat_name] = {"Initiated": initiated, "Won": won}

        # trs = match_soup.find_all("tr")
        # for tr in trs:
        #     for td in tr:
        #         player = ""
        #         team = ""
        #         agents = ""
        #         try:
        #             td_class = td.get('class') or ""
        #             class_name = " ".join(td_class)
        #             # print(class_name)
        #             if class_name == "mod-player":
        #                 player_info = td.find("div").find("a").find_all("div")
        #                 player = player_info[0].text
        #                 team = player_info[1].text
        #                 match_type_dict[match_name][] = {} 
        #             elif class_name == "mod-agents":
        #                 imgs = td.find("div").find_all("img")
        #                 agents_played = []
        #                 for img in imgs:
        #                     file_name = img.get("src")
        #                     match = re.search(pattern, file_name)
        #                     agent_name = match.group(1)
        #                     agents_played.append(agent_name)
        #                 if len(agents_played) == 1:
        #                     agents = agents_played[0]
        #                     players_with_one_agent_played.add(player)
        #                     players_stats[stage][player][agents] = {}
        #                     players_stats[stage][player][agents]["team"] = team
        #                 else:
        #                     agents = "multiple agents"
        #                     players_stats[stage][player][agents] = {}
        #                     players_stats[stage][player][agents]["team"] = team
        #             elif class_name == "mod-rnd" or class_name == "mod-cl" or class_name == "":
        #                 stat = remove_special_characters(td.text)
        #                 stat_name = stats_titles[index]
        #                 players_stats[stage][player][agents][stat_name] = stat
        #             elif class_name == "mod-color-sq mod-acs" or class_name ==  "mod-color-sq":
        #                 stat = td.find("div").find("span").text
        #                 stat_name = stats_titles[index]
        #                 players_stats[stage][player][agents][stat_name] = stat
        #             elif class_name == "mod-a mod-kmax":
        #                 stat = remove_special_characters(td.find("a").text)
        #                 stat_name = stats_titles[index]
        #                 players_stats[stage][player][agents][stat_name] = stat
        #         except AttributeError:
        #             continue
        break
# print(match_maps)

    