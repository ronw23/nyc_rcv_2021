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
    'Eric L. Adams':        (200, 450, 1743, 3983, 21204, 37430, 49669),
    'Maya D. Wiley':        (66, 323, 4461, 3081, 29912, 15473, ),
    'Kathryn A. Garcia':    (108, 96, 2056, 5120, 31576, 43072, 129446),
    'Andrew Yang':          (171, 201, 2502, 3572, 14011,),
    'Scott M. Stringer':    (72, 101, 1644, 3114, ),
    'Dianne Morales':       (39, 111, 3508, 771, ),
    'Raymond J. McGuire':   (30, 146, 937, 1565,),
    'Shaun Donovan':        (22, 125, 724,),
    'Aaron S. Foldenauer':  (16, 61,),
    'Art Chang':            (16, 29,),
    'Paperboy Love Prince': (43, 53,),
    'Joycelyn Taylor':      (21, 97,),
    'Isaac Wright Jr.':     (12,)
}

initial_votes = {
    'Eric L. Adams':288654,
    'Maya D. Wiley':199778,
    'Kathryn A. Garcia':183433,
    'Andrew Yang':114639,
    'Scott M. Stringer':51534,
    'Dianne Morales':26374,
    'Raymond J. McGuire':25074,
    'Shaun Donovan':23074,
    'Aaron S. Foldenauer':7729,
    'Art Chang':7023,
    'Paperboy Love Prince':	3934,
    'Joycelyn Taylor':	2652,
    'Isaac Wright Jr.':	2234,
    'WRITE-IN':1567
}

round_inactive_votes=(751, 453, 4099, 2739, 18317, 39121, 73979)

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
nyc_bb = geopandas.read_file('nybb_21b/nybb.shp')
eliminated = None

# Scale foctor to closer align our final results with unofficial numbers
for k, v in initial_votes.items():
    all_eds[k] *= sum(initial_votes.values())/all_eds[k].sum()*v

number_rounds = max([len(v) for v in round_votes_gained.values()])
for round_number in range(-1, number_rounds):
    if round_number != -1:
        round_total = sum([v[round_number] for v in round_votes_gained.values() if len(v) > round_number])
        effective_vote = round_total/(round_inactive_votes[round_number]+round_total)
        d = {k: v[round_number]/round_total for k, v in round_votes_gained.items() if len(v) > round_number}
        eliminated = set(all_eds.columns)-(set(list(d.keys())+list(previous_eliminiated.keys())))
        eliminated_votes = all_eds[list(eliminated)].apply(lambda x: x*effective_vote).sum(axis=1)
        for k in d.keys():
            all_eds[k] = all_eds[k]+eliminated_votes*d[k]

        all_eds[list(eliminated)] = 0
        previous_eliminiated.update({k: True for k in eliminated})

    winners = all_eds.idxmax(axis=1).apply(lambda x: 'Other' if x not in top_4 else x)
    margins = all_eds.max(axis=1)/all_eds.sum(axis=1)
    round_map = nyc_ed.join([winners.to_frame(name='winning_party'), margins.to_frame(name='margin')]).dropna()

    plt.clf()
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.axis("off")
    title = f'Round {round_number+2}'
    if eliminated:
        title += f'\n{", ".join(eliminated)} eliminated'
    fig.suptitle(title)
    total_round_votes = all_eds.sum().sum()
    for n, party in enumerate(top_4 + ('Other',)):
        if party == 'Other':
            party_votes = all_eds[list(set(round_votes_gained)-set(previous_eliminiated)-set(top_4))].sum().sum()
        else: 
            party_votes = all_eds[party].sum().sum()
        if party_votes==0:
            continue
        cax = fig.add_axes((0.05+n*0.0750, 0.65, 0.025, 0.25))
        party_label = party.split(' ')[-1] if party in top_4 else 'Other'
        party_plurality = party_votes/total_round_votes*100
        cax.set_xlabel(f'{party_label}\n({party_plurality:.2f}%)')
        round_map[round_map.winning_party == party].plot(column='margin', cmap=color_map[party_label],
                                            legend=True, ax=ax, cax=cax, vmin=0.19, vmax=1.0, legend_kwds={'orientation': 'vertical'})

    ax.text(0.05, 0.55, "Election day ED-level results\nscaled by released round-by-round\nelimination",transform=ax.transAxes)
    nyc_bb.plot(ax=ax, legend=False, facecolor="none", edgecolor="0.0", linewidth=0.5)
    fig.subplots_adjust(0.0, 0.0, 1, 1)
    plt.savefig(f'nyc_rcv_{round_number+2}.png')