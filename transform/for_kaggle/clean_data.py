from utilities.find_csv_files import find_csv_files
from utilities.data_clean.data_clean import *
import os

def main():
    years = [2026]

    matches_csv_files = [find_csv_files(f"{os.getcwd()}/vct_{year}/matches", "matches", year) for year in years]

    matches_result = {year: {} for year in years}
    for i, file_list in enumerate(matches_csv_files):
        year = years[i]
        for file in file_list:
            file_name = file.split("/")[2]
            df = csv_to_df(file)
            df = remove_white_spaces(df)
            df = remove_white_spaces_in_between(df)
            df = remove_tabs_and_newlines(df)
            df = remove_forfeited_matches(df)
            df = remove_nan_players_agents(df)
            df = add_missing_abbriev(df, year)
            df = update_player_names(df)
            df = update_team_names(df)
            df = update_match_names(df)
            df = fixed_team_names(df)
            df = fixed_player_names(df)
            df = fixed_match_names(df)
            df = convert_nan_players_teams(df)
            if file_name == "kills_stats.csv":
                df = get_all_agents_played_for_kills_stats(df)
            elif file_name == "rounds_kills.csv":
                print(year)
                df = extract_round_number(df)
            df = convert_to_float(df)
            df = convert_to_int(df)
            df = convert_to_str(df)    
            matches_result[year][file_name] = df
    for year, dataframes in matches_result.items():
        for file_name, dataframe in dataframes.items():
            if year == 2025 and file_name == "eco_rounds.csv":
                filtered_dataframe = dataframe[dataframe['Tournament'] == 'Valorant Masters Toronto 2025']
                eco_round_df = pd.read_csv(f"cleaned_data/vct_2025/matches/eco_rounds_copy.csv")
                dataframe = pd.concat(
                    [filtered_dataframe, eco_round_df],   # order matters: put filtered_df first
                    ignore_index=True,         # re‑number rows 0…N‑1; drop if you want to keep originals
                    sort=False                 # keeps column order; prevents sort warning when cols differ
                    )
            dataframe.to_csv(f"cleaned_data/vct_{year}/matches/{file_name}", encoding="utf-8", index=False)

    agents_stats_csv_files = [find_csv_files(f"{os.getcwd()}/vct_{year}/agents", "agents", year) for year in years]
    print(agents_stats_csv_files)
    agents_result = {year: {} for year in years}
    for i, file_list in enumerate(agents_stats_csv_files):
        year = years[i]
        for file in file_list:
            file_name = file.split("/")[2]
            df = csv_to_df(file)
            df = remove_white_spaces(df)
            df = remove_white_spaces_in_between(df)
            df = remove_tabs_and_newlines(df)
            df = update_player_names(df)
            df = update_team_names(df)
            df = update_match_names(df)
            df = fixed_team_names(df)
            df = fixed_player_names(df)
            df = convert_nan_players_teams(df)
            df = convert_to_str(df)
            agents_result[year][file_name] = df
    for year, dataframes in agents_result.items():
        for file_name, dataframe in dataframes.items():
            dataframe.to_csv(f"cleaned_data/vct_{year}/agents/{file_name}", encoding="utf-8", index=False)

    players_stats_csv_files = [find_csv_files(f"{os.getcwd()}/vct_{year}/players_stats", "players_stats", year) for year in years]
    players_result = {year: {} for year in years}
    for i, file_list in enumerate(players_stats_csv_files):
        year = years[i]
        for file in file_list:
            file_name = file.split("/")[2]
            df = csv_to_df(file)
            df = remove_white_spaces(df)
            df = remove_white_spaces_in_between(df)
            df = remove_tabs_and_newlines(df)
            df = convert_nan_players_teams(df)
            df = update_player_names(df)
            df = update_team_names(df)
            df = update_match_names(df)
            df = fixed_team_names(df)
            df = fixed_player_names(df)
            df = convert_to_float(df)
            df = convert_to_int(df)
            df = convert_to_str(df)
            players_result[year][file_name] = df
    for year, dataframes in players_result.items():
        for file_name, dataframe in dataframes.items():
            dataframe.to_csv(f"cleaned_data/vct_{year}/players_stats/{file_name}", encoding="utf-8", index=False)

    ids_csv_files = [find_csv_files(f"{os.getcwd()}/vct_{year}/ids", "ids", year) for year in years]
    ids_result = {year: {} for year in years}
    for i, file_list in enumerate(ids_csv_files):
        year = years[i]
        for file in file_list:
            file_name = file.split("/")[2]
            df = csv_to_df(file)
            df = remove_white_spaces(df)
            df = remove_white_spaces_in_between(df)
            df = remove_tabs_and_newlines(df)
            df = update_player_names(df)
            df = update_team_names(df)
            df = update_match_names(df)
            df = add_missing_player(df, year)
            df = add_missing_matches_id(df, year)
            df = fixed_match_names(df)
            df = convert_to_int(df)
            df = convert_to_str(df)
            ids_result[year][file_name] = df
    for year, dataframes in ids_result.items():
        for file_name, dataframe in dataframes.items():
            dataframe.to_csv(f"cleaned_data/vct_{year}/ids/{file_name}", encoding="utf-8", index=False)


if __name__ == '__main__':
    main()
