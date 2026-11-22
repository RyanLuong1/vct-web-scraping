import pandas as pd
import re
import traceback
import Levenshtein
from bs4 import Tag, Comment, BeautifulSoup
import sys
import json
from utilities.compute_stats import compute_stats

overview_stats_titles = ["", "", "Rating", "Average Combat Score", "Kills", "Deaths", "Assists", "Kills - Deaths (KD)",
                        "Kill, Assist, Trade, Survive %", "Average Damage per Round", "Headshot %", "First Kills",
                        "First Deaths", "Kills - Deaths (FKD)"]

performance_stats_title = ["", "", "2k", "3k", "4k", "5k", "1v1", "1v2", "1v3", "1v4", "1v5", "Economy", "Spike Plants", "Spike Defuse"]
economy_stats_title = ["", "Pistol Won", "Eco (won)", "$ (won)", "$$ (won)", "$$$ (won)"]
overview, performance, economy = "Overview", "Performance", "Economy"
specific_kills_name = ["All Kills", "First Kills", "Op Kills"]
eco_types = {"": "Eco: 0-5k", "$": "Semi-eco: 5-10k", "$$": "Semi-buy: 10-20k", "$$$": "Full buy: 20k+"}
# all_agents = ["astra", "breach", "brimstone", "chamber", "cypher", "deadlock", "fade", "gekko", "harbor", "iso", "jett", "kayo",
#               "killjoy", "neon", "omen", "phoenix", "raze", "reyna", "sage", "skye", "sova", "viper", "yoru", "all"]
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
methods = {"elim": "Elimination", "boom": "Detonated", "defuse": "Defused", "time": "Time Expiry (No Plant)"}

cjk_pattern = re.compile(r'[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\uff66-\uff9f]')
pattern = r'/(\w+)\.png'


def extract_games_id(games_id_divs, games_id, results, list):
    tournament_name = list[0]
    stage_name = list[1]
    match_type_name = list[2]
    match_name = list[3]
    tournament_id = list[4]
    stage_id = list[5]
    match_id = list[6]
    for div in games_id_divs:
        if div.get("data-game-id"):
            id = div.get("data-game-id")
            map = re.sub(r"\d+|\t|\n", "", div.text.strip())
            if  map != "N/A":
                games_id[id] = map
    for id, map in games_id.items():
        if map != "All Maps":
            results["maps_played"].append([tournament_name, stage_name, match_type_name, match_name, map])
            results["tournaments_stages_matches_games_ids"].append([tournament_name, tournament_id, stage_name, stage_id, match_type_name, match_name, match_id, map, id])

def extract_maps_notes(maps_notes, results, team_mapping, list):
    tournament_name = list[0]
    stage_name = list[1]
    match_type_name = list[2]
    match_name = list[3]
    try:
        if ";" in maps_notes[-1].text:
            maps_notes = maps_notes[-1].text.strip().split("; ")
            for note in maps_notes:
                if "ban" in note or "pick" in note:
                    result = note.split()
                    map = result.pop()
                    action = result.pop()
                    team = " ".join(result)
                    try:
                        team = team_mapping[team]
                    except KeyError as e:
                        # print(f"{tournament_name}, {stage_name}, {match_type_name}, {match_name} could not be consistent with the abbrievated name")
                        # print(f"The notes used the full team name {e} instead of the abbreviated team name")
                        team = min(team_mapping.values(), key=lambda x: Levenshtein.distance(team, x))
                    results["draft_phase"].append([tournament_name, stage_name, match_type_name, match_name, team, action, map])
                
        else:
            print(f"For {tournament_name}, {stage_name}, {match_type_name}, {match_name}, its notes regarding the draft phase is empty")
    except IndexError:
        print(f"For {tournament_name}, {stage_name}, {match_type_name}, {match_name}, its notes regarding the draft phase is empty")

def extract_maps_headers(maps_headers, results, list):
    tournament_name = list[0]
    stage_name = list[1]
    match_type_name = list[2]
    match_name = list[3]
    team_a = list[4]
    team_b = list[5]
    for header in maps_headers:
        left_team_header, map_header, right_team_header = header.find_all(recursive=False)
        lt_score = left_team_header.find("div", class_="score").text.strip()
        lt_rounds_scores = left_team_header.find_all("span")
        map_info = map_header.text.strip().split()
        rt_score = right_team_header.find("div", class_="score").text.strip()
        rt_rounds_scores = right_team_header.find_all("span")
        map = map_info[0]
        if map == "TBD":
            map = pd.NA

        lt_attacker_score, lt_defender_score = lt_rounds_scores[0].text.strip(), lt_rounds_scores[1].text.strip()
        rt_attacker_score, rt_defender_score = rt_rounds_scores[1].text.strip(), rt_rounds_scores[0].text.strip()
        try:
            lt_overtime_score = lt_rounds_scores[2].text.strip()
        except IndexError:
            lt_overtime_score = pd.NA
        try:
            rt_overtime_score = rt_rounds_scores[2].text.strip()
        except IndexError:
            rt_overtime_score = pd.NA
        try:
            duration = map_info[-1]
            if duration == "-" or duration == map:
                duration = pd.NA
        except IndexError:
            duration = pd.NA                


        results["maps_scores"].append([tournament_name, stage_name, match_type_name, match_name,
                                        map, team_a, lt_score, lt_attacker_score,
                                        lt_defender_score, lt_overtime_score,team_b,
                                        rt_score, rt_attacker_score, rt_defender_score,
                                        rt_overtime_score, duration])
    

def extract_methods(overview_stats, games_id, results, list):
    tournament_name = list[0]
    stage_name = list[1]
    match_type_name = list[2]
    match_name = list[3]
    team_a = list[4]
    team_b = list[5]
    for info in overview_stats:

        id = info.get("data-game-id")
        try:
            map = games_id[id]
        except KeyError:
            continue
        if pd.notna(map) and map == "All Maps":
            continue
        rounds = info.select("div.vlr-rounds-row")
        outcomes = {team_a: {"elim": 0, "boom": 0, "defuse": 0, "time": 0, "eliminated": 0, "failed_to_defuse": 0, "failed_to_detonate": 0, "failed_to_plant": 0},
                    team_b: {"elim": 0, "boom": 0, "defuse": 0, "time": 0, "eliminated": 0, "failed_to_defuse": 0, "failed_to_detonate": 0, "failed_to_plant": 0}}
        for round in rounds:
            rows = round.select("div.vlr-rounds-row-col")
            for row in rows:
                if not row.find_all("div", class_="team") and row.find("img"):
                    round_number, team_a_outcome, team_b_outcome = row.find_all("div")
                    round_number = round_number.text.strip()
                    if team_a_outcome.find("img"):
                        outcome = team_a_outcome.find("img").get("src").split("/")[-1].split(".")[0]
                        enemy_outcome = ""
                        outcomes[team_a][outcome] += 1

                        if outcome == "elim":
                            outcomes[team_b]["eliminated"] += 1
                            enemy_outcome = "Eliminated"
                        elif outcome == "boom":
                            outcomes[team_b]["failed_to_defuse"] += 1
                            enemy_outcome = "Failed Defused"
                        elif outcome == "defuse":
                            outcomes[team_b]["failed_to_detonate"] += 1
                            enemy_outcome = "Detonated Denied"
                        elif outcome == "time":
                            outcomes[team_b]["failed_to_plant"] += 1
                            enemy_outcome = "Time Expiry (Failed to Plant)"
                        results["win_loss_methods_round_number"].append([tournament_name, stage_name, match_type_name, match_name, map, round_number, team_a, methods[outcome], "Win"])
                        results["win_loss_methods_round_number"].append([tournament_name, stage_name, match_type_name, match_name, map, round_number, team_b, enemy_outcome, "Loss"])
                    # else:
                    #     results["win_methods_round_number"].append([tournament_name, stage_name, match_type_name, match_name, map, round_number, team_a, "Eliminated", "Loss"])
                        # outcomes[team_a]["eliminated"] += 1
                    elif team_b_outcome.find("img"):
                        outcome = team_b_outcome.find("img").get("src").split("/")[-1].split(".")[0]
                        enemy_outcome = ""
                        outcomes[team_b][outcome] += 1

                        if outcome == "elim":
                            outcomes[team_a]["eliminated"] += 1
                            enemy_outcome = "Eliminated"
                        elif outcome == "boom":
                            outcomes[team_a]["failed_to_defuse"] += 1
                            enemy_outcome = "Failed Defused"
                        elif outcome == "defuse":
                            outcomes[team_a]["failed_to_detonate"] += 1
                            enemy_outcome = "Detonated Denied"
                        elif outcome == "time":
                            outcomes[team_a]["failed_to_plant"] += 1
                            enemy_outcome = "Time Expiry (Failed to Plant)"
                        results["win_loss_methods_round_number"].append([tournament_name, stage_name, match_type_name, match_name, map, round_number, team_b, methods[outcome], "Win"])
                        results["win_loss_methods_round_number"].append([tournament_name, stage_name, match_type_name, match_name, map, round_number, team_a, enemy_outcome, "Loss"])

                    # else:
                    #     results["win_methods_round_number"].append([tournament_name, stage_name, match_type_name, match_name, map, round_number, team_b, "Eliminated", "Loss"])
                    #     outcomes[team_b]["eliminated"] += 1
        results["win_loss_methods_count"].append([tournament_name, stage_name, match_type_name, match_name, map,
                                             team_a, outcomes[team_a]["elim"], outcomes[team_a]["boom"],
                                             outcomes[team_a]["defuse"], outcomes[team_a]["time"], outcomes[team_a]["eliminated"],
                                             outcomes[team_a]["failed_to_defuse"], outcomes[team_a]["failed_to_detonate"],
                                             outcomes[team_a]["failed_to_plant"]])
        results["win_loss_methods_count"].append([tournament_name, stage_name, match_type_name, match_name, map,
                                             team_b, outcomes[team_b]["elim"], outcomes[team_b]["boom"],
                                             outcomes[team_b]["defuse"], outcomes[team_b]["time"], outcomes[team_b]["eliminated"],
                                             outcomes[team_b]["failed_to_defuse"], outcomes[team_b]["failed_to_detonate"],
                                             outcomes[team_b]["failed_to_plant"]])
                    


        
def extract_overview_stats(overview_stats, games_id, team_mapping, results, list):
    tournament_name = list[0]
    stage_name = list[1]
    match_type_name = list[2]
    match_name = list[3]
    team_a = list[4]
    team_b = list[5]
    overview_dict = {}
    player_to_team = {}
    processed_maps = set()
    for index, stats in enumerate(overview_stats):
        id = stats.get("data-game-id")

        try:
            map = games_id[id]
        except KeyError: #match is BO1
            continue
        if map in processed_maps:
            print(
                f"Skipping repeated map: "
                f"{tournament_name} | {match_name} | "
                f"{map} | Game ID: {id}"
            )
            continue

        processed_maps.add(map)
        map_dict = overview_dict.setdefault(map, {})
        stats_tables = stats.select("div.ovw-table")

        stat_mapping = {
            "rating2": "Rating",
            "acs": "Average Combat Score",
            "kills": "Kills",
            "deaths": "Deaths",
            "assists": "Assists",
            "kd-diff": "Kills - Deaths (KD)",
            "kast": "Kill, Assist, Trade, Survive %",
            "adr": "Average Damage per Round",
            "hsp": "Headshot %",
            "fb": "First Kills",
            "fd": "First Deaths",
            "fk-diff": "Kills - Deaths (FKD)"
        }

        for table in stats_tables:
            trs = table.select("div.ovw-row:not(.mod-head)")

            for tr in trs:
                player_info = tr.select_one(".ovw-cell.mod-player")
                a_tag = player_info.find("a")

                if a_tag:
                    player_id = a_tag.get("href").split("/")[2]
                else:
                    player_id = pd.NA

                player = player_info.select_one(
                    ".ovw-player-name"
                ).get_text(strip=True)

                team = player_info.select_one(
                    ".ovw-player-tag"
                ).get_text(strip=True)

                try:
                    team = team_mapping[team]
                except KeyError:
                    if not team:
                        if cjk_pattern.search(team_a):
                            team = team_a
                        elif cjk_pattern.search(team_b):
                            team = team_b
                        else:
                            team = min(
                                team_mapping.values(),
                                key=lambda x: Levenshtein.distance(team, x)
                            )

                results["players_ids"][player] = player_id
                player_to_team[player] = team

                team_dict = map_dict.setdefault(team, {})
                player_dict = team_dict.setdefault(player, {})

                # Extract agents
                imgs = tr.select(".ovw-cell.mod-agents img")
                agents = ", ".join(img.get("alt") for img in imgs)

                if "agents" in player_dict:
                    agents = f"{player_dict['agents']}, {agents}"

                player_dict["agents"] = agents

                # Extract statistics
                stat_cells = tr.select(
                    ".ovw-cell[data-col], .ovw-kda-stat[data-col]"
                )

                for cell in stat_cells:
                    stat_col = cell.get("data-col")
                    stat_name = stat_mapping.get(stat_col)

                    if not stat_name:
                        continue

                    values = {}
                    for side, css_class in [
                        ("both", "mod-both"),
                        ("attack", "mod-t"),
                        ("defend", "mod-ct")
                    ]:
                        span = cell.select_one(f".side.{css_class}")
                        values[side] = (
                            span.get_text(strip=True)
                            if span and span.get_text(strip=True)
                            else pd.NA
                        )
                    player_dict[stat_name] = values
    sides = ["both", "attack", "defend"]
    for map_name, team in overview_dict.items():
        for team_name, player in team.items():
            for player_name, data in player.items():
                    agents = ", ".join(sorted(set(data["agents"].split(", "))))
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
                        results["overview"].append([tournament_name, stage_name, match_type_name, match_name, map_name,
                                                    player_name, team_name, agents,
                                                    rating[side], acs[side], kills[side], deaths[side], assists[side],
                                                    kills_deaths_fd[side], kats[side], adr[side], headshot[side],
                                                    first_kills[side], first_deaths[side], kills_deaths_fkd[side], side])
    return player_to_team

def extract_kills_stats(performance_stats_div, games_id, team_mapping, player_to_team, results, list):

    tournament_name, stage_name, match_type_name, match_name, team_a, team_b = list[:6]

    try:
        def get_player(team_div):
            if team_div is None:
                return pd.NA, pd.NA

            tag = team_div.select_one(".team-tag")
            abbr = tag.get_text(strip=True) if tag else ""

            # Get player name without the nested team tag
            player_div = team_div.find("div")
            player = (
                "".join(player_div.find_all(string=True, recursive=False)).strip()
                if player_div else ""
            )

            team = team_mapping.get(abbr, abbr)
            if not team or team == abbr and abbr not in team_mapping:
                if not abbr:
                    if cjk_pattern.search(team_a):
                        team = team_a
                    elif cjk_pattern.search(team_b):
                        team = team_b
                    else:
                        team = team_a
                else:
                    closest = min(
                        team_mapping.keys(),
                        key=lambda x: Levenshtein.distance(abbr, x)
                    )
                    team = team_mapping[closest]

            return player or pd.NA, team

        for div in performance_stats_div:
            id = div.get("data-game-id")

            if id not in games_id:
                continue

            map_name = games_id[id]

            # Extract kill matrices
            matrix_classes = ["mod-normal", "mod-fkfd", "mod-op"]

            for matrix_index, matrix_class in enumerate(matrix_classes):
                table = div.select_one(f"table.mod-matrix.{matrix_class}")

                if table is None:
                    continue

                rows = table.select("tr")
                if not rows:
                    continue

                headers = rows[0].find_all("td", recursive=False)
                team_b_players = [
                    get_player(td.select_one(".team"))[0]
                    for td in headers[1:]
                ]

                kill_name = specific_kills_name[matrix_index]

                for tr in rows[1:]:
                    tds = tr.find_all("td", recursive=False)
                    if not tds:
                        continue

                    player, team = get_player(
                        tds[0].select_one(".team")
                    )

                    for player_b, td in zip(team_b_players, tds[1:]):
                        kills_div = td.select("div.stats-sq")

                        if len(kills_div) < 3:
                            continue

                        player_a_kills, player_b_kills, difference = [
                            item.get_text(strip=True)
                            for item in kills_div[:3]
                        ]

                        if not any([player_a_kills, player_b_kills, difference]):
                            player_a_kills = pd.NA
                            player_b_kills = pd.NA
                            difference = pd.NA

                        results["kills"].append([
                            tournament_name, stage_name, match_type_name,
                            match_name, map_name, team, player,
                            team_b, player_b, player_a_kills,
                            player_b_kills, difference, kill_name
                        ])

            # Extract advanced performance stats
            kills_table = div.select_one("table.mod-adv-stats")

            if kills_table is None:
                continue

            for tr in kills_table.select("tr")[1:]:
                tds = tr.find_all("td", recursive=False)

                if not tds:
                    continue

                player, team = get_player(tds[0].select_one(".team"))

                agent_img = tds[1].select_one("img") if len(tds) > 1 else None
                agent = (
                    re.search(r'/(\w+)\.png', agent_img.get("src")).group(1)
                    if agent_img else pd.NA
                )

                values = [
                    tournament_name, stage_name, match_type_name,
                    match_name, map_name, team, player, agent
                ]

                for index, td in enumerate(tds[2:], start=2):
                    stat_name = performance_stats_title[
                        index % len(performance_stats_title)
                    ]

                    stat_div = td.select_one(".stats-sq")

                    if stat_div is None:
                        values.append(pd.NA)
                        continue

                    # Read only the direct text, excluding popup details
                    stat = "".join(
                        stat_div.find_all(string=True, recursive=False)
                    ).strip()

                    values.append(stat if stat else pd.NA)

                    # Extract round-by-round kills from popup
                    scope = stat_div.select_one(".vm-perf-notable-scope")

                    if scope is None:
                        continue

                    round_groups = scope.select(
                        'div[style*="margin-top: 10px"]'
                    )

                    for group in round_groups:
                        round_span = group.select_one(
                            'div[style*="white-space: nowrap"] span'
                        )

                        if round_span is None:
                            continue

                        round_stat = round_span.get_text(strip=True)

                        eliminated_divs = group.select(
                            'div[style*="align-items: center"]'
                        )

                        for eliminated_div in eliminated_divs:
                            img = eliminated_div.find("img")

                            if img is None:
                                continue

                            src = img.get("src", "")
                            match = re.search(r'/(\w+)\.png', src)
                            eliminated_agent = match.group(1) if match else pd.NA

                            eliminated = eliminated_div.get_text(strip=True)
                            eliminated = eliminated if eliminated else pd.NA

                            eliminated_team = (
                                player_to_team.get(eliminated, pd.NA)
                                if pd.notna(eliminated) else pd.NA
                            )

                            results["rounds_kills"].append([
                                tournament_name, stage_name, match_type_name,
                                match_name, map_name, round_stat,
                                team, player, agent, eliminated_team,
                                eliminated, eliminated_agent, stat_name
                            ])

                results["kills_stats"].append(values)

    except AttributeError:
        print(
            f"{tournament_name}, {stage_name}, {match_type_name}, "
            f"{match_name} does not contain performance data."
        )
    except Exception:
        print("ERROR COMING FROM SCRAPING THE PERFORMANCE PAGE")
        print(tournament_name, stage_name, match_type_name, match_name)
        traceback.print_exc()


def extract_player_loadouts(loadout_soup, games_id, team_mapping, results, list):

    tournament_name = list[0]
    stage_name = list[1]
    match_type_name = list[2]
    match_name = list[3]

    games = loadout_soup.select(".vm-stats-game[data-game-id]")

    for game in games:

        game_id = game.get("data-game-id")

        # Skip the aggregate "All" page
        if game_id == "all":
            continue

        # Skip games without replay data
        if game.select_one(".lg-empty"):
            continue

        # Convert game ID to map name
        map_name = games_id.get(str(game_id))

        if map_name is None:
            print(f"Map not found for game ID for {tournament_name}, {stage_name}, {match_type_name}, {match_name}: {game_id}")
            continue

        rounds = game.select(".lg-rounds > .lg-round[data-round]")

        if not rounds:
            continue

        for round_element in rounds:

            round_number = int(round_element["data-round"])

            teams = round_element.select(".lg-mir > .lg-mir-team")

            for team in teams:

                classes = team.get("class", [])

                if "mod-atk" in classes:
                    side = "Attack"
                elif "mod-def" in classes:
                    side = "Defense"
                else:
                    side = None

                for player_row in team.select(".lg-mir-row"):

                    player_element = player_row.select_one(".lg-mir-name")
                    team_element = player_row.select_one(".lg-mir-tag")
                    agent_element = player_row.select_one("img.lg-agent")

                    credits_spent_element = player_row.select_one(".lg-kit-spent")
                    credits_left_element = player_row.select_one(".lg-mir-left")

                    armor_element = player_row.select_one(
                        ".lg-kit-armor [title]"
                    )

                    gun_element = player_row.select_one(
                        ".lg-mir-gun img.lg-kit-gun"
                    )

                    player = (
                        player_element.get_text(strip=True)
                        if player_element else None
                    )

                    team_abbreviation = (
                        team_element.get_text(strip=True)
                        if team_element else None
                    )

                    # Convert abbreviation to full team name
                    team_name = (
                        team_mapping.get(
                            team_abbreviation,
                            team_abbreviation
                        )
                    )

                    agent = None

                    if agent_element:
                        agent = (
                            agent_element.get("src", "")
                            .rsplit("/", 1)[-1]
                            .removesuffix(".png")
                            .replace("_", "")
                            .replace("-", "")
                            .lower()
                        )

                    def parse_credits(element):
                        if element is None:
                            return None

                        value = re.sub(
                            r"[^\d]",
                            "",
                            element.get_text(strip=True)
                        )

                        return int(value) if value else None

                    credits_spent = parse_credits(credits_spent_element)
                    credits_remaining = parse_credits(credits_left_element)

                    armor = (
                        armor_element.get("title")
                        if armor_element else None
                    )

                    gun = (
                        gun_element.get("title")
                        if gun_element else None
                    )

                    results["player_loadouts"].append({
                        "Tournament": tournament_name,
                        "Stage": stage_name,
                        "Match Type": match_type_name,
                        "Match": match_name,
                        "Map": map_name,
                        "Round": round_number,
                        "Team": team_name,
                        "Player": player,
                        "Side": side,
                        "Agent": agent,
                        "Credits Spent": credits_spent,
                        "Credits Remaining": credits_remaining,
                        "Armor": armor,
                        "Weapon": gun
                    })

def extract_economy_stats_div(economy_stats_div):
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
    return eco_stats, eco_rounds_stats


def extract_economy_stats(economy_stats_div, games_id, team_mapping, results, list):
    tournament_name = list[0]
    stage_name = list[1]
    match_type_name = list[2]
    match_name = list[3]
    team_a = list[4]
    team_b = list[5]

    def resolve_team(abbr):
        if abbr in team_mapping:
            return team_mapping[abbr]
        if abbr.lower() == team_a.lower():
            return team_a
        if abbr.lower() == team_b.lower():
            return team_b
        return abbr

    def get_credits(element):
        if element is None:
            return pd.NA

        title = element.get("title", "")
        match = re.search(r"(\d+(?:\.\d+)?)k", title)

        return float(match.group(1)) * 1000 if match else pd.NA

    def get_eco_type(element):
        if element is None:
            return pd.NA

        classes = element.get("class", [])

        if "mod-bp" in classes:
            return "Pistol"
        elif "mod-b1" in classes:
            return "Eco"
        elif "mod-b2" in classes:
            return "Half Buy"
        elif "mod-b3" in classes:
            return "Full Buy"

        return pd.NA

    for div in economy_stats_div:
        id = div.get("data-game-id")

        # Handle All Maps and individual maps
        if id == "all":
            map_name = "All Maps"
        else:
            try:
                map_name = games_id[id]
            except KeyError:
                continue

        # ---------------------------------------
        # Extract team names
        # ---------------------------------------
        if id == "all":
            team_1 = team_a
            team_2 = team_b
        else:
            team_tags = div.select(
                ".vlr-rounds-row-col.mod-teams .vlr-rounds-tag"
            )

            if len(team_tags) < 2:
                continue

            team_1 = resolve_team(team_tags[0].get_text(strip=True))
            team_2 = resolve_team(team_tags[1].get_text(strip=True))

        # ---------------------------------------
        # Extract summary economy statistics
        # ---------------------------------------
        tables = div.select("table.ecm")

        for table_index, table in enumerate(tables):
            rows = table.select("tr")

            if len(rows) < 3:
                continue

            if table_index == 0:
                stat_names = ["Pistol", "Converted", "Bonus"]
            elif table_index <= 3:
                own_type = ["Eco", "Half Buy", "Full Buy"][table_index - 1]

                stat_names = [
                    f"On {own_type} vs Eco",
                    f"On {own_type} vs Half Buy",
                    f"On {own_type} vs Full Buy"
                ]
            else:
                continue

            for row_index, row in enumerate(rows[1:3]):
                team = team_1 if row_index == 0 else team_2

                cells = row.find_all("td", recursive=False)

                for stat_name, td in zip(stat_names, cells):
                    score = td.select_one(".ecm-score")

                    if score is None:
                        initiated = pd.NA
                        won = pd.NA
                    else:
                        fraction = score.get_text(strip=True).split("/")

                        if len(fraction) == 2:
                            won = fraction[0]
                            initiated = fraction[1]
                        else:
                            initiated = pd.NA
                            won = pd.NA

                    results["eco_stats"].append([
                        tournament_name,
                        stage_name,
                        match_type_name,
                        match_name,
                        map_name,
                        team,
                        stat_name,
                        initiated,
                        won
                    ])

        # All Maps only contains summary statistics
        if id == "all":
            continue

        # ---------------------------------------
        # Extract round-by-round economy stats
        # ---------------------------------------
        round_columns = div.select(".vlr-rounds-row-col")
        round_number = 0

        for column in round_columns:
            classes = column.get("class", [])

            # Skip team header and halftime separator
            if "mod-teams" in classes or "mod-spacing" in classes:
                continue

            team_1_loadout = column.select_one(".ecc-c.mod-t1")
            team_2_loadout = column.select_one(".ecc-c.mod-t2")

            if team_1_loadout is None or team_2_loadout is None:
                continue

            team_1_sq = team_1_loadout.select_one(".ecc-sq")
            team_2_sq = team_2_loadout.select_one(".ecc-sq")

            if team_1_sq is None or team_2_sq is None:
                continue

            team_1_eco_type = get_eco_type(team_1_sq)
            team_2_eco_type = get_eco_type(team_2_sq)

            # Skip empty round placeholders
            if pd.isna(team_1_eco_type) or pd.isna(team_2_eco_type):
                continue

            round_number += 1

            team_1_bank = column.select_one(".ecr-bank.mod-t1")
            team_2_bank = column.select_one(".ecr-bank.mod-t2")

            team_1_loadout_value = get_credits(team_1_loadout)
            team_2_loadout_value = get_credits(team_2_loadout)

            team_1_remaining_credits = get_credits(team_1_bank)
            team_2_remaining_credits = get_credits(team_2_bank)

            team_1_outcome = (
                "Win"
                if "mod-win" in team_1_sq.get("class", [])
                else "Loss"
            )

            team_2_outcome = (
                "Win"
                if "mod-win" in team_2_sq.get("class", [])
                else "Loss"
            )

            results["eco_rounds"].append([
                tournament_name,
                stage_name,
                match_type_name,
                match_name,
                map_name,
                round_number,
                team_1,
                team_1_loadout_value,
                team_1_remaining_credits,
                team_1_eco_type,
                team_1_outcome
            ])

            results["eco_rounds"].append([
                tournament_name,
                stage_name,
                match_type_name,
                match_name,
                map_name,
                round_number,
                team_2,
                team_2_loadout_value,
                team_2_remaining_credits,
                team_2_eco_type,
                team_2_outcome
            ])
          
    # else:
    #     print(tournament_name, stage_name, match_type_name, match_name, "does not contain any data under their economy page")

def extract_agent_pictures(agent_pictures, global_table_titles):
    for th in agent_pictures:
        src = th.find("img").get("src")
        match = re.search(pattern, src)
        agent = match.group(1)
        global_table_titles.append(agent)

def extract_pick_rates(table_stats_tr, maps_stats_dict, agents_pick_rates_dict, global_table_titles):
    # all_maps_played = []
    for tr in table_stats_tr:
        all_tds = tr.find_all("td")
        filtered_tds = [td for td in all_tds if isinstance(td, Tag)]
        for index, td in enumerate(filtered_tds):
            td_class = td.get("class") or ""
            class_name = " ".join(td_class).strip()
            if not class_name:
                map = td.text.strip().replace("\t", "")
                if not map:
                    map = "All Maps"
                else:
                    logo, map = map.split("\n")
                # if map != "All Maps":
                #     all_maps_played.append(map)
                map_stats_dict = maps_stats_dict.setdefault(map, {})
                agent_pick_rate_dict = agents_pick_rates_dict.setdefault(map, {})
            elif class_name == "mod-right":
                stat = td.text.strip()
                title = global_table_titles[index]
                map_stats_dict[title] = stat
            elif class_name == "mod-color-sq mod-center":
                stat = td.text.strip()
                agent = global_table_titles[index]
                agent_pick_rate_dict[agent] = stat
    # all_maps = ", ".join(sorted(all_maps_played))
    # maps_stats_dict[all_maps] = maps_stats_dict.pop("All Maps")
    # agents_pick_rates_dict[all_maps] = agents_pick_rates_dict.pop("All Maps")

def extract_team_picked_agents(teams_tables, teams_pick_rates_dict):

    for table in teams_tables:

        # Extract map name
        header = table.find("tr")
        map_name = header.find("th").get_text(" ", strip=True)
        map_name = re.sub(r"^[A-Z]\s+", "", map_name)

        map_records = teams_pick_rates_dict.setdefault(map_name, [])

        # Extract agent names in the order displayed
        agents = [
            img.get("title")
            for img in header.select("th img[title]")
        ]

        # Process each team
        for tr in table.select("tr.pr-matrix-row"):

            team_element = tr.select_one("td a[href^='/team/']")

            if team_element is None:
                continue

            team = team_element.get_text(" ", strip=True)

            # Extract individual map data
            script = tr.find("script", type="application/json")

            if script is None or not script.string:
                continue

            try:
                matches = json.loads(script.string)
            except json.JSONDecodeError as e:
                print(f"JSON error for {team} on {map_name}: {e}")
                continue

            for match in matches:

                outcome = match.get("result")
                opponent = match.get("opp_name")
                picks = match.get("picks", "")
                link = match.get("link", "")

                if outcome not in ("win", "loss"):
                    continue

                # Validate agent selections
                if len(picks) != len(agents):
                    print(
                        f"Agent count mismatch for {team} on {map_name}"
                    )
                    continue

                selected_agents = sorted([
                    agent
                    for agent, picked in zip(agents, picks)
                    if picked == "1"
                ])

                if len(selected_agents) != 5:
                    print(
                        f"Expected 5 agents, got {len(selected_agents)} "
                        f"for {team} on {map_name}"
                    )
                    continue

                # Extract game ID from the match URL
                game_id_match = re.search(r"[?&]game=(\d+)", link)

                game_id = (
                    game_id_match.group(1)
                    if game_id_match
                    else None
                )

                record = {
                    "Game ID": game_id,
                    "Team": team,
                    "Opponent": opponent,
                    "Result": outcome,
                    "Agent 1": selected_agents[0],
                    "Agent 2": selected_agents[1],
                    "Agent 3": selected_agents[2],
                    "Agent 4": selected_agents[3],
                    "Agent 5": selected_agents[4]
                }

                map_records.append(record)

def extract_players_stats(
    stats_trs, match_type_dict, df,
    tournament_name, stage_name, match_type_name,
    agent, map_name, side_name
):
    for tr in stats_trs:
        player_td = tr.select_one("td.mod-player")

        if player_td is None:
            continue

        player_element = player_td.select_one(".st-pl-name")
        team_element = player_td.select_one(".st-pl-country")

        if player_element is None:
            continue

        player = player_element.get_text(strip=True)
        team = (
            team_element.get_text(strip=True)
            if team_element else None
        )

        filtered = df[
            (df["Player"] == player) &
            (df["Tournament"] == tournament_name)
        ]

        if stage_name != "All Stages":
            filtered = filtered[
                filtered["Stage"] == stage_name
            ]

        if match_type_name != "All Match Types":
            filtered = filtered[
                filtered["Match Type"] == match_type_name
            ]

        teams = sorted(filtered["Team"].dropna().unique())

        if len(teams) > 0:
            team = ", ".join(teams)

        team_dict = match_type_dict.setdefault(team, {})
        player_dict = team_dict.setdefault(player, {})
        agent_dict = player_dict.setdefault(agent, {})
        map_dict = agent_dict.setdefault(map_name, {})
        stats_dict = map_dict.setdefault(side_name, {})

        for td in tr.select("td[data-col]"):
            column = td.get("data-col")

            if column not in stats_titles:
                continue

            stat_name = stats_titles[column]
            stat = td.get_text(" ", strip=True)

            stats_dict[stat_name] = stat if stat else pd.NA
