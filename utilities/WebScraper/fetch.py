import asyncio
import sys
from bs4 import BeautifulSoup, Tag
from utilities.MaxReentriesReached.max_reentries_reached import MaxReentriesReached
from utilities.WebScraper.web_data_extraction import *
from itertools import product
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
import pandas as pd
import re
import aiohttp
import random
import logging
import traceback
from aiolimiter import AsyncLimiter
import time
import statistics

rate_limiter = AsyncLimiter(5, 0.5)
request_semaphore = asyncio.Semaphore(5)
logging.basicConfig(level=logging.INFO)  # Set the desired logging level

# Define a logger
logger = logging.getLogger(__name__)

headers = {
    "User-Agent": ""
}

all_agents = ["astra", "breach", "brimstone", "chamber", "clove", "cypher", "deadlock", "fade", "gekko", "harbor", "iso", "jett", "kayo",
              "killjoy", "miks", "neon", "omen", "phoenix", "raze", "reyna", "sage", "skye", "sova", "tejo", "waylay", "veto", "viper", "vyse", "yoru", "all"]

async def fetch(url, session):
    max_retries = 3

    for attempt in range(max_retries):
        try:
            # wait_start = time.perf_counter()

            async with rate_limiter:
                # limiter_wait = time.perf_counter() - wait_start

                async with request_semaphore:
                    # request_start = time.perf_counter()

                    async with session.get(url, timeout=30) as response:
                        html = await response.text()

                    # request_time = time.perf_counter() - request_start

                    # logger.info(
                    #     f"Limiter wait: {limiter_wait:.3f}s | "
                    #     f"HTTP time: {request_time:.3f}s | "
                    #     f"URL: {url}"
                    # )

                    if response.status == 200:
                        return html

                    logger.warning(
                        f"HTTP {response.status} ({response.reason}) "
                        f"for URL: {url} "
                        f"(Attempt {attempt + 1}/{max_retries})"
                    )

                    if response.status in (403, 404):
                        break

                    if response.status == 429:
                        logger.warning(
                            f"Rate limited! Retry-After: "
                            f"{response.headers.get('Retry-After', 'Not provided')}"
                        )
                        break

        except asyncio.TimeoutError:
            logger.warning(
                f"Timeout for URL: {url} "
                f"(Attempt {attempt + 1}/{max_retries})"
            )

        except aiohttp.ClientError as e:
            logger.warning(
                f"Connection error for URL: {url} "
                f"(Attempt {attempt + 1}/{max_retries}): "
                f"{type(e).__name__}: {e}"
            )

        # Exponential backoff for retryable failures
        if attempt < max_retries - 1:
            await asyncio.sleep(2 ** attempt)

    logger.error(f"Max retries reached or request aborted for URL: {url}")
    raise MaxReentriesReached(f"Failed to fetch URL: {url}")
    

def get_active_combinations(
    pick_rates_df, tournament_name, stage_name, match_type_name
):
    scope = pick_rates_df[
        (pick_rates_df["Tournament"] == tournament_name) &
        (pick_rates_df["Stage"] == stage_name) &
        (pick_rates_df["Match Type"] == match_type_name)
    ]

    if scope.empty or scope["Pick Rate Numeric"].isna().any():
        return None

    active = scope[scope["Pick Rate Numeric"] > 0]

    return {
        "combinations": set(zip(active["Map"], active["Agent"])),
        "maps": set(active["Map"])
    }

def add_url_params(url, **params):
    parts = urlsplit(url)
    query = dict(parse_qsl(parts.query))

    for key, value in params.items():
        if value is None:
            query.pop(key, None)
        else:
            query[key] = value

    return urlunsplit((
        parts.scheme,
        parts.netloc,
        parts.path,
        urlencode(query),
        parts.fragment
    ))


def extract_filters(soup):
    agents = {
        element["data-n"]: element["value"]
        for element in soup.select('input[name="agent[]"]')
    }

    maps = {
        element["data-n"]: element["value"]
        for element in soup.select('input[name="map_id[]"]')
    }

    return agents, maps



async def generate_urls_combination(tournament_name, stages_ids, match_types_ids, url, stages_filter, session):
    try:
        page = await fetch(url, session)
    except MaxReentriesReached as e:
        print(f"Error: {e}")
        sys.exit(1)

    soup = BeautifulSoup(page, "html.parser")

    all_stages = soup.select("div.mp-pop.mod-stages div.mp-stage")

    tournament_dict = stages_filter.setdefault(tournament_name, {})
    stages_to_ids = stages_ids.setdefault(tournament_name, {})
    stages_to_match_types = match_types_ids.setdefault(tournament_name, {})

    for stage in all_stages:
        stage_input = stage.select_one('input[name="stage[]"]')

        if stage_input is None:
            continue

        stage_name = stage_input.get("data-n")
        stage_id = stage_input.get("data-grp")

        stages_to_ids[stage_name] = stage_id

        stage_dict = tournament_dict.setdefault(stage_name, {})
        match_types_to_ids = stages_to_match_types.setdefault(stage_name, {})

        match_types = stage.select('input[name="substage[]"]')

        for match_type in match_types:
            match_type_name = match_type.get("data-n")
            match_type_id = match_type.get("value")

            match_types_to_ids[match_type_name] = match_type_id
            stage_dict[match_type_name] = f"{url}?substage={match_type_id}"

        stage_dict["All Match Types"] = f"{url}?stage={stage_id}"
        match_types_to_ids["All Match Types"] = pd.NA

    tournament_dict["All Stages"] = {
        "All Match Types": url
    }

    stages_to_match_types["All Stages"] = {
        "All Match Types": pd.NA
    }

    stages_to_ids["All Stages"] = pd.NA




async def scraping_card_data(tournament_name, card, tournaments_ids, stages_ids, session):
    match_type_name, stage_name = card.find(
        "div", class_="match-item-event text-of"
    ).text.strip().splitlines()

    match_type_name = match_type_name.strip("\t")
    stage_name = stage_name.strip("\t")

    if match_type_name == "Showmatch":
        return {}

    results = {
        "scores": [],
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
        "teams_ids": {},
        "players_ids": {},
        "tournaments_stages_matches_games_ids": []
    }

    tournament_id = tournaments_ids.get(tournament_name, 0)
    stage_id = stages_ids.get(tournament_name, {}).get(stage_name, 0)

    teams = card.find("div", class_="match-item-vs").find_all(
        recursive=False
    )

    team_a = teams[0].find("div").text.strip()
    team_b = teams[1].find("div").text.strip()

    if not team_a:
        team_a = "TBD"

    if not team_b:
        team_b = "TBD"

    match_name = f"{team_a} vs {team_b}"

    try:
        team_a_score = int(
            teams[0].find(
                "div", class_="match-item-vs-team-score"
            ).text.strip()
        )
        team_b_score = int(
            teams[1].find(
                "div", class_="match-item-vs-team-score"
            ).text.strip()
        )
    except (AttributeError, ValueError):
        print(
            f"N/A SCORE: {tournament_name} | {stage_name} | "
            f"{match_type_name} | {match_name}"
        )
        return {}

    if team_a_score > team_b_score:
        match_result = f"{team_a} won"
    elif team_b_score > team_a_score:
        match_result = f"{team_b} won"
    elif team_a_score == 0 and team_b_score == 0:
        print(
            f"No score: {tournament_name} | {stage_name} | "
            f"{match_type_name} | {match_name}"
        )
        return {}
    elif "mod-winner" in teams[0].get("class", []):
        match_result = f"{team_a} won"
    elif "mod-winner" in teams[1].get("class", []):
        match_result = f"{team_b} won"
    else:
        match_result = "Draw"

    results["scores"].append([
        tournament_name, stage_name, match_type_name,
        match_name, team_a, team_b,
        team_a_score, team_b_score, match_result
    ])

    # print(
    #     "Starting collecting for",
    #     tournament_name, stage_name, match_type_name, match_name
    # )

    url = card.get("href")
    match_id = url.split("/")[1]
    base_url = f"https://vlr.gg{url}"

    team_mapping = {}

    match_info = [
        tournament_name, stage_name, match_type_name,
        match_name, team_a, team_b
    ]

    # --------------------------------------------------
    # 1. START ALL DOWNLOADS CONCURRENTLY
    # --------------------------------------------------

    download_tasks = [
        asyncio.create_task(
            fetch(base_url, session)
        ),
        asyncio.create_task(
            fetch(f"{base_url}/?game=all&tab=performance", session)
        ),
        asyncio.create_task(
            fetch(f"{base_url}/?game=all&tab=economy", session)
        ),
        asyncio.create_task(
            fetch(f"{base_url}/?game=all&tab=logs", session)
        )
    ]

    overview_task, performance_task, economy_task, loadout_task = download_tasks

    try:
        # --------------------------------------------------
        # 2. WAIT FOR OVERVIEW AND EXTRACT GAME IDS FIRST
        # --------------------------------------------------

        match_page = await overview_task
        match_soup = BeautifulSoup(match_page, "html.parser")

        team_ids_div = match_soup.find(
            "div", class_="match-header-vs"
        ).find_all("a")

        team_a_id = team_ids_div[0].get("href")
        team_b_id = team_ids_div[1].get("href")

        team_a_id = (
            team_a_id.split("/")[2]
            if team_a_id else pd.NA
        )
        team_b_id = (
            team_b_id.split("/")[2]
            if team_b_id else pd.NA
        )

        results["teams_ids"][team_a] = team_a_id
        results["teams_ids"][team_b] = team_b_id

        try:
            overview_stats = match_soup.find_all(
                "div", class_="vm-stats-game"
            )

            team_tags = match_soup.select(".ovw-player-tag")

            teams_abbriev = list(dict.fromkeys(
                tag.get_text(strip=True)
                for tag in team_tags
            ))

            team_a_abbriev, team_b_abbriev = teams_abbriev

            if team_a_abbriev not in team_mapping:
                team_mapping[team_a_abbriev] = team_a

            if team_b_abbriev not in team_mapping:
                team_mapping[team_b_abbriev] = team_b

            games_id = {}

            games_id_divs = match_soup.select(
                "div.vm-stats-gamesnav a"
            )

            if games_id_divs:
                extract_games_id(
                    games_id_divs,
                    games_id,
                    results,
                    [
                        tournament_name, stage_name,
                        match_type_name, match_name,
                        tournament_id, stage_id, match_id
                    ]
                )
            else:
                print("Only one game was played")

                map_name = overview_stats[0].find(
                    "div", class_="map"
                ).text.strip().split("\t")[0]

                if not map_name or map_name == "TBD":
                    map_name = pd.NA

                game_id = overview_stats[0].get("data-game-id")
                games_id[game_id] = map_name

                results["maps_played"].append([
                    tournament_name, stage_name,
                    match_type_name, match_name, map_name
                ])

                results["tournaments_stages_matches_games_ids"].append([
                    tournament_name, tournament_id,
                    stage_name, stage_id,
                    match_type_name, match_name,
                    match_id, map_name, game_id
                ])

            # Game IDs have now been extracted.
            # Other downloads are already running.

            maps_notes = match_soup.find_all(
                "div", class_="match-header-note"
            )

            extract_maps_notes(
                maps_notes,
                results,
                team_mapping,
                [
                    tournament_name, stage_name,
                    match_type_name, match_name
                ]
            )

            extract_methods(
                overview_stats,
                games_id,
                results,
                match_info
            )

            maps_headers = match_soup.find_all(
                "div", class_="vm-stats-game-header"
            )

            extract_maps_headers(
                maps_headers,
                results,
                match_info
            )

            player_to_team = extract_overview_stats(
                overview_stats,
                games_id,
                team_mapping,
                results,
                match_info
            )

        except IndexError:
            print("ERROR FROM SCRAPING OVERVIEW PAGE")
            print(
                f"{tournament_name}, {stage_name}, "
                f"{match_type_name}, {match_name}"
            )
            print(traceback.format_exc())
            return {}

        # --------------------------------------------------
        # 3. WAIT FOR REMAINING DOWNLOADS
        # --------------------------------------------------

        performance_page, economy_page, loadout_page = await asyncio.gather(
            performance_task,
            economy_task,
            loadout_task
        )

        # --------------------------------------------------
        # 4. EXTRACT PERFORMANCE STATISTICS
        # --------------------------------------------------

        performance_soup = BeautifulSoup(
            performance_page, "html.parser"
        )

        performance_stats_div = performance_soup.select(
            "div.vm-stats-game"
        )

        extract_kills_stats(
            performance_stats_div,
            games_id,
            team_mapping,
            player_to_team,
            results,
            match_info
        )

        # --------------------------------------------------
        # 5. EXTRACT ECONOMY STATISTICS
        # --------------------------------------------------

        economy_soup = BeautifulSoup(
            economy_page, "html.parser"
        )

        economy_stats_div = economy_soup.select(
            "div.vm-stats-game"
        )

        extract_economy_stats(
            economy_stats_div,
            games_id,
            team_mapping,
            results,
            match_info
        )

        # --------------------------------------------------
        # 6. EXTRACT LOADOUT STATISTICS
        # --------------------------------------------------

        loadout_soup = BeautifulSoup(
            loadout_page, "html.parser"
        )

        extract_player_loadouts(
            loadout_soup,
            games_id,
            team_mapping,
            results,
            [
                tournament_name, stage_name,
                match_type_name, match_name
            ]
        )

        results["team_mapping"] = team_mapping

        return results

    except MaxReentriesReached as e:
        print(
            f"Download failed: {tournament_name} | "
            f"{match_name} | {e}"
        )
        raise

    finally:
        # Cancel any downloads still running if extraction
        # fails or the function returns early.
        for task in download_tasks:
            if not task.done():
                task.cancel()

        # Collect task exceptions and finish cancellation.
        await asyncio.gather(
            *download_tasks,
            return_exceptions=True
        )




async def scraping_matches_data(tournament_name, cards, tournaments_ids, stages_ids, session):
    # card_semaphore = asyncio.Semaphore(semaphore_count)
    tasks = [scraping_card_data(tournament_name, card, tournaments_ids, stages_ids, session) for card in cards]
    results = await asyncio.gather(*tasks)
    return results


async def scraping_agents_data_match_type_helper(
    tournament_name,
    stage_name,
    match_type_name,
    url,
    session
):

    global_table_titles = [
        "Map",
        "Total Played",
        "Attacker Side Win",
        "Defender Side Win"
    ]

    result = {}

    tournament_dict = result.setdefault(tournament_name, {})
    stage_dict = tournament_dict.setdefault(stage_name, {})
    match_type_dict = stage_dict.setdefault(match_type_name, {})

    maps_stats_dict = match_type_dict.setdefault("Maps Stats", {})
    agents_pick_rates_dict = match_type_dict.setdefault("Agents Pick Rates", {})
    teams_pick_rates_dict = match_type_dict.setdefault("Teams Pick Rates", {})

    print(
        f"Collecting data for "
        f"{tournament_name}, {stage_name}, {match_type_name}"
    )

    try:
        page = await fetch(url, session)
    except MaxReentriesReached as e:
        logger.error(f"Error collecting agent data: {e}")
        return None

    soup = BeautifulSoup(page, "html.parser")

    global_maps_table = soup.find(
        "table",
        class_="wf-table mod-pr-global"
    )

    if global_maps_table is not None:

        agent_pictures = global_maps_table.find_all(
            "th",
            style=" vertical-align: middle; padding-top: 0; padding-bottom: 0; width: 65px;"
        )

        extract_agent_pictures(
            agent_pictures,
            global_table_titles
        )

        table_stats_tr = global_maps_table.find_all("tr")[1:]

        extract_pick_rates(
            table_stats_tr,
            maps_stats_dict,
            agents_pick_rates_dict,
            global_table_titles
        )

    # Updated team agent composition extraction
    teams_tables = soup.select(
        ".pr-matrix-map table.wf-table"
    )

    extract_team_picked_agents(
        teams_tables,
        teams_pick_rates_dict
    )

    await asyncio.sleep(random.uniform(0.5, 0.7))

    return result


async def scraping_agents_data_stage_helper(tournament_name, stage_name, match_types, session):
    tasks = [scraping_agents_data_match_type_helper(tournament_name, stage_name, match_type_name, url, session) for match_type_name, url in match_types.items()]
    results = await asyncio.gather(*tasks)
    return results

async def scraping_agents_data(tournament_name, stages, session): 
    tasks = [scraping_agents_data_stage_helper(tournament_name, stage_name, match_types, session) for stage_name, match_types in stages.items()]
    results = await asyncio.gather(*tasks)
    return results



# async def processing_each_agents(match_type_dict, global_players_agents, players_agents, tournament_name, stage_name, match_type_name, url, df, agent, session ):
#     async with asyncio.Semaphore(2):
#         print(f"Collecting data for {agent} {tournament_name}, {stage_name}, {match_type_name}")
#         try:
#             page = await fetch(f"{url}&min_rounds=0&agent={agent}", session)
#         except MaxReentriesReached as e:
#             print(f"Error: {e}")
#             sys.exit(1)
#         await asyncio.sleep(random.uniform(0, 1))
#         soup = BeautifulSoup(page, "html.parser")
#         stats_trs = soup.find_all("tr")[1:]

#         if len(stats_trs) >= 1 and stats_trs[0].find("td"):
#             extract_players_stats(stats_trs, match_type_dict, global_players_agents, players_agents, df, tournament_name, stage_name, match_type_name, agent)

async def scraping_player_stats_match_type_helper(
    tournament_name, stage_name, match_type_name,
    url, team_df, agent_pick_rates_df, session
):
    """Scrape player statistics and benchmark the download/parse pipeline."""

    benchmark_start = time.perf_counter()
    result = {}
    tournament_dict = result.setdefault(tournament_name, {})
    stage_dict = tournament_dict.setdefault(stage_name, {})
    match_type_dict = stage_dict.setdefault(match_type_name, {})

    initial_url = url
    initial_fetch_start = time.perf_counter()
    try:
        page = await fetch(initial_url, session)
    except MaxReentriesReached as e:
        print(f"Error: {e}")
        raise
    initial_fetch_time = time.perf_counter() - initial_fetch_start

    initial_parse_start = time.perf_counter()
    soup = BeautifulSoup(page, "html.parser")
    initial_parse_time = time.perf_counter() - initial_parse_start

    agents, maps = extract_filters(soup)
    if not agents or not maps:
        raise ValueError(f"Agent or map filters not found: {initial_url}")

    agents = {"All Agents": None, **agents}
    maps = {"All Maps": None, **maps}
    sides = {"Both": None, "Attack": "t", "Defense": "ct"}

    active_filters = get_active_combinations(
        agent_pick_rates_df, tournament_name, stage_name, match_type_name
    )
    requests_made = 0
    requests_skipped = 0

    valid_combinations = []
    for ((agent_name, agent_id), (map_name, map_id),
         (side_name, side_id)) in product(agents.items(), maps.items(), sides.items()):
        if active_filters is not None:
            if map_name != "All Maps" and map_name not in active_filters["maps"]:
                requests_skipped += 1
                continue
            if agent_name != "All Agents":
                normalized_agent = (
                    agent_name.lower().replace("/", "")
                    .replace("-", "").replace(" ", "")
                )
                combination = (map_name, normalized_agent)
                if combination not in active_filters["combinations"]:
                    requests_skipped += 1
                    continue

        filter_url = add_url_params(
            url, agent=agent_id, map_id=map_id, side=side_id
        )
        valid_combinations.append(
            (agent_name, map_name, side_name, filter_url)
        )

    url_queue = asyncio.Queue(maxsize=100)
    html_queue = asyncio.Queue(maxsize=20)

    # Each helper owns its own measurements. The parser returns timing values
    # to the event-loop thread instead of modifying shared lists in a thread.
    download_times = []
    parse_times = []
    selection_times = []
    extraction_times = []
    queue_wait_times = []
    queue_samples = []
    queue_full_samples = 0
    queue_max_seen = 0
    queue_blocked_puts = 0
    pages_processed = 0
    pages_with_rows = 0

    async def download_worker():
        nonlocal queue_max_seen, queue_blocked_puts
        while True:
            combination = await url_queue.get()
            try:
                agent_name, map_name, side_name, filter_url = combination
                # logger.info(
                #     "Collecting %s, %s, %s | URL: %s",
                #     agent_name,
                #     map_name,
                #     side_name,
                #     filter_url
                # )

                if filter_url == initial_url:
                    html = None
                    was_downloaded = False
                else:
                    fetch_start = time.perf_counter()
                    html = await fetch(filter_url, session)
                    download_times.append(time.perf_counter() - fetch_start)
                    was_downloaded = True
                    if html is None:
                        raise ValueError(f"No HTML returned: {filter_url}")

                # Capture fullness before put(): a full queue forces this
                # downloader to wait for the parser to take an item.
                was_full = html_queue.full()
                put_start = time.perf_counter()
                await html_queue.put((combination, html, was_downloaded))
                put_wait = time.perf_counter() - put_start
                queue_wait_times.append(put_wait)
                if was_full:
                    queue_blocked_puts += 1
                queue_max_seen = max(queue_max_seen, html_queue.qsize())
            finally:
                url_queue.task_done()

    def parse_player_stats_page(combination, html, was_downloaded):
        agent_name, map_name, side_name, filter_url = combination

        parse_start = time.perf_counter()
        filtered_soup = (
            BeautifulSoup(html, "html.parser") if was_downloaded else soup
        )
        parse_elapsed = time.perf_counter() - parse_start

        selection_start = time.perf_counter()
        if filtered_soup.select_one(".st-empty"):
            return parse_elapsed, time.perf_counter() - selection_start, 0.0, False

        table = filtered_soup.select_one("#st-table")
        if table is None:
            raise ValueError(f"Player statistics table not found: {filter_url}")

        stats_trs = table.select("tbody tr")
        selection_elapsed = time.perf_counter() - selection_start
        if not stats_trs:
            return parse_elapsed, selection_elapsed, 0.0, False

        extract_start = time.perf_counter()
        extract_players_stats(
            stats_trs, match_type_dict, team_df,
            tournament_name, stage_name, match_type_name,
            agent_name, map_name, side_name
        )
        extraction_elapsed = time.perf_counter() - extract_start
        return parse_elapsed, selection_elapsed, extraction_elapsed, True

    async def parser_worker():
        nonlocal requests_made, pages_processed, pages_with_rows
        while True:
            combination, html, was_downloaded = await html_queue.get()
            try:
                (parse_elapsed, selection_elapsed,
                 extraction_elapsed, has_rows) = await asyncio.to_thread(
                    parse_player_stats_page, combination, html, was_downloaded
                )
                parse_times.append(parse_elapsed)
                selection_times.append(selection_elapsed)
                extraction_times.append(extraction_elapsed)
                pages_processed += 1
                pages_with_rows += int(has_rows)
                if was_downloaded:
                    requests_made += 1
            finally:
                html_queue.task_done()

    async def monitor_queue():
        nonlocal queue_full_samples, queue_max_seen
        while True:
            size = html_queue.qsize()
            queue_samples.append(size)
            queue_max_seen = max(queue_max_seen, size)
            if html_queue.full():
                queue_full_samples += 1
            # print(
            #     f"[QUEUE] {tournament_name} | {stage_name} | {match_type_name} "
            #     f"HTML={size}/{html_queue.maxsize} "
            #     f"URLs={url_queue.qsize()}/{url_queue.maxsize}"
            # )
            await asyncio.sleep(2)

    async def run_pipeline():
        download_workers = [
            asyncio.create_task(download_worker()) for _ in range(3)
        ]
        parser = asyncio.create_task(parser_worker())
        monitor = asyncio.create_task(monitor_queue())
        workers = download_workers + [parser]

        async def feed_urls():
            for combination in valid_combinations:
                await url_queue.put(combination)

        async def wait_for_completion():
            await feed_urls()
            await url_queue.join()
            await html_queue.join()

        completion_task = asyncio.create_task(wait_for_completion())
        try:
            done, _ = await asyncio.wait(
                workers + [completion_task],
                return_when=asyncio.FIRST_COMPLETED
            )
            for task in done:
                if task is completion_task:
                    continue
                if task.cancelled():
                    raise RuntimeError("A pipeline worker was cancelled unexpectedly")
                exception = task.exception()
                if exception is not None:
                    raise exception
                raise RuntimeError("A pipeline worker stopped unexpectedly")
            await completion_task
        finally:
            for task in workers + [completion_task, monitor]:
                task.cancel()
            await asyncio.gather(
                *workers, completion_task, monitor, return_exceptions=True
            )

    await run_pipeline()
    elapsed = time.perf_counter() - benchmark_start

    def report_timing(label, values):
        if not values:
            print(f"{label:<20} no samples")
            return
        print(
            f"{label:<20} n={len(values):<5} "
            f"avg={statistics.mean(values):.4f}s  "
            f"min={min(values):.4f}s  max={max(values):.4f}s  "
            f"sum={sum(values):.2f}s"
        )

    print("\n" + "=" * 80)
    print(f"PLAYER STATS BENCHMARK: {tournament_name} | {stage_name} | {match_type_name}")
    print("=" * 80)
    print(f"Wall-clock runtime:      {elapsed:.2f}s")
    print(f"Initial fetch:           {initial_fetch_time:.4f}s")
    print(f"Initial BeautifulSoup:   {initial_parse_time:.4f}s")
    print(f"Valid combinations:      {len(valid_combinations)}")
    print(f"Skipped combinations:    {requests_skipped}")
    print(f"Additional requests:     {requests_made}")
    print(f"Pages processed:         {pages_processed}")
    print(f"Pages containing rows:   {pages_with_rows}")
    print("\n--- TIMING (elapsed per operation; downloads include rate-limit waits) ---")
    report_timing("Fetch", download_times)
    report_timing("BeautifulSoup", parse_times)
    report_timing("CSS selection", selection_times)
    report_timing("Extraction", extraction_times)
    report_timing("HTML queue put wait", queue_wait_times)
    print("\n--- HTML QUEUE ---")
    print(f"Capacity:                {html_queue.maxsize}")
    print(f"Maximum observed:        {queue_max_seen}")
    print(f"Full when put started:   {queue_blocked_puts}/{len(queue_wait_times)}")
    if queue_samples:
        print(f"Average sampled size:    {statistics.mean(queue_samples):.2f}")
        print(f"Full monitor samples:    {queue_full_samples}/{len(queue_samples)}")
    print("=" * 80 + "\n")
    return result


async def scraping_player_stats_stage_helper(tournament_name, stage_name, match_types, team_df, player_pick_rates_df, session):
    tasks = [scraping_player_stats_match_type_helper(tournament_name, stage_name, match_type_name, url, team_df, player_pick_rates_df, session) for match_type_name, url in match_types.items()]
    results = await asyncio.gather(*tasks)
    return results

async def scraping_players_stats(tournament_name, stages, team_df, agent_pick_rates_df, session):
    tasks = [scraping_player_stats_stage_helper(tournament_name, stage_name, match_types, team_df, agent_pick_rates_df, session) for stage_name, match_types in stages.items()]
    results = await asyncio.gather(*tasks)
    return results

