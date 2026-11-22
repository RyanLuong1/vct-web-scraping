from utilities.data_clean.data_clean import csv_to_df, convert_to_int
import pandas as pd
import math 

def main():
    years = [2021, 2022, 2023, 2024, 2025, 2026]
    players_dfs = {}
    players = pd.DataFrame()
    teams_dfs = {}
    teams = pd.DataFrame()
    matches_ids_dfs = {}
    tournaments_stages_match_types_ids_dfs = {}
    matches_ids = pd.DataFrame()
    tournaments_stages_match_types_ids = pd.DataFrame()
    teams_mapping = pd.DataFrame()
    teams_mapping_dfs = {}

    for year in years:
        # agents_df = pd.read_csv(f"vct_{year}/all_values/all_agents.csv")

        players_df = csv_to_df(f"cleaned_data/vct_{year}/ids/players_ids.csv")
        # print(players_df[players_df["Player ID"] == 10207])
        teams_df = csv_to_df(f"cleaned_data/vct_{year}/ids/teams_ids.csv")

        team_mapping_df = csv_to_df(f"cleaned_data/vct_{year}/matches/team_mapping.csv")

        teams_mapping_dfs[year] = team_mapping_df

        tournaments_stages_matches_games_ids_df = csv_to_df(f"cleaned_data/vct_{year}/ids/tournaments_stages_matches_games_ids.csv")
        tournaments_stages_match_types_ids_df = csv_to_df(f"cleaned_data/vct_{year}/ids/tournaments_stages_match_types_ids.csv")

        # all_agents = set(agents_df['Agents'])

        teams_df["Team ID"] = teams_df["Team ID"].apply(lambda id: int(id) if not math.isnan(id) else pd.NA)
        players_dfs[year] = players_df
        teams_dfs[year] = teams_df

        tournaments_stages_matches_games_ids_df["Stage ID"] = tournaments_stages_matches_games_ids_df['Stage ID'].astype(str)
        tournaments_stages_match_types_ids_df["Stage ID"] = tournaments_stages_match_types_ids_df['Stage ID'].astype(str)
        tournaments_stages_matches_games_ids_df.loc[:, "Match Type"] = tournaments_stages_matches_games_ids_df["Match Type"].str.strip()
        tournaments_stages_matches_games_ids_df.loc[:, "Match Type"] = tournaments_stages_matches_games_ids_df["Match Type"].str.strip()
        merged_df = pd.merge(tournaments_stages_matches_games_ids_df,
                            tournaments_stages_match_types_ids_df[["Tournament", "Stage", "Match Type", "Match Type ID"]],
                            on=["Tournament", "Stage", "Match Type"],
                            how="left")
        merged_df["Year"] = year

        matches_ids_dfs[year] = merged_df
        match_type_index = matches_ids_dfs[year].columns.get_loc("Match Type")
        match_type_ids = matches_ids_dfs[year].pop("Match Type ID")

        matches_ids_dfs[year].insert(match_type_index + 1, "Match Type ID", match_type_ids)

        tournaments_stages_match_types_ids_df["Year"] = year

        tournaments_stages_match_types_ids_dfs[year] = tournaments_stages_match_types_ids_df

        
        # agents = agents | all_agents

    for year in years:
        matches_ids_dfs[year].reset_index(drop=True, inplace=True)
        tournaments_stages_match_types_ids_dfs[year].reset_index(drop=True, inplace=True)
        players_dfs[year].reset_index(drop=True, inplace=True)
        teams_dfs[year].reset_index(drop=True, inplace=True)
        teams_mapping_dfs[year].reset_index(drop=True, inplace=True)
        # print(players_dfs[year][players_dfs[year]["Player"] == "nan"])
        matches_ids = pd.concat([matches_ids, matches_ids_dfs[year]], ignore_index=True)
        tournaments_stages_match_types_ids = pd.concat([tournaments_stages_match_types_ids,
                                                        tournaments_stages_match_types_ids_dfs[year]],
                                                        ignore_index=True)
        players = pd.concat([players, players_dfs[year]], ignore_index=True)
        teams = pd.concat([teams, teams_dfs[year]], ignore_index=True)
        teams_mapping = pd.concat([teams_mapping, teams_mapping_dfs[year]], ignore_index=True)

    # agents = pd.DataFrame({'Agents': list(agents)})
    
    players.drop_duplicates(inplace=True, subset=["Player", "Player ID"])
    teams.drop_duplicates(inplace=True, subset=["Team", "Team ID"])
    matches_ids.drop_duplicates(inplace=True)
    tournaments_stages_match_types_ids.drop_duplicates(inplace=True)
    teams_mapping.drop_duplicates(subset=["Abbreviated", "Full Name"], inplace=True)
    missing_rows = matches_ids[matches_ids["Match Type ID"].isnull()]
    missing_match_types = missing_rows[["Tournament", "Tournament ID", "Stage", "Stage ID", "Match Type", "Match Type ID", "Year"]].drop_duplicates()

    tournaments_stages_match_types_ids = pd.concat([tournaments_stages_match_types_ids, missing_match_types], ignore_index=True) \
                                        .sort_values(by=["Year", "Tournament", "Tournament ID", "Stage", "Stage ID", "Match Type"])
    
    mask = (tournaments_stages_match_types_ids["Stage ID"] == "all") & (tournaments_stages_match_types_ids["Match Type ID"] == "all")

    tournaments_stages_match_types_ids.loc[mask, ["Stage ID", "Match Type ID"]] = pd.NA

    tournaments_stages_match_types_ids["Stage ID"] = pd.to_numeric(tournaments_stages_match_types_ids["Stage ID"], errors="coerce").astype("Int32")
    tournaments_stages_match_types_ids["Match Type ID"] = pd.to_numeric(tournaments_stages_match_types_ids["Match Type ID"], errors="coerce").astype("Int32")

    # matches_ids["Stage ID"] = pd.to_numeric(matches_ids["Stage ID"], errors="coerce").astype("Int32")
    # matches_ids["Match Type ID"] = pd.to_numeric(matches_ids["Match Type ID"], errors="coerce").astype("Int32")
    # players["Player ID"] = pd.to_numeric(players["Player ID"], errors="coerce").astype("Int32")
    matches_ids = convert_to_int(matches_ids)
    players = convert_to_int(players)
    # matches_ids["Stage ID"] = convert_to_int(matches_ids["Stage ID"])
    # matches_ids["Match Type ID"] = convert_to_int(matches_ids["Match Type ID"])
    # players["Player ID"] = convert_to_int(players["Player ID"])

    nan_player = players[players["Player ID"] == 10207].index
    players.loc[nan_player, "Player"] = "nan"

    players.to_csv(f"all_ids/all_players_ids.csv", index=False)
    teams.to_csv(f"all_ids/all_teams_ids.csv", index=False)
    # agents.to_csv(f"all_ids/all_agents.csv", index=False)
    matches_ids.to_csv(f"all_ids/all_matches_games_ids.csv", index = False)
    tournaments_stages_match_types_ids.to_csv("all_ids/all_tournaments_stages_match_types_ids.csv", index = False)
    teams_mapping.to_csv("all_ids/all_teams_mapping.csv", index=False)



if __name__ == "__main__":
    main()