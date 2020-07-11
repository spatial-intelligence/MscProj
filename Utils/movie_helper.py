#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 11 09:33:06 2020

@author: andy
"""

from tqdm import tqdm
import pandas as pd
import sys
import re
sys.path.insert(1, '/home/andy/Documents/MscProject/MscProj/Entities')
sys.path.insert(1, '/home/andy/Documents/MscProject/MscProj/Utils')

from movie import Movie
import database_helper
import tweet_helper
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np


def get_movies_df():
    movies_df = database_helper.select_query("movies", {"investigate" : "1"})
    movies_df = movies_df.sort_values(by=['movieId'])   
    return movies_df

def get_movies():
    #movies_df = database_helper.select_query("movies", { "enabled" : "1" })
    movies_df = database_helper.select_query("movies", {"investigate" : "1"})
    movies_df = movies_df.sort_values(by=['movieId'])  
    return gen_movies(movies_df)

def gen_movies(movies_df):
    movies = []
    with tqdm(total=len(movies_df)) as pbar:
        for index, row in movies_df.iterrows(): 
            movie = Movie(row)
            movies.append(movie)
            pbar.update(1)
    return movies

def get_movie_by_id(movieId): 
    movies_df = database_helper.select_query("movies", { "movieId" : int(movieId) })
    if (not movies_df.empty):
        return Movie(movies_df.iloc[0])
    
    return None

def get_movie_by_title(title):
    movies_df = database_helper.select_query("movies", { "title" : title })
    if (not movies_df.empty):
        return Movie(movies_df.iloc[0])
    
    return None
    
def set_total_revenue_for_movies():
    movies = get_movies();
    with tqdm(total=len(movies)) as pbar:
        for movie in movies:
            total_rev = movie.box_office_df.iloc[movie.box_office_df['weeksOnRelease'].idxmax()]['grossToDate']
            update_params = { "totalRevenue" : total_rev }
            select_params = { "movieId" : movie.movieId }
            database_helper.update_data("movies", update_params = update_params, select_params = select_params)
            pbar.update(1)
            
def get_top_by_column(column, max_movies = 20):
    sql = """SELECT * FROM public.movies 
             WHERE "investigate" = '1'
             ORDER BY "{0}" DESC LIMIT {1}""".format(column, max_movies)

    return database_helper.get_data(sql)

def get_top_movies_by_column(column, max_movies = 20):
    top_df = get_top_by_column(column, max_movies)
    return gen_movies(top_df) 

def get_lowest_by_column(column, max_movies = 20):
    sql = """SELECT * FROM public.movies 
             WHERE "investigate" = '1'
             ORDER BY "{0}" ASC LIMIT {1}""".format(column, max_movies)
             
    return database_helper.get_data(sql)  

def get_lowest_movies_by_column(column, max_movies = 20):
    bottom_df = get_lowest_by_column(column, max_movies)
    return gen_movies(bottom_df)    

def count_tweets(movieId, start_date = None, end_date = None):
    sql = """
          SELECT "movieid", COUNT(*) 
          FROM movie_tweets2019 
          WHERE "movieid" = {0}""".format(movieId)   
          
    if not start_date == None:
        sql += """ AND "created_at" >= {0}""".format(start_date)
        
    if not end_date == None:
        sql += """ AND "created_at" <= {0}""".format(end_date)
          
    sql += """ GROUP BY "movieid"""""

        
    tweet_count = database_helper.get_data(sql)
    return tweet_count

def categorize_by_gross_profit():
    movies_df = get_movies_df()
    
    #calculate gross profit based on budget and worldwide gross
    movies_df["worldwide_gross_usd_norm"] = movies_df['worldwide_gross_usd'].replace('[\£,]', '', regex=True).astype(float) / 1000000
    movies_df["budget_usd_norm"] = movies_df['budget_usd'].replace('[\£,]', '', regex=True).astype(float) / 1000000
    movies_df["gross_profit_usd_norm"] = movies_df["worldwide_gross_usd_norm"] - movies_df["budget_usd_norm"]
    movies_df["gross_profit_usd"] = movies_df["worldwide_gross_usd"].replace('[\£,]', '', regex=True).astype(float) - movies_df["budget_usd"].replace('[\£,]', '', regex=True).astype(float)
    
    custom_bucket_array =[-50, 0, 50, 150, 300, 2500]
    bucket_labels = ['< $0 (Flop)', '$0 < $50m', '$50m < $150m', '$150m < $300m', ' > $300m (BlockBuster)' ]
    
    movies_df['class'] = pd.cut(movies_df['gross_profit_usd_norm'], custom_bucket_array,labels= bucket_labels)
    
    for index, row in movies_df.iterrows(): 
            updates = { "gross_profit_usd" : row["gross_profit_usd"],
                    "profit_class" : row["class"]
                    }
            selects = {"movieId" : row["movieId"]}
            database_helper.update_data("movies", update_params = updates, select_params = selects)
    
    return movies_df

def calculate_percentage_profit():
    movies_df = get_movies_df()
    movies_df["gross_profit_norm"] = movies_df["gross_profit_usd"].replace('[\£,]', '', regex=True).astype(float)
    movies_df["budget_norm"] = movies_df["budget_usd"].replace('[\£,]', '', regex=True).astype(float)
    movies_df["return_percentage"] = (movies_df["gross_profit_norm"] / movies_df["budget_norm"]) * 100
    
    for index, row in movies_df.iterrows(): 
        updates = { "return_percentage" : row["return_percentage"] }
        selects = {"movieId" : row["movieId"]}
        database_helper.update_data("movies", update_params = updates, select_params = selects)
    
    return movies_df


def categorize_by_return_percentage():
    movies_df = get_movies_df()
    
    custom_bucket_array =[-100, 0, 100, 400, 1000, 2000]
    bucket_labels = ['< %0 (Flop)', '%0-100%', '%100-%400', '%400-%1000', '> %1000 (BlockBuster)']
    movies_df['class'] = pd.cut(movies_df['return_percentage'], custom_bucket_array,labels= bucket_labels)
    
    for index, row in movies_df.iterrows(): 
            updates = { "return_class" : row["class"] }
            selects = {"movieId" : row["movieId"]}
            database_helper.update_data("movies", update_params = updates, select_params = selects)
    
    return movies_df

def categorize_by_uk_percentage():
    movies_df = get_movies_df()
    
    custom_bucket_array =[0, 2, 4, 6, 12, 20]
    bucket_labels = ['0% - 2%', '2% - 4%', '4% - 6%', '6% - 12%', '> 12%']
    movies_df['class'] = pd.cut(movies_df['uk_percentage'], custom_bucket_array,labels= bucket_labels)
    
    for index, row in movies_df.iterrows(): 
            updates = { "uk_percentage_class" : row["class"] }
            selects = {"movieId" : row["movieId"]}
            database_helper.update_data("movies", update_params = updates, select_params = selects)
    
    return movies_df

  
def calculate_uk_percentage_gross():
    movies_df = get_movies_df()
    movies_df["worldwide_norm"] = movies_df["worldwide_gross_usd"].replace('[\£,]', '', regex=True).astype(float)
    movies_df["uk_takings_norm"] = movies_df["uk_gross_usd"].replace('[\£,]', '', regex=True).astype(float)
    movies_df["uk_percentage"] = (movies_df["uk_takings_norm"] / movies_df["worldwide_norm"]) * 100
    
    for index, row in movies_df.iterrows(): 
        updates = { "uk_percentage" : row["uk_percentage"] }
        selects = {"movieId" : row["movieId"]}
        database_helper.update_data("movies", update_params = updates, select_params = selects)
    
    return movies_df
    

def get_movie_genres():
    movies_df = get_movies_df()
    movies_df["genres_list"] = movies_df["genres"].apply(lambda x: x.split(',') if x != None else [])
    genre_list = movies_df["genres_list"].to_list()
    
    genre_list = list(set([item for sublist in genre_list for item in sublist]))
    
    return genre_list


def get_movie_genre_counts():
    movies_df = get_movies_df()
    genre_list = get_movie_genres()
    
    genre_df = pd.DataFrame(columns=["genre", "count"])
    
    counts = []
    for genre in genre_list:
        row_s = movies_df.apply(lambda x: True if genre in x["genres"] else False, axis=1)
        counts.append(len(row_s[row_s == True].index))
     
    genre_df["genre"] = genre_list
    genre_df["count"] = counts
    
    return genre_df

def get_genre_tweet_counts():
    genre_list = get_movie_genres()
    counts = []
    
    for genre in genre_list:
        #get all movies in this genre
        genre_movies = database_helper.select_movies_by_genre(genre)

        tweet_count = 0
        for index, row in genre_movies.iterrows():
            tweet_count += int(count_tweets(row["movieId"])['count'])

            
        counts.append(tweet_count)
        
    genre_df = pd.DataFrame(columns=["genre", "count"])
    genre_df["genre"] = genre_list
    genre_df["count"] = counts
    
    return genre_df

def get_genre_tweet_sentiments():
    genre_list = get_movie_genres()
    
    output_df = pd.DataFrame(columns=['senti_class', 'counts', 'genre'])
    for genre in genre_list:
        genre_movies = database_helper.select_movies_by_genre(genre)
        
        #do the first movie 
        first_tweets = database_helper.select_geo_tweets(genre_movies.iloc[0]['movieId'])
        class_freq = first_tweets.groupby('senti_class').size().reset_index(name='counts')
        
        for index, row in genre_movies.iterrows():
            if index > 0:
                tweets = database_helper.select_geo_tweets(row["movieId"])
                my_class_freq = tweets.groupby('senti_class').size().reset_index(name='counts')
                class_freq['counts'] += my_class_freq['counts']
    
        class_freq['genre'] = genre
        output_df = output_df.append(class_freq)
        
    return output_df

def get_genre_revenues():
    genre_list = get_movie_genres()
                
    genre_revenues = []
    for genre in genre_list:
        genre_movies = database_helper.select_movies_by_genre(genre)  
        genre_movies["profit_mil"] = genre_movies["gross_profit_usd"].replace('[\£,]', '', regex=True).astype(float) / 1000000
        genre_total = genre_movies["profit_mil"].sum()
        
        genre_revenues.append(genre_total)
        
    output_df = pd.DataFrame(columns=["genre", "profit_mil"])
    output_df["genre"] = genre_list
    output_df["profit_mil"] = genre_revenues
    
    return output_df
        
        
def get_genre_movie_class_counts():
    genre_list = get_movie_genres()
      
    output_df = pd.DataFrame(columns=["profit_class", "genre", "counts"])
      
    for genre in genre_list: 
        genre_movies = database_helper.select_movies_by_genre(genre) 
        class_freq = genre_movies.groupby('profit_class').size().reset_index(name="counts")
        class_freq["genre"] = genre
        
        output_df = output_df.append(class_freq)
        
    return output_df


def get_correlation_matrix():
    #based on https://seaborn.pydata.org/examples/many_pairwise_correlations.html
    movies_df = get_movies_df()
    
    #get tweet counts for each movies 
    movies_df["tweet_count"] = movies_df.apply(lambda row: count_tweets(row.movieId)['count'], axis = 1)
    
    
    correlation_subset = movies_df[['budget_usd', 'uk_gross_usd', 'domestic_gross_usd', 'worldwide_gross_usd', 'international_gross_usd', 'gross_profit_usd', 'return_percentage', 'uk_percentage', 'tweet_count']]
    
    #covert money to float ($mil)
    correlation_subset["budget_usd"] = correlation_subset["budget_usd"].replace('[\£,]', '', regex=True).astype(float) / 1000000
    correlation_subset["uk_gross_usd"] = correlation_subset["domestic_gross_usd"].replace('[\£,]', '', regex=True).astype(float) / 1000000
    correlation_subset["domestic_gross_usd"] = correlation_subset["domestic_gross_usd"].replace('[\£,]', '', regex=True).astype(float) / 1000000
    correlation_subset["worldwide_gross_usd"] = correlation_subset["worldwide_gross_usd"].replace('[\£,]', '', regex=True).astype(float) / 1000000
    correlation_subset["international_gross_usd"] = correlation_subset["international_gross_usd"].replace('[\£,]', '', regex=True).astype(float) / 1000000
    correlation_subset["gross_profit_usd"] = correlation_subset["gross_profit_usd"].replace('[\£,]', '', regex=True).astype(float) / 1000000
    

    #computer the correlation 
    corr = correlation_subset.corr()
    
    # Generate a mask for the upper triangle
    mask = np.triu(np.ones_like(corr, dtype=np.bool))
    
    # Set up the matplotlib figure
    f, ax = plt.subplots(figsize=(11, 9))
    
    # Generate a custom diverging colormap
    cmap = sns.diverging_palette(220, 10, as_cmap=True)
    
    # Draw the heatmap with the mask and correct aspect ratio
    sns.heatmap(corr, mask=mask, cmap=cmap, vmax=.3, center=0, 
                square=True, linewidths=.5, cbar_kws={"shrink": .5}) 
    

