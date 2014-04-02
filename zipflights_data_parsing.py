import pandas as pd
import numpy as np

#Columns of interest in BTS OrigDest:Market Survey csv.
USECOLS = [u'MktCoupons', 
            u'Year', 
            u'Quarter', 
            u'Origin', 
            u'Dest', 
            u'AirportGroup', 
            u'TkCarrierChange', 
            u'TkCarrierGroup', 
            u'OpCarrierChange', 
            u'OpCarrierGroup', 
            u'RPCarrier', 
            u'TkCarrier', 
            u'OpCarrier', 
            u'BulkFare', 
            u'Passengers', 
            u'MktFare', 
            u'MktDistance', 
            u'MktMilesFlown', 
            u'NonStopMiles', 
            u'ItinGeoType', 
            u'MktGeoType']


def survey_load_strip_save(filepath_in, filepath_out):
    """
    filepath_in: path to survey csv, e.g.:
        'Origin_and_Destination_Survey_DB1BMarket_2013_3.csv'
    filepath_out: path to stripped version of csv, e.g.:
        'OrigDest_stripped_2013q3.csv'

    Load BTS OrigDest:Market Quarterly Survey csv into a dataframe
    and strip out the repetitive columns and save as a new csv that
    will be concatenated with data from other quarters.
    
    The data contains a large number of listed prices between zero and 
    five dollars, according to the BTS these are largely from tickets
    bought on contract where the actual amount paid is proprietary.  
    These tickets are irrelevant to our analysis so they are also
    stripped out here.
    """

    df = pd.read_csv(filepath_in)

    df = df[USECOLS]

    df = df.loc[df.MktFare >= 6.]

    df.to_csv(filepath_out)

def alphabetize_airports(od_df):
    """
    od_df: Dataframe of OrigDest survey data (most likely 
        stripped of irrevelant columns with survey_load_strip_save, 
        and concatenated with other quarters)

    Our analysis treats flights from LAX to JFK the same as flights
    from JFK to LAX, so add columns 'apt1' and 'apt2' that contain
    airport codes where 'apt1' precedes 'apt2' in the alphabet.
    """
    od_df['apt1'] = None
    od_df['apt2'] = None
    od_df.loc[od_df.Origin < od_df.Dest, 'apt1'] = od_df.Origin
    od_df.loc[od_df.Origin > od_df.Dest, 'apt1'] = od_df.Dest
    od_df.loc[od_df.Origin < od_df.Dest, 'apt2'] = od_df.Dest
    od_df.loc[od_df.Origin > od_df.Dest, 'apt2'] = od_df.Origin

def groupby_route_medians(od_df):
    """
    od_df: Dataframe of OrigDest survey (with 'apt1' and 'apt2' columns
            from alphabetize_airports func.)
    Returns: Dataframe with one row for each 'apt1' to 'apt2' route
        these columns are alphabetized by airport code, so data on flights
        between JFK and LAX will be listed as such (and not LAX, JFK).
    """
    cols_in = ['MktFare', 'NonStopMiles', 'Origin']
    od_meds_dists = od_df.groupby(by=['apt1', 'apt2'])[cols_in].agg([np.median, len])
    od_meds_dists = od_meds_dists.reset_index()

    cols_out = ['apt1', 'apt2', 'MktFareMed', 'Count', 'NonStopMiles', 'Count_dup']

    od_meds_dists.columns = cols_out

    return od_meds_dists[cols_out[:-1]]

def fare_dist_fit(od_meds_df):
    """
    od_meds_df: Dataframe of Fare, Distances and Ticket count data 
        (generated with groupby_route_medians) 
            

    Fit a line to median price versus distance of an airline route, 
    weighted by the number of passengers on the route.  Add columns
    to the dataframe 'pred_price' that is the price expected by this
    linear model based on the distance of a route, and 'delta_price'
    that is 'pred_price' - actual median price.

    """
    
    x = od_meds_df['NonStopMiles']
    y = od_meds_df['MktFareMed']
    weight = od_meds_df['Count']
    fit = np.polyfit(x, y, 1, w = weight)

    od_meds_df['pred_price'] = np.polyval(fit, od_meds_df.NonStopMiles)
    od_meds_df['delta_price'] = od_meds_df.pred_price - od_meds_df.MktFareMed

    def weighted_avg_and_std(values, weights):
        """
        Return the weighted average and standard deviation.

        values, weights -- Numpy ndarrays with the same shape.
        (shamelessly stolen from stack exchange)
        """
        average = np.average(values, weights=weights)
        variance = np.average((values-average)**2, weights=weights)  # Fast and numerically precise
        return (average, np.sqrt(variance))

    wav_str = "Weighted avg and std of predicted prices. USED IN WEB-APP:"
    print wav_str, weighted_avg_and_std(od_meds_df.delta_price, weight)


def dests_by_rank_preds_by_dest(od_meds_df):
    """
    od_meds_df: Dataframe of Fare, Distances, etc. including 'pred_price'
            (see fare_dist_fit)

    Returns: Two Dict of dicts of the form {Origin_code: {1: Dest_Code1, 2: Dest_Code2, ...}}
            and {Origin_code:{Dest_code:pred_price, ...}}

    Generate a dict to be used to in web app that, given an origin airport code as key, 
    the value is a dict where the keys are ranks 1 to n and values are airports such that
    {'JFK': {1: 'LAX'}} would mean that 'LAX' is the best value destination from 'JFK', based
    on the linear fit from fare_dist_fit().  Also return Orig to Dest to Predicted price dict.
    """


    #make JFK->LAX and LAX->JFK separate entries for grouping purposes
    #also require at least 100 entries on a given route for it to be included in rankings
    od_meds_dfcop = od_meds_df.loc[od_meds_df.Count >= 100].copy()
    od_meds_dfcop['apt1'] = od_meds_df['apt2']
    od_meds_dfcop['apt2'] = od_meds_df['apt1']
    od_dub = pd.concat([od_meds_df.loc[od_meds_df.Count >= 100], od_meds_dfcop])
    od_dub.index = range(len(od_dub))
    od_dub['dest_value_rank'] = od_dub.groupby('apt1')['delta_price'].rank(ascending = False)

    rank_to_dest_d = dict()
    dest_to_pred_d = dict()
    for orig, dest, rank, pred in np.array(od_dub[['apt1', 'apt2', 'dest_value_rank', 'pred_price']]):
        if orig in rank_to_dest_d:
            rank_to_dest_d[orig][rank] = dest
        else:
            rank_to_dest_d[orig] = {rank: dest}
        if orig in dest_to_pred_d:
            dest_to_pred_d[orig][dest] = pred
        else:
            dest_to_pred_d[orig] = {dest: pred}
    
    for orig in rank_to_dest_d:
        rank_to_dest_d[orig]['max_rank'] = max(rank_to_dest_d[orig].keys())


    return rank_to_dest_d, dest_to_pred_d



def make_hidden_cities_d(od_df):
    """
    od_df: OrigDest dataframe, with MktFare >= 6.
    Returns: Dict of the form {(Origin_code, Dest_code): [Fake_Dest_code, ...]}

    Aggregate nonstop routes with routes with stops that start with the given 
    nonstop, i.e. LAX->JFK is grouped with LAX->JFK->BOS, LAX->JFK->IAD, etc.
    Then identify the routes with changes that have lower median prices than
    the corresponding nonstop. i.e. if LAX->JFK costs $300 and LAX->JFK->BOS
    costs $250 and LAX->JFK->IAD costs $350 then include the BOS route but not
    the IAD route. 
    """
    od_routings = od_df.groupby(['Origin', 'Dest', 'AirportGroup'])['MktFare'].agg([np.median, len])
    od_routings = od_routings.reset_index()
    
    #require routings to have at least 50 entries to be considered 
    od_routings = od_routings.loc[od_routings.len >= 50]

    route_d = dict()
    for route, fare in np.array(od_routings[['AirportGroup', 'median']]):
        route_l = route.split(':')
        orig = route_l[0]
        
        for dest in route_l[1:]:
            if (orig, dest) in route_d:
                route_d[(orig, dest)][route] = fare
            else:
                route_d[(orig, dest)] = {route:fare}

    nonstop_route_deals = dict()
    for route_tup in route_d:
        nonstop_s = route_tup[0] + ':' + route_tup[1]
        if nonstop_s in route_d[route_tup]:
            nonstop_fare = route_d[route_tup][nonstop_s]
            for subroute in route_d[route_tup]:
                subroute_l = subroute.split(':')
                if route_d[route_tup][subroute] < nonstop_fare and subroute_l[1] == route_tup[1]:
                        if route_tup in nonstop_route_deals:
                            nonstop_route_deals[route_tup][subroute] = route_d[route_tup][subroute]
                        else:
                            nonstop_route_deals[route_tup] = {subroute: route_d[route_tup][subroute]}

    hidden_cities_d = dict()
    for route_tup in nonstop_route_deals:
        hiddens = set()
        for route_s in nonstop_route_deals[route_tup]:
            hiddens.add(route_s.split(':')[-1])
        hidden_cities_d[route_tup] = list(hiddens)

    hidden_cities_paired_d = dict()
    for route_tup in hidden_cities_d:
        if (route_tup[1], route_tup[0]) in hidden_cities_d:
            hidden_cities_paired_d[route_tup] = hidden_cities_d[route_tup]

    return hidden_cities_paired_d



def od_codes_to_airport_name_d(dest_to_pred_d):
    """
    dest_to_pred_d: dict containing origin airport codes
                generated by dests_by_rank_preds_by_dest()

    Returns: dict of airport code to its full name.  Some 
    airports (those with fewer than 10000 passengers per Year)
    are not listed in the wikipedia table.  These are removed.

    #ASSUMES airport_list.html is in current directory.
    #This file was taken from: 
    http://en.wikipedia.org/wiki/List_of_airports_in_the_United_States
    #In March 2014.
    """

    htmdf = pd.read_html('airport_list.html', skiprows=2, infer_types = False)[0] #read_html assumes multiple tables per page

    htmdf.columns = ['city', 'FAA', 'IATA', 'ICAO', 'airport', 'role', 'enplanements']
    htmdf = htmdf.loc[htmdf.airport != '']
    htmdf.index = range(len(htmdf))

    
    def shorten_airports(apt_s):
        if "International" in apt_s:
            return apt_s.split("International")[0]
        elif "Regional" in apt_s:
            return apt_s.split("Regional")[0]
        elif "Airport" in apt_s:
            return apt_s.split("Airport")[0]
        else:
            return apt_s + ' '

    htmdf['apt_v1'] = htmdf['airport'].apply(shorten_airports)

    def rewrite_airports(x):
        if x['city'] in x['apt_v1']: 
            return x['apt_v1']+'('+x['IATA']+')'  
        else:
             return x['apt_v1'].rstrip(' ')+', '+x['city']+' ('+x['IATA']+')'
    
    
    htmdf['apt_info'] = htmdf.apply(rewrite_airports, axis = 1)


    apt_code_city_d = dict()
    for code in dest_to_pred_d:
        city_name = htmdf.loc[htmdf.IATA == code, 'apt_info'].all()
        if type(city_name) is not bool:
            apt_code_city_d[code] = city_name 



    #FIX some airport names by hand:
    apt_code_city_d['AVP'] = 'Wilkes-Barre/Scranton (AVP)'
    apt_code_city_d['AZO'] = 'Kalamazoo/Battle Creek (AZO)'
    apt_code_city_d['BWI'] = 'Baltimore/Washington (BWI)'
    apt_code_city_d['CAK'] = 'Akron/Canton (CAK)'
    apt_code_city_d['CHO'] = 'Charlottesville (CHO)'
    apt_code_city_d['CRP'] = 'Corpus Christi (CRP)'
    apt_code_city_d['CVG'] = 'Cincinnati/Northern Kentucky (CVG)'
    apt_code_city_d['DCA'] = 'Washington National (DCA)'
    apt_code_city_d['DFW'] = 'Dallas/Fort Worth (DFW)'
    apt_code_city_d['DTW'] = 'Detroit Metropolitan Wayne County (DTW)'
    apt_code_city_d['FLL'] = 'Fort Lauderdale (FLL)'
    apt_code_city_d['IAD'] = 'Washington Dulles (IAD)'
    apt_code_city_d['LIH'] = 'Lihue (LIH)'
    apt_code_city_d['LNY'] = 'Lanai City (LNY)'
    apt_code_city_d['PIE'] = 'St. Petersburg/Clearwater (PIE)'
    apt_code_city_d['SJC'] = 'Norman Y. Mineta San Jose (SJC)'
    apt_code_city_d['SJU'] = 'San Juan / Carolina (SJU)'

    return apt_code_city_d

