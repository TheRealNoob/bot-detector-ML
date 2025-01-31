import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

skills = [
    "attack","defence","strength","hitpoints","ranged","prayer","magic","cooking","woodcutting","fletching","fishing","firemaking","crafting","smithing","mining","herblore","agility","thieving","slayer","farming","runecraft","hunter","construction"
]

class data_class:
    def __init__(self, data) -> None:
        self.df = pd.DataFrame(data)

        # defaults
        self.df_clean = None
        self.df_low = None
        self.minigames = None
        self.skills = skills

    def clean(self):
        logger.debug('Cleaning data')
        self.df_clean = self.df.copy()
        
        # drop unrelevant columns
        if 'name' in self.df_clean.columns:
            self.users = self.df_clean[['Player_id','name']]
            self.df_clean.drop(columns=['id','timestamp','ts_date','name'], inplace=True)
        else:
            self.df_clean.drop(columns=['id','timestamp','ts_date'], inplace=True)

        # set unique index
        self.df_clean.set_index(['Player_id'], inplace=True)

        columns = self.df_clean.columns
        self.minigames = [c for c in columns if c not in skills and c != 'total']

        # total is not always on hiscores
        self.df_clean[self.skills] = self.df_clean[self.skills].replace(-1, 0)
        self.df_clean['total'] = self.df_clean[self.skills].sum(axis=1)
        
        self.df_clean[self.minigames] = self.df_clean[self.minigames].replace(-1, 0)
        self.df_clean['boss_total'] = self.df_clean[self.minigames].sum(axis=1)

        # get low lvl players
        mask = (self.df_clean['total'] < 1_000_000)
        self.df_low = self.df_clean[mask].copy()

        return self.df_clean
    
    def add_features(self):
        logger.debug('adding features')
        if self.df_clean == None:
            self.clean()
        
        # save total column to variable
        total = self.df_clean['total']
        boss_total =  self.df_clean['boss_total']

        # for each skill, calculate ratio
        for skill in self.skills:
            self.df_clean[f'{skill}/total'] = self.df_clean[skill] / total

        for boss in self.minigames:
            self.df_clean[f'{boss}/boss_total'] = self.df_clean[boss] / boss_total

        self.df_clean['median_feature'] = self.df_clean[self.skills].median(axis=1)
        self.df_clean['mean_feature'] = self.df_clean[self.skills].mean(axis=1)

        # replace infinities & nan
        self.df_clean = self.df_clean.replace([np.inf, -np.inf], 0) 
        self.df_clean.fillna(0, inplace=True)
        self.features = True
        return self.df_clean

    def filter_features(self, base:bool=True, feature:bool=True, ratio:bool=True):
        logger.debug(f'filtering features: {base=}, {feature=}, {ratio=}')
        
        # input validation
        if not(base or feature or ratio):
            raise 'pick at least one filter'

        # if the data is not cleaned, clena the data first
        if self.df_clean == None:
            self.add_features() if feature else self.clean()
        
        # filters
        base_columns = [c for c in self.df_clean.columns if not ('_feature' in c or '/total' in c or '/boss_total' in c)] if base else []
        feature_columns = [c for c in self.df_clean.columns if '_feature' in c] if feature else []
        ratio_columns = [c for c in self.df_clean.columns if '/total' in c or '/boss_total' in c] if ratio else []

        # combine all columns
        columns = base_columns + feature_columns + ratio_columns
        return self.df_clean[columns]

