import pandas as pd
import numpy as np
import datetime

def which_year(x, yr):
    return yr if (len(x) == 3) & (x[0] in ['1', '2']) else str(int(yr)-1)

assert which_year('913', '21') == '20'
assert which_year('1213', '21') == '20'
assert which_year('113', '21') == '21'
assert which_year('213', '21') == '21'

def favorite(v_ml, h_ml):
    """Return 1 is home team is favorite based on money line."""
    if v_ml == h_ml:
        return np.nan
    return 1 if v_ml > h_ml else -1

assert np.isnan(favorite(-110, -110))

def visitor_first(x, y):
    if x['VH'] == 'V':
        return x, y
    return y, x

def odds_parser(filename):
    df = pd.read_csv(filename)
    df = df.replace(to_replace='NL', value=np.nan)
    df = df.replace(to_replace='pk', value=0)
    df[['Open', 'Close', '2H']] = df[['Open', 'Close', '2H']].astype('float')
    newr = []
    end_yr = filename[filename.find('.csv')-2:filename.find('.csv')]
    recs = list(df.to_dict(orient='records'))
    for l, r in zip(recs[::2], recs[1::2]):
        md = str(r['Date'])
        yr = which_year(md, end_yr)
        d = {}; d['Date'] = datetime.datetime.strptime(md+yr, '%m%d%y')
        v, h = visitor_first(l, r)
        d['Visitor'] = v['Team']; d['Visitor_1st'] = v['1st']; d['Visitor_2nd'] = v['2nd']; d['Visitor_3rd'] = v['3rd']; d['Visitor_4th'] = v['4th']; d['Visitor_Final'] = v['Final']
        d['Home'] = h['Team']; d['Home_1st'] = h['1st']; d['Home_2nd'] = h['2nd']; d['Home_3rd'] = h['3rd']; d['Home_4th'] = h['4th']; d['Home_Final'] = h['Final']
        # first assign the values arbitrary then flip the order as needed
        d['OU_Open'] = v['Open']; d['OU_Close'] = v['Close']; d['OU_2H'] = v['2H']
        d['Pts_Open'] = h['Open']; d['Pts_Close'] = h['Close']; d['Pts_2H'] = h['2H']
        for suf in ['Open', 'Close', '2H']:
            if 'OU_'+suf in d.keys():
                if d['OU_'+suf] < d['Pts_'+suf]:
                        d['OU_'+suf], d['Pts_'+suf] = d['Pts_'+suf], d['OU_'+suf]
        d['Home_Fav'] = favorite(v['ML'], h['ML'])
        if not np.isnan(d['Home_Fav']):
            d['Fav_Team'], d['Dog_Team'] = (h['Team'], v['Team']) if d['Home_Fav'] == 1 else (v['Team'], h['Team'])
            d['ML_Fav'], d['ML_Dog'] = (h['ML'], v['ML']) if d['Home_Fav'] == 1 else (v['ML'], h['ML'])
        newr.append(d)
    return pd.DataFrame(newr)

def calc_prob(x):
    if np.isnan(x):
        return np.nan
    if x < 0:
        return -x/(-x+100)
    return 100/(x+100)

def odds_parser_prob(odds):
    """Compute probability statistics based on parsed odds data. Required columns: ['ML_Fav', 'ML_Dog'].
    
    Note on Hold calculation: Technically, the hold needs to calculated in such a way that the experted 
    profit matches on both sides of the bet but this gives us a rough sense of the zero risk profits 
    made by the book. """
    odds['Prob_Fav'] = odds['ML_Fav'].apply(lambda x: calc_prob(x))
    odds['Prob_Dog'] = odds['ML_Dog'].apply(lambda x: calc_prob(x))
    odds['Hold'] = odds['Prob_Fav'] + odds['Prob_Dog'] - 1
    odds['IP_Fav'] = odds['Prob_Fav'] / (odds['Prob_Fav'] + odds['Prob_Dog'])
    odds['IP_Dog'] = odds['Prob_Dog'] / (odds['Prob_Fav'] + odds['Prob_Dog'])
    odds['Home_Winner'] = ((odds['Home_Final'] - odds['Visitor_Final']) > 0)*2-1
    odds['Fav_Winner'] = ((odds['Home_Fav'] * odds['Home_Winner'])+1)/2
    return odds