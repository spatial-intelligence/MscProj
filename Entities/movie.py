#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 11 14:12:31 2020

@author: andy
"""

import json
import jsonpickle
from json import JSONEncoder
from decimal import Decimal
import matplotlib.pyplot as plt
import pandas as pd
import sys
import re
sys.path.insert(1, '/home/andy/Documents/MscProject/MscProj/Utils')

import tweet_helper
import database_helper
from person import Actor, Director, Writer
from trailers import Trailer
from weekend_box_office import WeekendBoxOffice
from mojo_box_office import MojoWeekendBoxOffice
import geopandas as gpd
from geopandas.tools import sjoin
import matplotlib.dates as mdates
import scipy.signal
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import seaborn as sns
import numpy as np
from colour import Color
from datetime import datetime
from datetime import timedelta
import scipy.ndimage as ndi
import scipy.stats as stats

class Movie:
    def __init__(self, db_row):
        self.movieId = db_row.movieId
        self.imdbId = db_row.imdbId
        self.title = db_row.title
        self.distributor = db_row.distributor
        self.country = db_row.country
        self.url = db_row.url
        self.year = db_row.year
        self.genres = db_row.genres.split(',') if db_row.genres != None else []
        self.rating = db_row.rating
        self.votes = db_row.votes
        self.certificates = db_row.certificates.split(',') if db_row.certificates != None else []
        self.keywords = db_row.keywords.split(',') if db_row.keywords != None else []
        self.hashtags = db_row.hashtags.split(',') if db_row.hashtags != None else []
        self.twitterHandle = db_row.twitterHandle
        self.totalRevenue = db_row.totalRevenue
        self.ukReleaseDate = db_row.ukReleaseDate
        self.budget_usd = db_row.budget_usd
        self.uk_gross_usd = db_row.uk_gross_usd
        self.domestic_gross_usd = db_row.domestic_gross_usd
        self.worldwide_gross_usd = db_row.worldwide_gross_usd
        self.international_gross_usd = db_row.international_gross_usd
        self.gross_profit_usd = db_row.gross_profit_usd
        self.profit_class = db_row.profit_class
        self.end_weekend = db_row.end_weekend
        self.total_weekends = db_row.total_weekends
        self.total_release_weeks = db_row.total_release_weeks
        self.first_run_end = db_row.first_run_end
        self.first_run_weeks = db_row.first_run_weeks
        self.critical_start = db_row.critical_start
        self.critical_end = db_row.critical_end
        self.get_cast()
        self.get_directors()
        self.get_writers()
        self.get_trailers()
        self.get_synopsis()
        self.get_box_office()
        self.get_mojo_box_office()
        
        
    def get_cast(self):
        actors_df = database_helper.select_query("actors", {"m_imdbId" : self.imdbId})
        self.actors = []
        self.actors_df = actors_df
        for index, row in actors_df.iterrows(): 
            actor = Actor(row)
            self.actors.append(actor)
    
    def get_directors(self):
        directors_df = database_helper.select_query("directors", {"m_imdbId" : self.imdbId})
        self.directors = []
        self.directors_df = directors_df
        for index, row in directors_df.iterrows(): 
            director = Director(row)
            self.directors.append(director)
    
    def get_writers(self):
        writers_df = database_helper.select_query("writers", {"m_imdbId" : self.imdbId})
        self.writers = []
        self.writers_df = writers_df
        for index, row in writers_df.iterrows(): 
            writer = Writer(row)
            self.writers.append(writer)
    
    def get_trailers(self):
        trailers_df = database_helper.select_query("trailers", { "movieId" : int(self.movieId) })
        self.trailers = []
        self.trailers_df = trailers_df
        for index, row in trailers_df.iterrows(): 
            trailer = Trailer(row)
            self.trailers.append(trailer)    
        return
        
    def get_synopsis(self):
        synopsis_df = database_helper.select_query("synopsis", {"movieId" : int(self.movieId) })
        self.synopsis_df = synopsis_df
        self.synopsis = ''
        if (not synopsis_df.empty):
            self.synopsis = synopsis_df.iloc[0].summary
        #get synopsis
        return
        
    def get_tweets(self):
        #get tweets
        return
        
    def get_box_office(self):
        box_office_df = database_helper.select_query("weekend_box_office", {"movieId" : int(self.movieId) })
        self.box_office = []
        self.box_office_df = box_office_df
        for index, row in box_office_df.iterrows(): 
            box_office = WeekendBoxOffice(row)
            self.box_office.append(box_office)   
        return
    
    def get_mojo_box_office(self):
        box_office_df = database_helper.select_query("weekend_box_office_mojo", {"movieid" : int(self.movieId) })
        box_office_df = box_office_df.sort_values(by="start_date")
        self.mojo_box_office = []
        self.mojo_box_office_df = box_office_df
        for index, row in box_office_df.iterrows(): 
            box_office = MojoWeekendBoxOffice(row)
            self.mojo_box_office.append(box_office)   
        return        
    
    def toJSON(self):
        return jsonpickle.encode(self, unpicklable=False)
        #return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)
    
    def plot_weekend_revenues(self):
        self.box_office_df['weekendGross_thou'] = self.box_office_df['weekendGross'].replace('[\£,]', '', regex=True).astype(float) / 1000
        self.box_office_df['weekendStart'] = pd.to_datetime(self.box_office_df['weekendStart']) 
        self.box_office_df.set_index('weekendStart')['weekendGross_thou'].plot()
        plt.xticks(self.box_office_df['weekendStart'])
        plt.xlabel("Weekend Starting")
        plt.ylabel("Weekend Gross (£0000)")
        plt.title(self.title + " Weekend Takings")
        plt.show()
        plt.clf()
        plt.cla()
        plt.close()
        return
    
    def plot_weekend_vs_total(self):
        self.box_office_df['weekendGross_thou'] = self.box_office_df['weekendGross'].replace('[\£,]', '', regex=True).astype(float) / 1000
        self.box_office_df['grossToDate_thou'] = self.box_office_df['grossToDate'].replace('[\£,]', '', regex=True).astype(float) / 1000    
        self.box_office_df['weekendStart'] = pd.to_datetime(self.box_office_df['weekendStart']) 
        self.box_office_df.set_index('weekendStart')['weekendGross_thou'].plot()
        self.box_office_df.set_index('weekendStart')['grossToDate_thou'].plot()
        plt.xticks(self.box_office_df['weekendStart'])
        plt.xlabel("Weekend Starting")
        plt.ylabel("Weekend Gross (£0000)")
        plt.title(self.title + " Weekend Takings")
        plt.show()
        plt.clf()
        plt.cla()
        plt.close()
        
        
    def plot_weekend_revenue_mojo(self):
        self.mojo_box_office_df['weekend_gross_thou'] = self.mojo_box_office_df['weekend_gross_usd'].replace('[\£,]', '', regex=True).astype(float) / 1000
        ax = sns.lineplot(x="start_date", y="weekend_gross_thou", data=self.mojo_box_office_df)
        ax.set(xlabel='Weekend Start Date', ylabel='Gross Takings ($thou)')
        plt.title("{0} Weekend Takings".format(self.title))
        plt.xticks(rotation=40)
        plt.show()
      
        
    def get_percentage_of_takings_in_first_two_weeks(self):
        
        if (self.mojo_box_office_df.shape[0] > 1):
            self.mojo_box_office_df["gross_to_date_f"] = self.mojo_box_office_df['gross_to_date_usd'].replace('[\£,]', '', regex=True).astype(float)
            
            week_two = self.mojo_box_office_df.iloc[1]["gross_to_date_f"]
            total_gross = float(re.sub('[^\d.]', '', self.uk_gross_usd))
            
            percentage = (week_two/total_gross) * 100
            
            return percentage
        else: 
            return 100
        
    def plot_weekend_revenue_mojo_vs_tweets(self, full_week = False, week_inc_weekend = False):
        self.mojo_box_office_df['weekend_gross_thou'] = self.mojo_box_office_df['weekend_gross_usd'].replace('[\£,]', '', regex=True).astype(float) / 1000
        self.mojo_box_office_df["weekend_tweet_count"] = self.mojo_box_office_df.apply(lambda row: self.get_geotweet_count_by_dates(row["start_date"], row["end_date"]), axis = 1)
        
        ax = self.mojo_box_office_df.plot(x="start_date", y="weekend_gross_thou", legend=False, label="Gross Takings")
        ax.set(xlabel='Date', ylabel='Gross Takings ($thou)')
        ax2 = ax.twinx()
        ax2.set(ylabel = "Tweet Count")
        self.mojo_box_office_df.plot(x="start_date", y="weekend_tweet_count", ax=ax2, legend=False, color="r", label="Weekend Tweet Count")
      
        if full_week:
            self.mojo_box_office_df["week_tweet_count"] = self.mojo_box_office_df.apply(lambda row: self.get_geotweet_count_by_dates(row["start_date"] - timedelta(days=4), row["start_date"]), axis = 1)       
            self.mojo_box_office_df.plot(x="start_date", y="week_tweet_count", ax=ax2, legend=False, color="g", label="Weekly Tweet Count")
      
        if week_inc_weekend:
            self.mojo_box_office_df["week_tweet_count_weekend"] = self.mojo_box_office_df.apply(lambda row: self.get_geotweet_count_by_dates(row["start_date"] - timedelta(days=4), row["end_date"]), axis = 1)
            self.mojo_box_office_df.plot(x="start_date", y="week_tweet_count_weekend", ax=ax2, legend=False, color="y", label="Week (inc Weekend) Tweet Count")            
      
        lines_1, labels_1 = ax.get_legend_handles_labels()
        lines_2, labels_2 = ax2.get_legend_handles_labels()
        
        lines = lines_1 + lines_2
        labels = labels_1 + labels_2
      
        ax.legend(lines, labels, loc=0)  

        plt.title("{0} Weekend Takings".format(self.title))
        plt.setp(ax.get_xticklabels(), rotation=45)
        plt.show()
        
        
    def plot_weekend_rank_mojo_vs_tweets(self, first_run = False):
        mojo_df = self.mojo_box_office_df
        
        if first_run:
            mojo_df = mojo_df[mojo_df['end_date'] <= self.first_run_end]
        
        mojo_df["weekend_tweet_count"] = mojo_df.apply(lambda row: self.get_geotweet_count_by_dates(row["start_date"], row["end_date"]), axis = 1)
        
        
        ax = mojo_df.plot(x="start_date", y="rank", legend=False, label="Weekend Ranking")
        ax.set(xlabel='Weekend Start Date', ylabel='Weekend Ranking')
     #   ax.invert_yaxis()
        ax.set_ylim(ax.get_ylim()[::-1])
        ax2 = ax.twinx()
        ax2.set(ylabel = 'Tweet Count')
        mojo_df.plot(x="start_date", y="weekend_tweet_count", ax=ax2, legend=False, color="r", label="Tweet Count")
      
        lines_1, labels_1 = ax.get_legend_handles_labels()
        lines_2, labels_2 = ax2.get_legend_handles_labels()
        
        lines = lines_1 + lines_2
        labels = labels_1 + labels_2
      
        ax.legend(lines, labels, loc=0)  

        plt.title("{0} Weekend Ranking".format(self.title))
        plt.setp(ax.get_xticklabels(), rotation=45)
        plt.show()
        
    def plot_weekend_takings_mojo_against_tweets(self, first_run):
        mojo_df = self.mojo_box_office_df
        
        if first_run:
            mojo_df = mojo_df[mojo_df['end_date'] <= self.first_run_end]
        
        mojo_df['weekend_gross_thou'] = mojo_df['weekend_gross_usd'].replace('[\£,]', '', regex=True).astype(float) / 1000
        mojo_df["weekend_tweet_count"] = mojo_df.apply(lambda row: self.get_geotweet_count_by_dates(row["start_date"], row["end_date"]), axis = 1)
        
        ax = sns.regplot(x="weekend_gross_thou", y="weekend_tweet_count", data=mojo_df)

        ax.set(xlabel="Gross Takings ($thou)", ylabel="Tweet Count")
        plt.title("{0} Weekend Takings vs Tweet Count".format(self.title))
        plt.show()
        
    def plot_weekend_tweets_against_rank(self, first_run):
        mojo_df = self.mojo_box_office_df
        
        if first_run:
            mojo_df = mojo_df[mojo_df['end_date'] <= self.first_run_end]
        
        mojo_df["weekend_tweet_count"] = mojo_df.apply(lambda row: self.get_geotweet_count_by_dates(row["start_date"], row["end_date"]), axis = 1)
        
        ax = sns.regplot(x="rank", y="weekend_tweet_count", data=mojo_df)

        ax.set(xlabel="Weekend Rank", ylabel="Tweet Count")
        plt.title("{0} Weekend Rank vs Tweet Count".format(self.title))
        plt.show()
        
    def corellate_weekend_takings_against_tweets(self, full_week = False, week_inc_weekend = False, first_run = False, critical_period = False, senti_class = None):
        mojo_df = self.mojo_box_office_df
        
        results = []
        if (mojo_df.shape[0] > 1):
            if first_run:
                mojo_df = mojo_df[mojo_df['end_date'] <= self.first_run_end]
                
            if critical_period:
                start = datetime.fromtimestamp(self.critical_start.timestamp())
                end = datetime.fromtimestamp(self.critical_end.timestamp())
                
                mojo_df = mojo_df[(mojo_df['start_date'] >= self.critical_start) & (mojo_df['end_date'] <= self.critical_end)]
                       
            
            mojo_df['weekend_gross_thou'] = mojo_df['weekend_gross_usd'].replace('[\£,]', '', regex=True).astype(float) / 1000
            mojo_df["weekend_tweet_count"] = mojo_df.apply(lambda row: self.get_geotweet_count_by_dates(row["start_date"], row["end_date"], senti_class), axis = 1)
              
            
            tweet_col = "weekend_tweet_count"
            if full_week:
                mojo_df["week_tweet_count"] = mojo_df.apply(lambda row: self.get_geotweet_count_by_dates(row["start_date"] - timedelta(days=4), row["start_date"]), axis = 1)
                tweet_col = "week_tweet_count"
                
            if week_inc_weekend:
                mojo_df["week_tweet_count_weekend"] = mojo_df.apply(lambda row: self.get_geotweet_count_by_dates(row["start_date"] - timedelta(days=4), row["end_date"]), axis = 1)
                tweet_col = "week_tweet_count_weekend"
            
            total_tweets = mojo_df[tweet_col].sum()
            
            pearson = stats.pearsonr(mojo_df['weekend_gross_thou'] , mojo_df[tweet_col])
            pearson_res = {"movieId" : self.movieId, 
                          "method" : "pearson", 
                          "coef" : pearson[0], 
                          "p_val" : pearson[1],
                          "tweet_count" : total_tweets,
                          "weekends" : mojo_df.shape[0]}
    
            spearman = stats.spearmanr(mojo_df['weekend_gross_thou'] , mojo_df[tweet_col])
            spearman_res = {"movieId" : self.movieId,  
                          "method" : "spearman", 
                          "coef" : spearman[0], 
                          "p_val" : spearman[1],
                          "tweet_count" : total_tweets,
                          "weekends" : mojo_df.shape[0]}
            
            kendall = stats.kendalltau(mojo_df['weekend_gross_thou'] , mojo_df[tweet_col])
            kendall_res = {"movieId" : self.movieId, 
                          "method" : "kendalltau", 
                          "coef" : kendall[0], 
                          "p_val" : kendall[1],
                          "tweet_count" : total_tweets,
                          "weekends" : mojo_df.shape[0]}
        
        

            results.append(pearson_res)                
            results.append(spearman_res)
            results.append(kendall_res)
            
            
        else:
            results.append({"movieId" : self.movieId,
                            "method" : "NA",
                           "coef" : 0,
                           "p_val" : 0,
                           "tweet_count" : 0 ,
                           "weekends" : mojo_df.shape[0]})
        
        return pd.DataFrame(results)
    
    def corellate_weekend_takings_against_rank(self, first_run):
        mojo_df = self.mojo_box_office_df
        
        if first_run:
            mojo_df = mojo_df[mojo_df['end_date'] <= self.first_run_end]
        
        mojo_df["weekend_tweet_count"] = mojo_df.apply(lambda row: self.get_geotweet_count_by_dates(row["start_date"], row["end_date"]), axis = 1)
              
        pearson = stats.pearsonr(mojo_df['rank'] , mojo_df["weekend_tweet_count"])
        pearson_res = {"movieId" : self.movieId, 
                      "method" : "pearson", 
                      "coef" : pearson[0], 
                      "p_val" : pearson[1]}

        spearman = stats.spearmanr(mojo_df['rank'] , mojo_df["weekend_tweet_count"])
        spearman_res = {"movieId" : self.movieId,  
                      "method" : "spearman", 
                      "coef" : spearman[0], 
                      "p_val" : spearman[1]}
        
        kendall = stats.kendalltau(mojo_df['rank'] , mojo_df["weekend_tweet_count"])
        kendall_res = {"movieId" : self.movieId, 
                      "method" : "kendalltau", 
                      "coef" : kendall[0], 
                      "p_val" : kendall[1]}
        
        results = []
        results.append(pearson_res)                
        results.append(spearman_res)
        results.append(kendall_res)
        
        return pd.DataFrame(results)
        
    def get_geotweets_by_dates(self, start_date = None, end_date = None, senti_class = None):
        
        if start_date == None:
            #try two weeks prior to release
            start_date = self.ukReleaseDate
            start_date = datetime.combine((start_date - timedelta(days=14)), datetime.min.time())
        else:
            start_date = datetime.combine(start_date, datetime.min.time())
                     
        if end_date == None: 
            end_date = self.first_run_end    
            end_date = datetime.combine((end_date + timedelta(days=14)), datetime.max.time())
        else:
            end_date = datetime.combine(end_date, datetime.min.time())
        
        
        tweets = database_helper.select_geo_tweets(self.movieId, senti_class=senti_class)
        

        tweets = tweets[(tweets.created_at >= start_date) & (tweets.created_at <= end_date)]
        
        return tweets
    
    def get_geotweet_count_by_dates(self, start_date = None, end_date = None, senti_class=None):
        tweets = self.get_geotweets_by_dates(start_date, end_date, senti_class)
        
        return len(tweets)
        
    def plot_geotweets(self, normalize = True, cinema_run = False):
        #NB TIDY THIS UP
        # regional_pop = { 'Scotland Euro Region' :  5463300,  
        #         'East Midlands Euro Region' : 4835928, 
        #         'London Euro Region' : 8961989, 
        #         'North West Euro Region' : 7341196, 
        #         'West Midlands Euro Region' : 5934037,
        #         'Yorkshire and the Humber Euro Region' : 5502967,
        #         'South East Euro Region' : 9180135, 
        #         'North East Euro Region' : 2669941,
        #         'Wales Euro Region' : 3152879, 
        #         'Eastern Euro Region' : 6236072,
        #         'South West Euro Region' : 5624696} 
        
        
        #region_tweets_count_df = database_helper.select_query("tweets_region_count")
        cell_tweet_count_df = database_helper.select_query("tweet_cell_count")
  
        title = "{0} tweets per region".format(self.title)
        map_col = 'counts'
        gb = gpd.read_file("../../ProjectData/Data/GB/european_region_region.shp")
        
        tweets = self.get_geotweets_by_dates() if cinema_run else database_helper.select_geo_tweets(self.movieId)
        
        #remove any tweets without geometry info
        #tweets =  database_helper.select_geo_tweets(self.movieId)
        
        #if cinema_run: 
         #   tweets = get_geotweets_by_dates
        
        tweets.dropna(subset=["geombng"], inplace=True)
        gb_tweets = sjoin(tweets, gb, how='inner')
        #THIS WAS FOR NORMALIZING BY POPULATION
        # tweet_freq = gb_tweets.groupby('NAME').size().reset_index(name='counts')
        
        # if normalize:
        #     tweet_freq['population'] = tweet_freq['NAME'].map(regional_pop)
        #     tweet_freq["norm_count"] = tweet_freq['counts'] / tweet_freq['population']
        #     tweet_freq["norm_count"] = (tweet_freq['counts'] / tweet_freq['population']) * 1000000
        #     map_col = 'norm_count'
        
        #NORMALIZE BY UK REGION
        # tweet_freq = gb_tweets.groupby('UNIT_ID').size().reset_index(name='counts')
        # if normalize:
        #     tweet_freq = tweet_freq.merge(region_tweets_count_df, left_on="UNIT_ID", right_on="unit_id")
        #     tweet_freq = tweet_freq.rename(columns={'tweet_count' : 'region_tweet_count'})
        #     tweet_freq = tweet_freq.drop(columns=['unit_id'])
        #     tweet_freq["norm_count"] = (tweet_freq['counts'] / tweet_freq['region_tweet_count']) * 1000000
        #     map_col = 'norm_count'
        
        tweet_freq = gb_tweets.groupby('NUMBER').size().reset_index(name='counts')
        if normalize:
            tweet_freq = tweet_freq.merge(cell_tweet_count_df, left_on="NUMBER", right_on="cellid")
            tweet_freq = tweet_freq.rename(columns={'tweet_count' : 'cell_tweet_count'})
            tweet_freq = tweet_freq.drop(columns=['cellid'])
            tweet_freq["norm_count"] = (tweet_freq['counts'] / tweet_freq['cell_tweet_count']) * 1000000
            map_col = 'norm_count'
        
        map_freq = gb.merge(tweet_freq, left_on='NUMBER', right_on='NUMBER')
        fig, ax = plt.subplots(1, 1)
        ax.axis('off')
        ax.set_title(title)
        fig.set_dpi(100)
        map_freq.plot(column=map_col, ax=ax, legend=True, cmap='OrRd')
        
    def plot_tweets_kde_map(self, cinema_run = False):
        #http://darribas.org/gds_scipy16/ipynb_md/06_points.html
        gb = gpd.read_file("../../ProjectData/Data/GB/european_region_region.shp")
            
        fig, ax = plt.subplots(1,figsize=(9,9))
        #remove any tweets without geometry info
        tweets = self.get_geotweets_by_dates() if cinema_run else database_helper.select_geo_tweets(self.movieId)
        
        tweets.dropna(subset=["geombng"], inplace=True)
        gb_tweets = sjoin(tweets, gb, how='inner')
        gb_tweets["lat"] = gb_tweets["geombng"].y
        gb_tweets["lng"] = gb_tweets["geombng"].x
        
        gb.plot(ax=ax)
        
        sns.kdeplot(gb_tweets['lng'], gb_tweets['lat'], 
                    shade=True, shade_lowest=False, cmap='viridis',
                     ax=ax)
    
    
        
        ax.set_axis_off()
        plt.axis('equal')
        plt.title(self.title + " Tweet Density")
        plt.show()
        plt.clf()
        plt.cla()
        plt.close()
        
    def plot_tweets_over_time(self, plot_run=True, cinema_run = False, critical_period = False):
        releaseDate = self.ukReleaseDate
        endWeekend = self.first_run_end
       # endWeekend = self.box_office_df.iloc[self.box_office_df['weeksOnRelease'].idxmax()].weekendEnd
        fig, ax = plt.subplots()
        if plot_run:
            ax.axvspan(*mdates.datestr2num([str(releaseDate), str(endWeekend)]), color='skyblue', alpha=0.5)
        
        tweets = self.get_geotweets_by_dates() if cinema_run else database_helper.select_geo_tweets(self.movieId)
        tweets =  database_helper.select_geo_tweets(self.movieId, self.critical_start, self.critical_end) if critical_period else tweets

        tweets['date'] = tweets['created_at'].dt.date
        date_freq = tweets.groupby('date').size().reset_index(name='count') 
        date_freq.sort_values('date')
        date_freq['date'] = pd.to_datetime(date_freq['date'], errors='coerce')
        
        indexes, _ = scipy.signal.find_peaks(date_freq['count'], height=7, distance=2.1)
        peak_dates = date_freq[date_freq.index.isin(indexes)]
           
        peak_dates['color'] = date_freq.apply(lambda row: "g" if row["date"] == self.ukReleaseDate else "r", axis=1)
        peak_dates['label'] = date_freq.apply(lambda row: "Release Date" if row["date"] == self.ukReleaseDate else "Other", axis=1)
        
        self.trailers_df["publishDate_date"] = self.trailers_df.apply(lambda row: row["publishDate"].date(), axis = 1)
        peak_dates['color'] = peak_dates.apply(lambda row: "b" if row["date"] in self.trailers_df["publishDate_date"].values else row['color'], axis = 1)
        peak_dates['label'] = peak_dates.apply(lambda row: "Trailer Release" if row["date"] in self.trailers_df["publishDate_date"].values else row['label'], axis = 1)

        c_palette = {"Release Date" : "g", "Trailer Release" : "b", "Other" : "y"}
        l_order = ["Release Date", "Trailer Release", "Other"]
        
        ax.plot(date_freq['date'], date_freq['count'])
        sns.scatterplot(x="date", y="count", data=peak_dates, hue="label", palette=c_palette, hue_order=l_order, ax=ax)

        

        ax.legend()
        handles, labels = ax.get_legend_handles_labels()
        ax.legend(handles=handles[1:], labels=labels[1:])
        
        print('Peaks are: %s' % (indexes))
        #plt.xticks(date_freq['date'])
        plt.xlabel("Date")
        plt.ylabel("Tweet Count")
        plt.title(self.title + " Tweets over time")
        plt.xticks(rotation=40)
        plt.show()

        
    def get_tweet_peak_dates(self):
        tweets = database_helper.select_geo_tweets(self.movieId)
     #   tweets =  database_helper.select_geo_tweets(self.movieId, self.critical_start, self.critical_end) if critical_period else tweets

        tweets['date'] = tweets['created_at'].dt.date
        date_freq = tweets.groupby('date').size().reset_index(name='count') 
        date_freq.sort_values('date')
        date_freq['date'] = pd.to_datetime(date_freq['date'], errors='coerce')
        indexes, _ = scipy.signal.find_peaks(date_freq['count'], height=7, distance=2.1)    
        
        return date_freq.iloc[indexes]
    
    def get_tweet_peak_events(self):
        print("{0} {1}".format(self.title, self.movieId))
        
        peak_dates_count = self.get_tweet_peak_dates()
        self.trailers_df["date"] = self.trailers_df.apply(lambda row: row["publishDate"].date(), axis=1).astype('datetime64[ns]')
        
        results_df = pd.merge(peak_dates_count, self.trailers_df[['date','youtubeId']], on='date', how='left')
        
        if (results_df.shape[0] > 0):
                
            
            results_df["movie_release"] = results_df.apply(lambda row: row["date"] == self.ukReleaseDate, axis = 1)
            
    
            
            opening_start = self.mojo_box_office_df.iloc[0]["start_date"]
            opening_end = self.mojo_box_office_df.iloc[0]["end_date"]
            
            results_df["movie_opening_weekend"] = results_df.apply(lambda row: (opening_start <= row["date"].date()) & (opening_end >= row["date"].date()), axis=1)
            results_df = results_df.sort_values(by='count', ascending=False)
            results_df["movieId"] = self.movieId
            
            return results_df
        
        else:
            dummy = {"date" : None, 
                     "count" : 0, 
                     "movie_release" : False, 
                     "movie_opening_weekend" : False, 
                     "movieId" : self.movieId}
            return pd.DataFrame([dummy])
        
        
        
        
    def plot_tweet_sentiment_over_time(self, avg = False):
        analyser = SentimentIntensityAnalyzer()
        tweets =  database_helper.select_geo_tweets(self.movieId)
        tweet_sentiment = []
        for index, row in tweets.iterrows(): 
            sentiment = analyser.polarity_scores(row['msg'])
            tweet_sentiment.append(sentiment['compound'])
            
        tweets['compound_sentiment'] = tweet_sentiment
        tweets['date'] = tweets['created_at'].dt.date
        date_sentiment = tweets.groupby(['date'], as_index = False).sum()
        date_sentiment.sort_values('date')
        date_sentiment['date'] = pd.to_datetime(date_sentiment['date'], errors='coerce')
        date_sentiment['count'] = tweets.groupby('date').size().reset_index(name='count')['count']
        date_sentiment["compound_norm"] = date_sentiment['compound_sentiment'] / date_sentiment['count']
        
        y_col = 'compound_norm' if avg else 'compound_sentiment'
        
        indexes, _ = scipy.signal.find_peaks(date_sentiment[y_col], height=7, distance=2.1)
        #date_freq.set_index('date')['count'].plot(markevery=indexes.tolist())
        plt.plot(date_sentiment['date'], date_sentiment[y_col], marker='D',markerfacecolor='r', markevery=indexes.tolist())
        
        print('Peaks are: %s' % (indexes))
        #plt.xticks(date_freq['date'])
        plt.xlabel("Date")
        plt.ylabel("Tweet Sentiment")
        plt.title(self.title + " Tweet sentiment over time")
        plt.xticks(rotation=40)
        plt.show()

    def plot_tweets_by_class(self, cinema_run = False):
        tweets = self.get_geotweets_by_dates() if cinema_run else database_helper.select_geo_tweets(self.movieId)
        class_freq = tweets.groupby('senti_class').size().reset_index(name='counts')
        fig = plt.figure()
        ax = fig.add_axes([0,0,1,1])
        ax.bar(class_freq["senti_class"], class_freq["counts"])
        ax.set_xlabel("Sentiment Class")
        ax.set_ylabel("Tweet COunt")
        ax.set_title(self.title + " Tweet sentiment")
        plt.show()
        
    def plot_tweets_by_class_and_region(self, cinema_run = False):
        sns.set(style="whitegrid")
        region_tweets = tweet_helper.get_tweet_regions(self.movieId)
        title = self.title + " Tweets per region"
        grouped_tweets = region_tweets.groupby(["region", "senti_class"]).size().reset_index(name = "counts")
        g = sns.catplot(x="region", y="counts", hue="senti_class", data=grouped_tweets, height=6, kind="bar", palette="muted", legend_out=False)
        fig = g.fig
        g.set_ylabels("Tweet Counts")
        g.set_xlabels("Region")
        g.set_xticklabels(rotation=40, ha="right")
        fig.subplots_adjust(top=0.9)
        fig.suptitle(title, fontsize=16)
        plt.show()
        
    def plot_tweets_by_class_and_region_stacked(self, normalize = True):
        region_tweets = tweet_helper.get_tweet_regions(self.movieId)
        title = self.title + " Tweets per region"
        grouped_tweets = region_tweets.groupby(["region", "senti_class"]).size().reset_index(name = "counts")
        
        plot_col = "counts"
        if normalize:
            grouped_sum = grouped_tweets.groupby(['region']).sum()
            grouped_sum.rename(columns={'counts' : 'total'}, inplace=True)
            grouped_tweets = grouped_tweets.join(grouped_sum, on="region", how="inner")
            grouped_tweets["percentage"] = grouped_tweets["counts"] / grouped_tweets["total"] 
            plot_col = "percentage"
        
        data = grouped_tweets.pivot(index="region", columns="senti_class", values=plot_col)
        data.plot.bar(stacked=True)      
                
        
    def plot_time_maps_per_week(self):
        for index, row in self.mojo_box_office_df.iterrows():
            week_start = row["start_date"]  - timedelta(days=4)
            week_end = row["end_date"]
            
            print(week_start)
            print(week_end)
            self.plot_time_map(start_date = week_start, end_date = week_end)
            self.plot_heated_time_map(start_date = week_start, end_date = week_end)
    
    
    def plot_time_map_critical(self, heated = False):
        if heated:
            self.plot_heated_time_map(start_date = self.critical_start, end_date = self.critical_end)
        else:            
            self.plot_time_map(start_date = self.critical_start, end_date = self.critical_end)
    
    def plot_time_map(self, movie_run = False, start_date = None, end_date = None):
        #adapted from https://districtdatalabs.silvrback.com/time-maps-visualizing-discrete-events-across-many-timescales
        if movie_run:    
            start_date = datetime.combine((self.ukReleaseDate - timedelta(days=14)), datetime.min.time())
            end_date = datetime.combine((self.first_run_end + timedelta(days=14)), datetime.max.time())
            
        elif not (start_date == None) and not (end_date == None):
            start_date = datetime.combine(start_date, datetime.min.time())
            end_date = datetime.combine(end_date, datetime.max.time())
         
        tweets = database_helper.select_geo_tweets(self.movieId, start_date, end_date)
        tweets = tweets.sort_values(by=['created_at']).reset_index()
        times = tweets['created_at']
        times_tot_mins = 24*60 - (60*np.array([t.hour for t in times]) + np.array([t.minute for t in times]))
        
        if tweets.shape[0] > 0:
            seps=np.array([(times[i]-times[i-1]).total_seconds() for i in range(1,len(times))])
            seps[seps==0]=1 # convert zero second separations to 1-second separations
            
            sep_array=np.zeros((len(seps)-1,2)) # 1st column: x-coords, 2nd column: y-coords
            sep_array[:,0]=seps[:-1]
            sep_array[:,1]=seps[1:]
            
            Ncolors=24*60 
            
            ## set up color list
            red=Color("red")
            blue=Color("blue")
            color_list = list(red.range_to(blue, Ncolors)) # range of colors evenly speced on the spectrum between red and blue. Each element is a colour object
            color_list = [c.hex for c in color_list] # give hex version
            
            fig=plt.figure()
            ax =fig.add_subplot(111)
             	
            colormap = plt.cm.get_cmap('rainbow')  # see color maps at http://matplotlib.org/users/colormaps.html
            
            order=np.argsort(times_tot_mins[1:-1]) # so that the red dots are on top
            #	order=np.arange(1,len(times_tot_mins)-2) # dots are unsorted
            
            sc= ax.scatter(sep_array[:,0][order],sep_array[:,1][order],c=times_tot_mins[1:-1][order],vmin=0,vmax=24*60,s=25,cmap=colormap,marker='o',edgecolors='none')
            # taken from http://stackoverflow.com/questions/6063876/matplotlib-colorbar-for-scatter
             	
            color_bar=fig.colorbar(sc,ticks=[0,24*15,24*30,24*45,24*60],orientation='vertical')
            color_bar.ax.set_yticklabels(['Midnight','6:00','Noon','18:00','Midnight'])
             	
            ax.set_yscale('log') # logarithmic axes
            ax.set_xscale('log')
            
            plt.minorticks_off()
            pure_ticks = np.array([1e-3,1,10,60*10,2*3600,1*24*3600, 7*24*3600]) # where the tick marks will be placed, in units of seconds.
            labels = ['1 msec','1 sec','10 sec','10 min','2 hr','1 day','1 week']  # tick labels
            
            max_val = np.max([np.max(sep_array[:,0]), np.max(sep_array[:,1])])
             	
            ticks = np.hstack((pure_ticks, max_val))
            
            min_val = np.min([np.min(sep_array[:,0]), np.min(sep_array[:,1])])
             	
            
            title = "{0} Time Map".format(self.title)
            
            if not (start_date == None) and (not end_date == None):
                title += " {0} - {1}".format(start_date.date(), end_date.date())
                
            plt.title(title)
            plt.xticks(ticks,labels)
            plt.yticks(ticks,labels)
            plt.xticks(rotation=40)
         	
            plt.xlabel('Time Before Tweet')
            plt.ylabel('Time After Tweet')
            
            plt.xlim((min_val, max_val))
            plt.ylim((min_val, max_val))
             	
            ax.set_aspect('equal')
            plt.tight_layout()
            
            plt.show()
        else:
            print("No tweets for {0} between {1} and {2}".format(self.title, start_date.date(), end_date.date()))
        
    def plot_heated_time_map(self, movie_run = False, start_date = None, end_date = None):
        #adapted from https://districtdatalabs.silvrback.com/time-maps-visualizing-discrete-events-across-many-timescales               
        if movie_run:    
            start_date = datetime.combine((self.ukReleaseDate - timedelta(days=14)), datetime.min.time())
            end_date = datetime.combine((self.first_run_end + timedelta(days=14)), datetime.max.time())
            
        elif not (start_date == None) and not (end_date == None):
            start_date = datetime.combine(start_date, datetime.min.time())
            end_date = datetime.combine(end_date, datetime.max.time())

         
        tweets = database_helper.select_geo_tweets(self.movieId, start_date, end_date)
        tweets = tweets.sort_values(by=['created_at']).reset_index()
        times = tweets['created_at']
        times_tot_mins = 24*60 - (60*np.array([t.hour for t in times]) + np.array([t.minute for t in times]))
        
        
        if tweets.shape[0] > 0:
            seps=np.array([(times[i]-times[i-1]).total_seconds() for i in range(1,len(times))])
            seps[seps==0]=1 # convert zero second separations to 1-second separations
            
            sep_array=np.zeros((len(seps)-1,2)) # 1st column: x-coords, 2nd column: y-coords
            sep_array[:,0]=seps[:-1]
            sep_array[:,1]=seps[1:]
            
            Nside=4*256 # number of pixels along the x and y directions
            width=4 # the number of pixels that specifies the width of the Gaussians for the Gaussian filter
            
            # choose points within specified range. Example plot separations greater than 5 minutes:
            #	indices = (sep_array[:,0]>5*60) & (sep_array[:,1]>5*60)
            indices=range(sep_array.shape[0]) # all time separations
            
            x_pts = np.log(sep_array[indices,0])
            y_pts = np.log(sep_array[indices,1])
            
            
            #x_pts = sep_array[indices,0]
            #y_pts = sep_array[indices,1]
            
            min_val = np.min([np.min(x_pts), np.min(y_pts)])
               	
            x_pts = x_pts - min_val
            y_pts = y_pts - min_val
               	
            max_val = np.max([np.max(x_pts), np.max(y_pts)])
               	
            x_pts = x_pts * (Nside-1)/max_val
            y_pts = y_pts * (Nside-1)/max_val
               	
            img=np.zeros((Nside,Nside))
               
            for i in range(len(x_pts)):
                img[int(x_pts[i]),int(y_pts[i])] +=1
               
            img = ndi.gaussian_filter(img,width) # apply Gaussian filter
            img = np.sqrt(img) # taking the square root makes the lower values more visible
            img=np.transpose(img) # needed so the orientation is the same as scatterplot
               
            plt.imshow(img, origin='lower')
               	
            ## create custom tick marks. Calculate positions of tick marks on the transformed log scale of the image array
            plt.minorticks_off()
               	
            ## change font, which can also now accept latex: http://matplotlib.org/users/usetex.html
            plt.rc('text',usetex=False)
            plt.rc('font',family='serif')
               
            my_max = np.max([np.max(sep_array[indices,0]), np.max(sep_array[indices,1])])
            my_min = np.max([np.min(sep_array[indices,0]), np.min(sep_array[indices,1])])
            
            pure_ticks = np.array([1e-3,1,10,60*10,2*3600,1*24*3600, 7*24*3600]) 
            # where the tick marks will be placed, in units of seconds. An additional value will be appended to the end for the max
            labels = ['1 msec','1 sec','10 sec','10 min','2 hr','1 day','1 week']  # tick labels
               
            index_lower=np.min(np.nonzero(pure_ticks >= my_min)) 
            # index of minimum tick that is greater than or equal to the smallest time interval. This will be the first tick with a non-blank label
               
            index_upper=np.max(np.nonzero(pure_ticks <= my_max))
            # similar to index_lower, but for upperbound
               	
            ticks = pure_ticks[index_lower: index_upper + 1]
            ticks = np.log(np.hstack((my_min, ticks, my_max ))) # append values to beginning and end in order to specify the limits
            ticks = ticks - min_val
            ticks *= (Nside-1)/(max_val)
               	
            labels= np.hstack(('',labels[index_lower:index_upper + 1],'')) # append blank labels to beginning and end
            
            title = "{0} Time Map".format(self.title)
            
            if not (start_date == None) and (not end_date == None):
                title += " {0} - {1}".format(start_date.date(), end_date.date())
                
            plt.title(title)
            plt.xticks(ticks,labels)
            plt.yticks(ticks,labels)
            plt.xticks(rotation=40)
             	
            plt.xlabel('Time Before Tweet')
            plt.ylabel('Time After Tweet')
            plt.show()
        else:
            print("No tweets for {0} between {1} and {2}".format(self.title, start_date.date(), end_date.date()))

        