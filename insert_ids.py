from initialization.add_data import *
import pandas as pd
from Connect.connect import connect, engine
from initialization.create_tables import create_all_tables

def main():
    conn, curr = connect()
    sql_alchemy_engine = engine()
    all_agents = pd.read_csv("all_vct/all_agents.csv")
    all_players_id = pd.read_csv("all_vct/all_players_ids.csv")
    all_matches = pd.read_csv("all_vct/all_matches_games_ids.csv")
    all_teams_id = pd.read_csv("all_vct/all_teams_ids.csv")
    all_teams_mapping = pd.read_csv("all_vct/all_teams_mapping.csv")
    all_tournaments_stages_match_types = pd.read_csv("all_vct/all_tournaments_stages_match_types_ids.csv")
    create_all_tables(curr)    
    conn.commit()
    add_tournaments(all_tournaments_stages_match_types, sql_alchemy_engine)
    add_stages(all_tournaments_stages_match_types, sql_alchemy_engine)
    add_match_types(all_tournaments_stages_match_types, sql_alchemy_engine)
    add_matches(all_matches, sql_alchemy_engine)
    # add_games(all_matches, sql_alchemy_engine)
    add_teams(all_teams_id, sql_alchemy_engine)
    add_players(all_players_id, sql_alchemy_engine)
    curr.close()
    conn.close()

if __name__ == '__main__':
    main()