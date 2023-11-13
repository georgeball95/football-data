import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

from pitch_plot import drawpitch

# read in info on available data

competitions_info_url = "https://raw.githubusercontent.com/statsbomb/open-data/master/data/competitions.json"

competitions_df = pd.DataFrame(requests.get(url=competitions_info_url).json())

competitions_df[competitions_df["competition_name"] == "Premier League"]

# select desired competition and season; get ids

selected_competition = "Premier League"

selected_season = "2015/2016"

competition_season_df = competitions_df[(competitions_df["competition_name"] == selected_competition)
                      & (competitions_df["season_name"] == selected_season)]

competition_id, season_id = competition_season_df.iloc[0][['competition_id','season_id']]

matches_url = f"https://raw.githubusercontent.com/statsbomb/open-data/master/data/matches/{competition_id}/{season_id}.json"

matches_df = pd.DataFrame(requests.get(url=matches_url).json())

for i in list(matches_df):
    #print(i)
    
    if type(matches_df[i].tolist()[0]) == dict:
        
        new_cols = pd.json_normalize(matches_df[i])
        
        new_col_names = list(matches_df[i].tolist()[0].keys())
        
        #p#rint(new_col_names)
        
        matches_df = pd.concat(
                [
                    matches_df,
                    pd.DataFrame(
                        new_cols, 
                        index=matches_df.index, 
                        columns=new_col_names
                    )
                ], axis=1
            )
        
        del matches_df[i]
        
    else:
        
        pass
    
# select match to look at; get meta data
#match_id = 3825848

home_team, away_team = "Leicester City", "Everton"

# selected_match = matches_df[(matches_df["home_team_name"] == home_team) &
#            (matches_df["away_team_name"] == away_team)]

selected_match = matches_df[(matches_df["home_team_name"] == "Leicester City") |
           (matches_df["away_team_name"] == "Leicester City")]

selected_match['match_date'] = pd.to_datetime(selected_match['match_date'])
selected_match = selected_match.sort_values(by=['match_date'],ascending=True)

all_season = pd.DataFrame({})

n=1

for match_id in selected_match.match_id.tolist():
    
    print(n)
    n+=1

    # get event data
    
    match_events_url = f"https://raw.githubusercontent.com/statsbomb/open-data/master/data/events/{match_id}.json"
    
    match_events_df = pd.DataFrame(requests.get(url=match_events_url.format(match_id)).json())
    
    
    dict_cols, normal_cols = [], []
    for i in list(match_events_df):
        if dict in set([type(i) for i in match_events_df[i]]):
            dict_cols.append(i)
        else:
            normal_cols.append(i)
            
    df = match_events_df
    
    normalized_dfs = [df[c] for c in normal_cols]
    
    for col in dict_cols:
        
        x = pd.json_normalize(df[col])
        
        x.columns = [f"{col}_{i}" for i in list(x)]
        
        normalized_dfs.append(x)
        
    final = pd.concat(normalized_dfs, axis=1)
    
    location_columns = [col for col in list(final) if "location" in col]
    
    for col in location_columns:
        
        try:
            
            print(col)
        
            final[[f"{col}_x", f"{col}_y"]] = final[col].apply(pd.Series).fillna(0)
            
        except:
            
            pass
        
    final['match_id'] = match_id
        
    all_season = all_season.append(final)


passes = all_season[(all_season["type_name"] == "Pass") &
                    (all_season["team_name"] == "Leicester City")]

passes['kante_drink'] = np.where(((passes['player_name'] == """N''Golo Kanté""")&(passes['pass_recipient.name'] == 'Danny Drinkwater')),1,0)
passes['drink_vardy'] = np.where(((passes['player_name'] == "Danny Drinkwater")&(passes['pass_recipient.name'] == 'Jamie Vardy')),1,0)

passes['prev_kd'] = passes['kante_drink'].shift()

passes['sum'] = passes['prev_kd']+passes['drink_vardy']

p = passes[passes["drink_vardy"] == 1]

matches, possessions = p.match_id.tolist(),p.possession.tolist()

lod = {}

assists = []

for m,p in zip(matches, possessions):
    
    poss_df = all_season[(all_season["match_id"] == m)&(all_season["possession"] == p)]
    
    lod[m] = poss_df
    
    if "Goal" in poss_df['shot_outcome.name'].tolist():
        
        assists.append(m)
    

j=matches_df[matches_df["match_id"].isin(assists)]


################
from scipy.spatial import ConvexHull

for event in all_season.type_name.unique():
    
    events = all_season[(all_season["type_name"] == event)&
                        (all_season["player_name"] =="N''Golo Kanté")]
    
    if len(events.index) > 2:
        
        fig,ax=plt.subplots(figsize=(4,6))
        
        fig.patch.set_facecolor('white')
    
        hull = ConvexHull(events[['location_y','location_x']])
        
        defpoints = events[['location_y','location_x']].values
        
        #Loop through each of the hull's simplices
        for simplex in hull.simplices:
            #Draw a black line between each
            plt.plot(defpoints[simplex, 0], defpoints[simplex, 1], 'k-')
    
        
        drawpitch(ax, hspan = [0, 120], vspan = [80,0],
                    linecolor = '#232323', facecolor = '#e8e8e8', arcs = True, \
                    lw = 1.5, x_offset = [0,0], y_offset = [0,0], style_id = 8,
                    grass_cutting = False, measure='SB',orientation="vertical") 
        
        plt.scatter(events['location_y'],
                    events['location_x'],
                    color="blue",
                    s=40,
                    ec="black",
                    lw=1,
                    alpha=0.9
                    ,zorder=1)
        
        plt.title(event)
        plt.show()
        
    else:
        
        pass








#def plot_possession_seq(df):
    
    ##


# plt.rcParams["font.family"] = "Arial"
# player = "Riyad Mahrez"

# player_events = all_season[(all_season["player_name"] == player)&
#                      (all_season["type_name"] == "Shot")&
#                      (all_season["shot_outcome.name"] == "Goal")]

# ffs = []

# fig,ax = plt.subplots(figsize=(7,10)) 

# import matplotlib.image as image
# import matplotlib.pyplot as plt
# im = image.imread('sblogo.jpg')

# ax.imshow(im, aspect='auto', extent=(0,0,5,5))


# # from matplotlib.offsetbox import OffsetImage, AnnotationBbox

# # image = plt.imread('sblogo.jpg') 
# # ax.add_artist( #ax can be added image as artist.
# #     AnnotationBbox(
# #         OffsetImage(image)
# #         , (0,0)
# #         , frameon=False
# #     ) 
# # )


# dates = []

# for i in list(range(len(player_events.index))):
# #for i in list(range(len(player_events.index))):
    
#     shot = player_events.iloc[i]
    
#     mins,sec = shot['minute'], shot['second']
    
#     ax = plt.subplot(5,3, i+1)
    
#     ax.imshow(im, aspect='auto', extent=(0,0,5,5))
#     plt.axis('off')
#     fig.patch.set_facecolor('white')
    
#     drawpitch(ax, hspan = [0, 120], vspan = [80,0],
#                 linecolor = '#232323', facecolor = '#e8e8e8', arcs = True, \
#                 lw = 1.5, x_offset = [0,0], y_offset = [0,0], style_id = 8,
#                 grass_cutting = False, measure='SB',orientation="vertical") 
    
#     plt.scatter(shot['location_y'],
#                 shot['location_x'],
#                 color="blue",
#                 s=40,
#                 ec="black",
#                 lw=1,
#                 alpha=0.9
#                 ,zorder=1)
    
#     xg = shot['shot_statsbomb_xg']
    
#     end = shot['shot_end_location']
    
#     ff = shot['shot_freeze_frame']
    
#     tech,body_part,type_name,first_time,onev1 = shot['shot_technique.name'],\
#         shot['shot_body_part.name'],shot['shot_type.name'],shot['shot_first_time'],\
#             shot['shot_one_on_one']
            
#     #plt.scatter(end[1],end[0])
    
#     plt.plot([shot['location_y'],end[1]],[shot['location_x'],end[0]],
#              color="blue", ls=":", alpha=0.8, zorder=0)
            
#     ffs.append(ff)
    
#     plt.ylim(59.75,120.5)
#     plt.xlim(-1,81)
    
#     if type(ff) == list:
    
#         for ff_player in ff:
            
#             if ff_player['teammate']:
#                 col = "blue"
#             elif ff_player['position']['name'] == "Goalkeeper":
#                 col = "green"
#             else:
#                 col = "grey"
            
#             plt.scatter([ff_player['location'][1]],
#                         [ff_player['location'][0]],
#                         color=col,s=40,alpha=0.5,zorder=2)

#     match_info = matches_df[matches_df["match_id"] == shot['match_id']].iloc[0]
    
#     h,a,hg,ag,date = match_info['home_team_name'],\
#                     match_info['away_team_name'],\
#                     match_info['home_score'],\
#                     match_info['away_score'],\
#                     match_info['match_date']
                    
#     dates.append(date)
                    
#     #plt.text(40,80,f"{h} {hg} - {ag} {a}\n{date}\n{xg:.2f} xG\n{body_part}",ha="center")
    
#     #possession
#     poss = shot['possession']
    
#     poss_df = all_season[(all_season["match_id"] == match_id)&
#                (all_season["possession"] == poss)&
#                (all_season["type_name"].isin(["Pass","Carry"]))]
    
#     if h == "Leicester City":
        
#         title = f"{a} (H) - {mins+1}'"
        
#     else:
#         title = f"{h} (A) - {mins+1}'"
        
#     plt.title(title)
    
#     plt.text(13,66,f"{xg:.2f} xG",fontsize=10,ha="center", va="center",
#          bbox=dict(boxstyle="round",
#                    ec="0.2",
#                    fc="white",
#                    )
#          )

# first, last = dates[0], dates[-1]
                        

# plt.suptitle(f"{player} goals | {first} - {last} | 2015/16 Premier League",fontsize=14)
# plt.tight_layout()
# plt.savefig(os.path.join('images',f'{player}_all.png'),dpi=300)
# plt.show()

#     # for p in list(range(len(poss_df.index))):
        
#     #     poss_row = poss_df.iloc[p]
        
#     #     if poss_row['type_name'] == "Pass":
            
#     #         plt.scatter(poss_row['location_y'],poss_row['location_x'],
#     #                     color="red")
            
#     #         plt.plot([poss_row['location_y'],poss_row['pass_end_location_y']],
#     #                  [poss_row['location_x'],poss_row['pass_end_location_x']]
#     #                  ,color="red")
            
#     #     else:

#     #         plt.scatter(poss_row['location_y'],poss_row['location_x']
#     #                     ,color="red")
            
#     #         plt.plot([poss_row['location_y'],poss_row['carry_end_location_y']],
#     #                  [poss_row['location_x'],poss_row['carry_end_location_x']]
#     #                  ,color="red")
    
    
