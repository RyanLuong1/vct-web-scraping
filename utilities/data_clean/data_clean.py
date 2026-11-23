import pandas as pd
import numpy as np

def csv_to_df(file):
    return pd.read_csv(file, keep_default_na=True)

misnamed_teams = {"BLISS": "Team Bliss", "WaVii": "Team WaVii", "Arrow": "Team Arrow", "FNLTY": "Finality", "100su": "Mujig 100su",
                    "RRQ": "Rex Regum Qeon", "NXLGA": "NXLG Academy", "57RBB": "57 Rach Bunh Binh", "Kantic": "Kantic Gaming",
                    "NAJIN": "NAJIN Rivals", "ex-R5": "ex-Recon 5", "Swa": "Sway eSports", "SR.GC": "Shopify Rebellion GC",
                    "TGH L": "The Goose House Lunar", "Mustang": "Mustang Gaming", "Baec": "Baecon GG", "Vexed": "Vexed Gaming",
                    "NRAGE": "ENRAGE", "BK ROG": "BK ROG Esports", "kom4ka": "komand04ka", "eXiLe": "eXiLe eSports", "Orbit": "Orbit",
                    "XCN": "VOIN DRIP", "CNL": "VOIN DRIP", "FAV": "FAV gaming", "New": "New Team", "AE": "AKIHABARA ENCOUNT",
                    "Rebe": "Rebellion Arts", "YA": "Ingenuity", "Team": "rööcivarkaat", "ROISS": "Roisseur", "XTM": "VOIN DRIP",
                    "Recca.P": "Recca Project", "YTX": "VOIN DRIP", "TOKYO": "Tokyo", "INRE": "SchwarzerLand", "ICC": "SchwarzerLand",
                    "INS": "SchwarzerLand", "BB": "SchwarzerLand", "no n": "SchwarzerLand", "tp2luz": "tp i 2 luza", "TMSPACE": "TEAM SPACE",
                    "VEXEC": "ValorantEXEC", "DLWZK": "DELIRAWOW", "Wolves": "Wolves of Hell", "BENCH": "Benchwarmers", "sauce": "sas elle",
                    "Sangal": "Sangal Esports", "Vend": "Recca Project", "R&MB": "rice and meatballs", "Wygers": "Wygers Argentina",
                    "Procyon": "Procyon Team", "PÊEK": "PÊEK Gaming", "Whynot": "WhynotVLR", "anime": "animeshniki", "ZMM.B": "Zero MarksMen Black",
                    "SR.GC": "Shopify Rebellion GC", "ASTRO": "Astro Esports", "BLIND": "Blind Esports", "IGZ": "SchwarzerLand", "VOX.HK": "VOX Hakaishin",
                    "FTZ.R": "ForteZ Regulus", "KRAKEN": "KRAKEN ESC", "STY": "SchwarzerLand", "UAESA.G": "UAESA Green", "ZMM.S": "Zero MarksMen Silver",
                    "Azules": "Azules Esports", "Reaper": "The Reaper", "SPACE": "Space Walkers", "SPX": "Storks Phalanx", "NTH": "SchwarzerLand",
                    "RIVAL": "Rival Esports Alpha", "TAIYO": "Taiyo eSports", "ex-WC": "ex-Wildcard Gaming", "MXBSS": "MXB South Side", "VCTRY": "VCTRY Esports",
                    "ODIUM": "Odium", "Cavalry": "Cavalry Esports", "Focus": "Team Focus", "Fre": " Frederikssund Vikings", "GLD.GC": "Guild GC", "MANGAL": "TEAM MANGAL",
                    "ŞAK": "Komşu's", "db": "DownBad", "Sampi": "Team Sampi", "tftt": "tftteam", "tftteam, tftt": "tftteam", "GB": "Gamebreakers", "InTenZive": "InTenZiveEU",
                    "Bandits": "Bandit ESC", "Dont": "Dont Wanna Try Hard", "OW": "Overwatch", "tftt, tftteam": "tftteam", "KJlA": "KJlACCHblE", "mcch": "mcchicken",
                    "sile": "silence", "Kron": "KronBars", "Holl": "Hollywood", "sile, silence": "silence", "Holl, Hollywood": "Hollywood", "Kron, KronBars": "KronBars",
                    "Tens": "Tensei Esports", "Thic": "ThiccWRECK", "Synt": "Synthetic", "Inte": "Interstate 95", "Dial": "Dialed In", "ATK": "ATK Mode", "Pira, Pirate Nation": "Pirate Nation",
                    "Wind": "Windstorm", "Swag": "Swagoi", "Pira": "Pirate Nation", "Puls": "Pulsar", "Jumb": "Jumba", "Scru": "Scrub Garden", "Arli": "Arlington E.C.",
                    "Dial, Dialed In": "Dialed In", "Pira, Pireate Nation": "Pirate Nation", "YKS": "Yankees", "FIA": "FREAKSINACTION", "Clan, Clan Infamous": "Clan Infamous",
                    "GMG, GOMA": "GOMA", "GMG": "GOMA", "EPA, Euphoria": "Euphoria", "GHS": "Gehenna Sweepers", "GHS, Gehenna Sweepers": "Gehenna Sweepers", "Gwan, GwangDae": "GwangDae",
                    "OLDG": "OLDGUYZ", "v0rt, v0rteX 5": "v0rteX 5", "v0rt": "v0rtex", "MM": "Mob Mentality eSports", "Enig": "Enigma", "Doub": "DoubleCross eSports", "RESE": "Reservoir dogs",
                    "just": "justtry", "Les": "Les Babouches", "Anth": "Anthrax", "74, Nanashi no Gonbee": "Nanashi no Gonbee", "74": "Nanashi no Gonbee", "Endavant": "Team Endavant", "Rese": "Reservoir dogs",
                    "CK": "Cock Esports", "VT": "VITEAZ", "RR": "Rage's Rangos", "M5": "Morioh Cho", "Orbi": "VOIN DRIP", "XcN": "VOIN DRIP", "Play": "GRN Esports",
                    "OVA": "Secret Esports", "MCK": "Mastery", "owna": "Ziomki Poziomki", "Devi": "ValorEitis", "1VR": "Karasuno", "SE": "VITEAZ",
                    "illm": "Galaxie Punk Esport", "BRK": "Hide In Smoke", "Mega": "OfficialFragBoys", "SUPR": "Laia Nation", "SEN": "The Noah Aiello",
                    "bc": "OmegaKek", "RC": "Goldhorn Gaming", "NRG": "Mega Minors", "eU": "HDMI Port", "Ento": "Devision Esports", "GHST": "Boosted Immortals",
                    "FREE": "Rage's Rangos", "NBL": "Chilling in Space", "ABX": "Veggie Straws", "RESO": "Slaughter House", "PK": "sadHours", "FaZe": "South East Movement",
                    "V1": "Relentless Esports", "GT": "OES Solo", "Lemo": "Reborn", "seek": "Rekreational Esports"

}

misnamed_players = {"luk": "lukzera", "Λero": "Aero", "Playboi Joe": "velis", "WeDid": "wedid", "karma": "karmax1", "yeji": "shen", "xvr": "xeric",
                    "Oblivion": "icarus", "nickszxz": "nicksz", "m0rea": "budimeisteR", "mikalulba": "Mikael", "zhar": "Asteriskk", "justreggae": "reggae",
                    "BoBo": "Ender", "1000010": "01000010", "derilasong": "Fuqua", "Arquiza": "rkz", "par scofield": "parscofield", "florance": "flqrance",
                    "stev0r": "stev0rr", "unfaiR aK": "Unfair", "alulba": "aluba", "2": "002", "kETTU": "pATE", "Laika": "Wendigo", "HaoHao": "Howie"}

old_to_new_names_players = {"richzin": "rich", "kAdavra" : "K4DAVRA"}

old_to_new_names_teams = {"Leviatán": "LEVIATÁN", "Nightblood Converse": "Nightblood Gaming", "SDobbies": "Sdobbies"}

misnamed_match_names = {"Gaming Barracks.fi vs Endavant": "Gaming Barracks.fi vs Team Endavant", "IVY vs Endavant": "IVY vs Team Endavant",
                        "Endavant vs EXEN Esports": "Team Endavant vs EXEN Esports", "Endavant vs WLGaming Esports": "Team Endavant vs WLGaming Esports",
                        "Oserv Esport vs Endavant":"Oserv Esport vs Team Endavant"}

def remove_white_spaces(df):
    for column in ["Stage", "Match Type", "Match Name",
                  "Team", "Team A", "Team B",
                  "Eliminator Team", "Eliminated Team", "Player",
                  "Player Team", "Enemy Team", "Enemy",
                  "Eliminator", "Eliminated"]:
        if column in df:
            df[column] = df[column].apply(lambda x: x.strip() if isinstance(x, str) else x)
            if "Match Name" in df and (column == "Eliminator Team" or column == "Team"):
                mask = (df["Match Name"] == "Frederikssund Vikings vs The Goose House") & \
                       (df[column] != "The Goose House")
                df.loc[mask, column] = "Frederikssund Vikings"
    return df

def convert_to_str(df):
    for column in ["Team", "Team A", "Team B",
                  "Eliminator Team", "Eliminated Team", "Player",
                  "Player Team", "Enemy Team", "Enemy",
                  "Eliminator", "Eliminated"]:
        if column in df:
            df[column] = df[column].astype("string")
    return df

def convert_to_int(df):
    columns = [
        "Player ID", "Team ID", "Tournament ID", "Stage ID",
        "Match Type ID", "Match ID", "Game ID", "Initiated",
        "Player Kills", "Enemy Kills", "Difference",
        "2k", "3k", "4k", "5k",
        "1v1", "1v2", "1v3", "1v4",
        "Econ", "Spike Plants", "Spike Defuses",
        "Team A Attacker Score", "Team A Defender Score",
        "Team A Overtime Score", "Team B Attacker Score",
        "Team B Defender Score", "Team B Overtime Score",
        "Average Combat Score", "Kills", "Deaths",
        "Assists", "Kills - Deaths (KD)",
        "Average Damage Per Round", "First Kills",
        "First Deaths", "Kills - Deaths (FKD)"
    ]

    for column in columns:
        if column in df.columns:
            df[column] = (
                pd.to_numeric(df[column], errors="coerce")
                .round()
                .astype("Int64")
            )

    return df

def convert_to_float(df):
    for column in ["Rating", "Kills:Deaths", "First Kills Per Round", "First Deaths Per Round", "Average Combat Score", "Average Damage Per Round"]:
        if column in df:
            df[column] = pd.to_numeric(df[column], errors="coerce").astype("Float64")
    return df

def remove_empty_agent_rows(df):
    return df.dropna(subset=["Agents"], inplace=True)

def remove_white_spaces_in_between(df):
    if "Match Name" in df:
        df["Match Name"] = df["Match Name"].str.split().apply(lambda x: " ".join(x))
    return df

def fixed_match_names(df):
    if "Match Name" in df:
        df["Match Name"] = df["Match Name"].map(misnamed_match_names).fillna(df["Match Name"])
    return df

def fixed_team_names(df):
    for column in ["Team", "Teams", "Team A", "Team B", "Eliminator Team", "Eliminated Team", "Player Team", "Enemy Team"]:
        if column in df:
            df[column] = df[column].map(misnamed_teams).fillna(df[column])
    return df

def fixed_player_names(df):
    for column in ["Player", "Enemy", "Eliminator", "Eliminated"]:
        if column in df:
            df[column] = df[column].map(misnamed_players).fillna(df[column])
    return df

def fixed_clutches_success(df):
    df.loc[(df['Clutches (won/played)'].notnull()) & (df['Clutches (won/played)'].str.startswith('0')), 'Clutch Success %'] = "0%"

    return df

def get_missing_team(row, col):
    teams = row['Match Name'].split(' vs ')
    team = row[col]
    missing_team = teams[1] if teams[0] == team else teams[0]
    return missing_team

def update_team_names(df):
    columns = ["Team", "Team A", "Team B", "Eliminated Team", "Eliminator Team", "Player Team", "Enemy Team"]
    for column in columns:
        if column in df:
            for old_name, new_name in old_to_new_names_teams.items():
                old_name_condition = (df[column] == old_name)
                filtered_indices = df.index[old_name_condition]
                df.loc[filtered_indices, column] = new_name
    
    if "Teams" in df:
        for old_name, new_name in old_to_new_names_teams.items():
            filtered_indices = df["Teams"].str.contains(old_name)
            df.loc[filtered_indices, "Teams"] = df.loc[filtered_indices, "Teams"].str.replace(old_name, new_name)
    return df 

def update_match_names(df):
    if "Match Name" in df:
        for old_name, new_name in old_to_new_names_teams.items():
            filtered_indices = df["Match Name"].str.contains(old_name)
            df.loc[filtered_indices, "Match Name"] = df.loc[filtered_indices, "Match Name"].str.replace(old_name, new_name)
    return df


def update_player_names(df):
    columns = ["Player", "Enemy", "Eliminator", "Eliminated"]
    for column in columns:
        if column in df:
            for old_name, new_name in old_to_new_names_players.items():
                old_name_condition = (df[column] == old_name)
                filtered_indices = df.index[old_name_condition]
                df.loc[filtered_indices, column] = new_name
    return df 

def convert_nan_players_teams(df):
    if (
        all(col in df.columns for col in [
            "Tournament", "Stage", "Match Type", "Player"
        ])
        and ("Team" in df.columns or "Teams" in df.columns)
    ):
        team_col = "Team" if "Team" in df else "Teams"
        player_nan_condition = (df['Tournament'] == 'Champions Tour Philippines Stage 1: Challengers 2') & \
                               (df['Stage'].isin(['All Stages', 'Qualifier 1'])) & \
                               (df['Match Type'].isin(['Round of 16', 'All Match Types'])) & \
                               (df['Player'].isna()) & \
                               (df[team_col].isna())
        missing_bjk_condition = (df["Tournament"] == "Champions Tour Turkey Stage 1: Challengers 3") & \
                                (df["Stage"] == "Open Qualifier") & \
                                (df["Match Type"] == "Round of 32") & \
                                (df["Player"].isin(["Noffe", "m4rco", "vlt", "daNN", "MrFaliN"])) & \
                                (df[team_col].isna())
        pATE_condition = (df['Tournament'].isin(["Champions Tour Europe Stage 3: Challengers 2",
                                                "Champions Tour Europe Stage 3: Challengers 1", "Champions Tour Europe Stage 1: Challengers 1"])) & \
                         (df['Stage'].isin(['Open Qualifier', "Qualifier", 'All Stages'])) & \
                         (df['Match Type'].isin(['Round of 256', "Round of 128", 'All Match Types'])) & \
                         (df['Player'] == 'pATE') & \
                         (df[team_col].isna())
        wendigo_2021_condition = (df['Tournament'] == "Champions Tour North America Stage 2: Challengers 2") & \
                         (df['Stage'].isin(['Open Qualifier', 'All Stages'])) & \
                         (df['Match Type'].isin(["Round of 128", 'All Match Types'])) & \
                         (df['Player'] == 'Wendigo') & \
                         (df[team_col].isna())
        
        wendigo_2022_condition = (df['Tournament'] == "Champions Tour North America Stage 2: Challengers") & \
                         (df['Stage'].isin(["Open Qualifier #1", "Open Qualifier #2", 'All Stages'])) & \
                         (df['Match Type'].isin(["Round of 128", "Round of 64", 'All Match Types'])) & \
                         (df['Player'] == 'Wendigo') & \
                         (df[team_col].isna())

        howie_1_condition = (df['Tournament'] == "Oceania Tour: Stage 1") & \
                         (df['Stage'].isin(['Open Qualifier', 'All Stages'])) & \
                         (df['Match Type'].isin(["Round of 16", "Quarterfinals", "Lower Bracket Semifinals", "Lower Bracket Consolation Finals",
                                                 'All Match Types'])) & \
                         (df['Player'] == 'Howie') & \
                         (df[team_col].isna())

        howie_2_condition = (df['Tournament'] == "Oceania Tour: Stage 2") & \
                         (df['Stage'].isin(['Open Qualifier', 'All Stages'])) & \
                         (df['Match Type'].isin(["Round of 16", 'All Match Types'])) & \
                         (df['Player'] == 'Howie') & \
                         (df[team_col].isna())
        if "Match Name" in df:
            roocivarkaat_players_condition = (df["Tournament"] == "Champions Tour Europe Stage 3: Challengers 1") & \
                                             (df["Stage"] == "Open Qualifier") & \
                                             (df["Match Type"] == "Round of 256") & \
                                             (df["Match Name"] == "rööcivarkaat vs Team Name") & \
                                             (df["Player"].isna())
            filtered_rows = df[roocivarkaat_players_condition]
            for index, row in filtered_rows.iterrows():
                agent = row["Agents"]
                player = ""
                if agent == "skye" or agent == "breach":
                    player = "johkubb"
                elif agent == "brimstone" or agent == "omen":
                    player = "Nappi"
                elif agent == "killjoy" or agent == "cypher":
                    player = "akumeni"
                elif agent == "raze" or agent == "jett":
                    player = "Puoli"
                elif agent == "sova":
                    player = "maik"
                df.at[index, "Player"] = player
            filtered_indices = df.index[roocivarkaat_players_condition]
            df.loc[filtered_indices, "Team"] = "rööcivarkaat"


            japanese_team_player_condition = (df["Tournament"] == "Champions Tour Japan Stage 1: Challengers Week 1") & \
                                             (df["Stage"] == "Open Qualifier") & \
                                             (df["Match Type"] == "Group B") & \
                                             (df["Match Name"] == "ややーず vs Storks Phalanx") & \
                                             (df["Player"].isna())
            
            wrong_team_condition = japanese_team_player_condition & ((df["Team"] == "Storks Phalanx") | df["Team"].isna())

            filtered_indices = df.index[wrong_team_condition]
            df.loc[filtered_indices, "Team"] = "ややーず"

            missing_players_condition = japanese_team_player_condition & (df["Player"].isna())


            filtered_rows = df[missing_players_condition]

            for index, row in filtered_rows.iterrows():
                agent = row["Agents"]
                player = ""
                if agent == "kayo" or agent == "cypher":
                    player = "hatty"
                elif agent == "sova" or agent == "astra":
                    player = "YAYA"
                elif agent == "viper" or agent == "sage":
                    player = "Shinryaku"
                elif agent == "chamber" or agent == "raze":
                    player = "RIA"
                elif agent == "jett":
                    player = "Defectio"
                df.at[index, "Player"] = player


            player_nan_overview_condition = (df['Tournament'] == 'Champions Tour Philippines Stage 1: Challengers 2') & \
                               (df['Stage'] == 'Qualifier 1') & \
                               (df['Match Type'] == 'Round of 16') & \
                               (df['Player'].isna()) & \
                               (df["Match Name"] == "KADILIMAN vs MGS Spades")
            filtered_indices = df.index[player_nan_overview_condition]
            df.loc[filtered_indices, "Player"] = "nan"


        filtered_indices = df.index[player_nan_condition]
        df.loc[filtered_indices, team_col] = "MGS Spades"
        df.loc[filtered_indices, "Player"] = "nan"

        filtered_indices = df.index[missing_bjk_condition]
        df.loc[filtered_indices, team_col] = "Beşiktaş Esports"

        filtered_indices = df.index[pATE_condition]
        df.loc[filtered_indices, team_col] = "EXEN Esports"

        filtered_indices = df.index[wendigo_2021_condition]
        df.loc[filtered_indices, team_col] = "Chilling in Space"

        filtered_indices = df.index[wendigo_2022_condition]
        df.loc[filtered_indices, team_col] = "Team MystiC"

        filtered_indices = df.index[howie_1_condition]
        df.loc[filtered_indices, team_col] = "HEHE"

        filtered_indices = df.index[howie_2_condition]
        df.loc[filtered_indices, team_col] = "Trident Esports"

    if "Total Wins By Map" in df:
        tbd_condition = (df["Tournament"] == "Champions Tour Europe Stage 1: Challengers 2") & \
                        (df["Stage"].isin(["Open Qualifier", "All Stages"])) & \
                        (df["Match Type"].isin(["Round of 256", "All Match Types"])) & \
                        (df["Map"] == "Ascent") & \
                        (df["Team"].isna())
        filtered_indices = df.index[tbd_condition]
        df.loc[filtered_indices, "Team"] = "TBD"

    if "Eliminated Team" in df.columns and "Eliminator Team" in df.columns:
        null_rows = df[df["Eliminated Team"].isna()]
        eliminated_teams = null_rows.apply(lambda row: get_missing_team(row, "Eliminator Team"), axis=1)
        df.loc[null_rows.index, "Eliminated Team"] = eliminated_teams

        null_rows = df[df["Eliminator Team"].isna()]
        eliminator_teams = null_rows.apply(lambda row: get_missing_team(row, "Eliminated Team"), axis=1)
        df.loc[null_rows.index, "Eliminator Team"] = eliminator_teams

    return df

def unique_sorted_agents(agents):
    return ", ".join(list(sorted(set(agents))))

def get_all_agents_played_for_kills_stats(df):
    group_cols = [
        "Tournament",
        "Stage",
        "Match Type",
        "Match Name",
        "Team",
        "Player"
    ]

    # Use individual maps to collect agents played
    map_stats = df[df["Map"] != "All Maps"]

    # Collect all unique agents played by each player
    agents_played = (
        map_stats.groupby(group_cols)["Agents"]
        .agg(
            lambda agents: ", ".join(
                sorted({
                    agent.strip()
                    for value in agents.dropna()
                    for agent in str(value).split(",")
                    if agent.strip()
                })
            )
        )
        .reset_index(name="All Agents")
    )

    # Merge agents back into original DataFrame
    df = df.merge(
        agents_played,
        on=group_cols,
        how="left"
    )

    # Update only the All Maps rows
    mask = df["Map"] == "All Maps"

    df.loc[mask, "Agents"] = (
        df.loc[mask, "All Agents"]
        .fillna(df.loc[mask, "Agents"])
    )

    # Remove temporary column
    df = df.drop(columns=["All Agents"])

    return df


    

def remove_tabs_and_newlines(df):
    if "Map" in df:
        df["Map"] = df["Map"].str.replace("\t", "").replace("\n", "")
        df["Map"] = df["Map"].str.split("\n").str[0]
    return df

def add_missing_player(df, year):
    if "Player" in df and "Player ID" in df:
        if year == 2021:
            nan_player = df[df["Player ID"] == 10207].index
            df.loc[nan_player, "Player"] = "nan"
            df.loc[len(df.index)] = ["pATE", 9505]
            df.loc[len(df.index)] = ["Wendigo", 26880]
        elif year == 2022:
            df.loc[len(df.index)] = ["Wendigo", 26880]
        df.drop_duplicates(inplace=True, subset=["Player", "Player ID"])
        df.reset_index(drop=True, inplace=True)
    return df


def add_missing_matches_id(df, year):
    if "Match Name" in df and year == 2021:
        mask = (df['Tournament'] == 'Champions Tour Brazil Stage 1: Challengers 1') & \
              (df['Stage'] == 'Open Qualifier') & \
              (df['Match Type'] == 'Round of 32')
        first_occurence_index = df[mask].index[0]
        new_row = {'Tournament': ['Champions Tour Brazil Stage 1: Challengers 1'],
                   "Tournament ID": [292],
                   'Stage': ['Open Qualifier'],
                   "Stage ID": ["594"],
                   'Match Type': ['Round of 32'],
                   'Match Name': ['ChesterNo vs FURIA'],
                   'Match ID': [9082],
                   "Map": [pd.NA],
                   "Game ID": [15207]}
        df = pd.concat([df.iloc[:first_occurence_index], pd.DataFrame(new_row), df.iloc[first_occurence_index:]]).reset_index(drop=True)
        mask = (df['Tournament'] == 'Champions Tour North America Stage 1: Challengers 1') & \
        (df['Stage'] == 'Qualifier') & \
        (df['Match Type'] == 'Round of 128')
        first_occurence_index = df[mask].index[0]
        new_row = {'Tournament': ['Champions Tour North America Stage 1: Challengers 1'],
                   "Tournament ID": [291],
                   'Stage': ['Qualifier'],
                   "Stage ID": [593],
                   'Match Type': ['Round of 128'],
                   'Match Name': ['XSET vs Primeval'],
                   'Match ID': [9145],
                   "Map": [pd.NA],
                   "Game ID": [pd.NA]}
        df = pd.concat([df.iloc[:first_occurence_index], pd.DataFrame(new_row), df.iloc[first_occurence_index:]]).reset_index(drop=True)
    return df

def remove_forfeited_matches(df):
    if "Match Name" in df:
        df = df[df["Match Name"] != "Ksenox vs Savage"]
    return df

def remove_nan_players_agents(df):
    overview_col = ["Agents", "Average Combat Score", "Kills", "Deaths",	"Assists", "Kills - Deaths (KD)",
                    "Kill, Assist, Trade, Survive %", "Average Damage Per Round", "Headshot %", "First Kills",
                    "First Deaths",	"Kills - Deaths (FKD)"]
    if "Player" in df and "Agents" in df:
        df = df.dropna(subset=["Player", "Agents"], how="all")
    if all(col in df.columns for col in overview_col):
        df = df.dropna(subset=["Agents", "Average Combat Score", "Kills", "Deaths",	"Assists", "Kills - Deaths (KD)",
                               "Kill, Assist, Trade, Survive %", "Average Damage Per Round", "Headshot %", "First Kills",
                                "First Deaths",	"Kills - Deaths (FKD)"], how="all")
    return df

def add_missing_abbriev(df, year):
    if "Abbreviated" in df:
        if year == 2022:
            df.loc[df["Full Name"] == "ややーず", "Abbreviated"] = "ややーず" 
    df.reset_index(drop=True, inplace=True)
    return df

def extract_round_number(df):
    df["Round Number"] = df["Round Number"].str.split(" ").str[1]
    return df
