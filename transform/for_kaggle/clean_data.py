from pathlib import Path
from utilities.data_clean.data_clean import *


# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Input and output directories
RAW_DATA_DIR = PROJECT_ROOT
CLEANED_DATA_DIR = PROJECT_ROOT / "cleaned_data"


def clean_matches(df, file_name, year):
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

    # elif file_name == "rounds_kills.csv":
    #     df = extract_round_number(df)

    df = convert_to_float(df)
    df = convert_to_int(df)
    df = convert_to_str(df)

    return df


def clean_agents(df, year):
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

    return df


def clean_players_stats(df, year):
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

    return df


def clean_ids(df, year):
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

    return df


def process_csv_files(year, category, cleaning_function):
    """
    Reads CSV files from:
        vct_YYYY/category/

    Cleans and saves each file to:
        cleaned_data/vct_YYYY/category/
    """

    input_dir = RAW_DATA_DIR / f"vct_{year}" / category
    output_dir = CLEANED_DATA_DIR / f"vct_{year}" / category

    # Check whether the input directory exists
    if not input_dir.is_dir():
        print(f"Input directory not found: {input_dir}")
        return

    # Find all CSV files recursively
    csv_files = sorted(input_dir.rglob("*.csv"))

    if not csv_files:
        print(f"No CSV files found in {input_dir}")
        return

    # Create output directory if necessary
    output_dir.mkdir(parents=True, exist_ok=True)

    for file_path in csv_files:
        file_name = file_path.name

        print(f"Cleaning: {year} | {category} | {file_name}")

        # Read CSV into DataFrame
        df = csv_to_df(str(file_path))

        # Apply category-specific cleaning
        if category == "matches":
            df = cleaning_function(df, file_name, year)
        else:
            df = cleaning_function(df, year)

        # Preserve relative directory structure
        relative_path = file_path.relative_to(input_dir)
        output_path = output_dir / relative_path

        # Create subdirectories if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Save cleaned CSV
        df.to_csv(
            output_path,
            encoding="utf-8",
            index=False
        )

        print(f"Saved: {output_path}")

        # Release reference to the DataFrame
        del df


def main():
    years = [2026]

    cleaning_functions = {
        "matches": clean_matches,
        "agents": clean_agents,
        "players_stats": clean_players_stats,
        "ids": clean_ids
    }

    for year in years:
        print(f"\n========== Cleaning VCT {year} ==========\n")

        for category, cleaning_function in cleaning_functions.items():
            process_csv_files(
                year,
                category,
                cleaning_function
            )

        print(f"\n========== Finished VCT {year} ==========\n")


if __name__ == "__main__":
    main()