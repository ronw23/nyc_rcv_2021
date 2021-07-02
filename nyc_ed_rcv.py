import pandas as pd
import numpy as np
import geopandas
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable

top_4 = ('Eric L. Adams', 'Maya D. Wiley', 'Kathryn A. Garcia', 'Andrew Yang')

color_map = {
    'Adams': 'Blues',
    'Garcia': 'Greens',
    'Wiley': 'Oranges',
    'Yang': 'Purples',
    'Other': 'Greys'
}

round_votes_gained={
    'Eric L. Adams':(174,413,490,1077,3096,17437,31052,44327),
    'Maya D. Wiley':(58,297,1952,2104,2529,25327,12718),
    'Kathryn A. Garcia':(97,87,541,1280,4169,25711,36816,116844),
    'Andrew Yang':(147,179,434,1720,2622,10132),
    'Scott M. Stringer':(58,89,288,1155,2259),
    'Dianne Morales':(35,98,707,2460,632),
    'Raymond J. McGuire':(27,136,157,667,1184),
    'Shaun Donovan':(18,104,160,452),
    'Aaron S. Foldenauer':(15,54,107),
    'Art Chang':(10,26,412),
    'Paperboy Love Prince':(35,45),
    'Joycelyn Taylor':(18,77),
    'Isaac Wright Jr.':(11,)
}

round_inactive_votes=(671, 405, 773, 2903, 2053, 14465, 30653, 65404)

def ed_to_gis_id(ad):
    return lambda x: int(ad)*1000 + int(x.split(' ')[1])

previous_eliminiated = {}
all_eds = pd.DataFrame()

for ad_n in range(23, 88):
    ad = pd.read_html(f'dl_data/CD24306AD{ad_n}0.html', attrs={'class':"underline"}, header=0, skiprows=(1,-1))
    ad = ad[0]
    ad.drop(index=ad.tail(1).index, inplace=True)
    ad.rename(ad.iloc[:, 0], inplace=True)
    ad.rename(index=ed_to_gis_id(ad_n), inplace=True)
    ad.dropna(axis=1, inplace=True)
    ad.drop(columns=ad.columns[[0, 1]], inplace=True)
    all_eds = pd.concat([all_eds, ad])

nyc_ed = geopandas.read_file('nyed_21b/nyed.shp')
nyc_ed.rename(nyc_ed.iloc[:, 0], inplace=True)

number_rounds = max([len(v) for v in round_votes_gained.values()])
for round_number in range(number_rounds):

    round_total = sum([v[round_number] for v in round_votes_gained.values() if len(v) > round_number])
    effective_vote = round_total/(round_inactive_votes[round_number]+round_total)
    d = {k: v[round_number]/round_total for k, v in round_votes_gained.items() if len(v) > round_number}
    eliminated = set(all_eds.columns)-(set(list(d.keys())+list(previous_eliminiated.keys())))
    eliminated_votes = all_eds[list(eliminated)].apply(lambda x: x*effective_vote).sum(axis=1)
    for k in d.keys():
        all_eds[k] = all_eds[k]+eliminated_votes*d[k]

    all_eds[list(eliminated)] = 0
    previous_eliminiated.update({k: True for k in eliminated})

    winners = all_eds.idxmax(axis=1).apply(lambda x: x.split(' ')[-1] if x in top_4 else 'Other')
    margins = all_eds.max(axis=1)/all_eds.sum(axis=1)
    round_map = nyc_ed.join([winners.to_frame(name='winning_party'), margins.to_frame(name='margin')]).dropna()

    plt.clf()
    fig, ax = plt.subplots(figsize=(15, 10))
    ax.axis("off")
    inset_axis = ax.inset_axes([0.1, 0.6, 0.35, 0.40])
    inset_axis.axis('off')
    divider = make_axes_locatable(inset_axis)
    fig.suptitle(f'Round {round_number+1}\n{", ".join(eliminated)} eliminated')

    for party, color in reversed(list(color_map.items())):
        if len(round_map[round_map.winning_party == party])==0:
            continue
        cax = divider.append_axes('left', size='5%', pad=0.6)
        cax.set_xlabel(party)
        round_map[round_map.winning_party == party].plot(column='margin', cmap=color,
                                            legend=True, ax=ax, cax=cax, vmin=0.19, vmax=1.0, legend_kwds={'orientation': 'vertical'})

    plt.savefig(f'nyc_rcv_{round_number+1}.png')