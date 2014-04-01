from zipflights_data_parsing import *
import pickle as pkl

############ UPDATE FILE NAMES HERE ################
q3_2013 = 'Origin_and_Destination_Survey_DB1BMarket_2013_3/Origin_and_Destination_Survey_DB1BMarket_2013_3.csv'
q2_2013 = 'Origin_and_Destination_Survey_DB1BMarket_2013_2/Origin_and_Destination_Survey_DB1BMarket_2013_2.csv'
q1_2013 = 'Origin_and_Destination_Survey_DB1BMarket_2013_1/Origin_and_Destination_Survey_DB1BMarket_2013_1.csv'
q4_2012 = 'Origin_and_Destination_Survey_DB1BMarket_2012_4/Origin_and_Destination_Survey_DB1BMarket_2012_4.csv'

q3_2013_strip = 'OrigDestSurvey_Stripped_2013q3.csv'
q2_2013_strip = 'OrigDestSurvey_Stripped_2013q2.csv'
q1_2013_strip = 'OrigDestSurvey_Stripped_2013q1.csv'
q4_2012_strip = 'OrigDestSurvey_Stripped_2013q4.csv'

hidden_cities_out_fname = 'OrigDest_HiddenCity_Targets.pkl'
dest_ranks_out_fname = 'OrigDest_ranking_dict.pkl'
price_preds_out_fname = 'OrigDest_price_preds_dict.pkl'
apt_code_to_full_name_out_fname = 'AptCode_FullName_dict.pkl'
####################################################


csvs_in = [q3_2013, q2_2013, q1_2013, q4_2012]
csvs_out = [q3_2013_strip, q2_2013_strip, q1_2013_strip, q4_2012_strip]

for fin, fout in zip(csvs_in, csvs_out):
    survey_load_strip_save(fin, fout)

print "Origin and Dest csvs stripped and written to disk."

stripped_csvs_l = []
for fin in csvs_out:
    stripped_csvs_l.append(pd.read_csv(fin))

print "Stripped files re-read"

od_df = pd.concat(stripped_csvs_l)
od_df.index = range(len(od_df))

print "Data concatenated, num entries: " + str(len(od_df))

alphabetize_airports(od_df)
od_meds = groupby_route_medians(od_df)

print "Grouped by routes for median prices"

hidden_cities_d = make_hidden_cities_d(od_df)
pkl.dump(hidden_cities_d, open(hidden_cities_out_fname, 'wb'))
del hidden_cities_d

print "Wrote hidden cities dict. Finished with big dataframe."

del od_df

fare_dist_fit(od_meds)
rank_to_dest_d, dest_to_pred_d = dests_by_rank_preds_by_dest(od_meds)

pkl.dump(rank_to_dest_d, open(dest_ranks_out_fname, 'wb'))
pkl.dump(dest_to_pred_d, open(price_preds_out_fname, 'wb'))

print "Wrote rankings and price preds dicts."

apt_cities_d = od_codes_to_airport_name_d(dest_to_pred_d)

print "Wrote airport code to full name dict."

pkl.dump(apt_cities_d, open(apt_code_to_full_name_out_fname, 'wb'))




