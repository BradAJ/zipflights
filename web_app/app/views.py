from flask import render_template, flash, redirect, g, url_for, request
from app import *
from models import *
from form import FlyForm, ITAForm, NonStopForm

##GLOBALS
HIDDEN_PAIRS_D = pkl.load(open('app/static/OrigDest_HiddenCity_Targets.pkl', 'rb'))
DEST_RANK_D = pkl.load(open('app/static/OrigDest_Ranking.pkl', 'rb'))
DEST_PREDS_D = pkl.load(open('app/static/OrigDest_PricePreds.pkl', 'rb'))
APT_CITY_D =  pkl.load(open('app/static/AptCode_FullName.pkl', 'rb'))

#these are calculated in: zipflights_data_parsing.fare_dist_fit()
PRICE_DIST_MEAN = -15.51
PRICE_DIST_STD = 50.84

months_l = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
MONTHS = [(str(i+1), mon) for i, mon in enumerate(months_l) ]

@app.route('/')
@app.route('/index')
def index():    
    return render_template("index.html")


@app.route('/fly', methods = ['GET', 'POST'])
def fly():
    form = FlyForm()
    if form.validate_on_submit():   
        return redirect(url_for('show_dests', origin_entered = form.origin.data.upper()))
    elif form.is_submitted():
        flash('Invalid Input')
    return render_template('fly.html', title = "Where to?", form = form)

@app.route('/fly-nonstop', methods = ['GET', 'POST'])
def nonstops():
    form = NonStopForm()
    form.depart_month.choices = MONTHS
    form.return_month.choices = MONTHS
    if form.validate_on_submit():
        dep_date = datetime.date(form.depart_year.data, int(form.depart_month.data), form.depart_day.data)
        ret_date = datetime.date(form.return_year.data, int(form.return_month.data), form.return_day.data)
        today = datetime.date.today()
        origin_entered = form.origin.data.upper()
        dest_entered = form.destination.data.upper()


        if dep_date >= today and ret_date >= dep_date:
            if origin_entered in APT_CITY_D:
                if dest_entered in APT_CITY_D:

                    dep_date_s = date_obj_to_s(dep_date)

                    ret_date_s = date_obj_to_s(ret_date)
                    return redirect(url_for('nonstop_deals',
                                    origin_entered = form.origin.data.upper(),
                                    dest_entered = form.destination.data.upper(), 
                                    departing = dep_date_s,
                                    returning = ret_date_s))
                else:
                    flash("Sorry! We don't have any info on flights from: " + str(dest_entered))
            else:
                flash("Sorry! We don't have any info on flights from: " + str(origin_entered))
        else:
            flash('Invalid Input')
    elif form.is_submitted():
        flash('Invalid Input')
    return render_template('fly_nonstop.html', title = "Search Non-Stops", form = form)

@app.route('/show_dests', methods = ['GET', 'POST'])
def show_dests():

    origin_entered = request.args.get('origin_entered')
    if origin_entered is None:
        flash("Origin:"+str(origin_entered) )
        return redirect(url_for('fly'))

    if origin_entered in DEST_RANK_D:
        if DEST_RANK_D[origin_entered]['max_rank'] >= 10:
            dests_l = [DEST_RANK_D[origin_entered][float(i)] for i in range(1,11)]
        else:
            rank_max = int(1 + DEST_RANK_D[origin_entered]['max_rank'])
            dests_l = [DEST_RANK_D[origin_entered][float(i)] for i in range(1,rank_max)]
    else:
        flash("Sorry! we don't have any info on flights from: " + str(origin_entered))
        return redirect(url_for('fly'))

    dests_cities = []
    for dest in dests_l:
        if dest in APT_CITY_D and type(APT_CITY_D[dest]) is str:
            dests_cities.append((dest, APT_CITY_D[dest]))
        else:
            dests_cities.append((dest, dest))
    itaform = ITAForm()
    itaform.destination.choices = dests_cities 
    
    itaform.month.choices = MONTHS
    
    if itaform.validate_on_submit():
        
        return redirect(url_for('check_prices',
                               orig = origin_entered,
                               dest = itaform.destination.data, 
                               month = itaform.month.data,
                               duration = itaform.duration.data))
    elif itaform.is_submitted():
        flash('Invalid Input')
    return render_template('show_dests.html',
                             origin_entered = origin_entered,
                             itaform = itaform)


@app.route('/nonstop_deals')
def nonstop_deals():

    origin_entered = request.args.get('origin_entered')
    dest_entered = request.args.get('dest_entered')
    departing = request.args.get('departing')
    returning = request.args.get('returning')

    faa_orig = str(origin_entered)
    faa_dest = str(dest_entered)

    if faa_orig not in APT_CITY_D:
        flash("Sorry! we don't have any info on flights from: " + faa_orig)
        return redirect(url_for('fly-nonstop'))
    elif faa_dest not in APT_CITY_D:
        flash("Sorry! we don't have any info on flights to: " + faa_orig)
        return redirect(url_for('fly-nonstop'))

    response = ita_search(faa_orig, 
                        faa_dest, 
                        departing, 
                        returning, 
                        duration = True, 
                        out_constraints = 'N', 
                        return_constraints = 'N',
                        month_search = False)

    num_results = ita_response_d(response)['result']['solutionCount']
    nonstops_avail = num_results != 0

    if nonstops_avail:
        nonstop_d = ita_response_hidden_parse(response, faa_orig, faa_dest)
        deal_stars = deal_checker(faa_orig, faa_dest, nonstop_d['minprice'])

        if (faa_orig, faa_dest) in HIDDEN_PAIRS_D:
            out_fake_dests = HIDDEN_PAIRS_D[(faa_orig, faa_dest)]
            back_fake_dests = HIDDEN_PAIRS_D[(faa_dest, faa_orig)]
            out_response = ita_search(faa_orig, 
                                        out_fake_dests,
                                        departing,
                                        None,
                                        duration = None,
                                        out_constraints = faa_dest,
                                        month_search = False)

            back_response = ita_search(faa_dest, 
                                        back_fake_dests,
                                        returning,
                                        None,
                                        duration = None,
                                        out_constraints = faa_orig,
                                        month_search = False)

            out_num_results = ita_response_d(out_response)['result']['solutionCount']
            back_num_results = ita_response_d(back_response)['result']['solutionCount']
        
            hiddens_avail = True
            if out_num_results != 0:
                out_flights_d = ita_response_hidden_parse(out_response, faa_orig, faa_dest)
            else:
                hiddens_avail = False
            if back_num_results != 0:
                back_flights_d = ita_response_hidden_parse(back_response, faa_orig, faa_dest)
            else:
                hiddens_avail = False
        else:
            hiddens_avail = False

        if hiddens_avail:
            hiddens_help = nonstop_d['minprice'] > (out_flights_d['minprice'] + back_flights_d['minprice'])
            total_hidden = str(out_flights_d['minprice'] + back_flights_d['minprice'])
        else:
            hiddens_help = False
    else:
        deal_stars = False #No non-stops available, so can't evaluate deal
        route_price = None
        airlines = None
        hiddens_avail = False
        total_hidden = 'Too Much'


    return render_template('nonstop_deals.html', **locals())
    
@app.route('/check_prices')
def check_prices():

    faa_orig = request.args.get('orig')
    faa_dest = request.args.get('dest')
    month = int(request.args.get('month'))
    duration = int(request.args.get('duration'))

    today = datetime.date.today()
    if today.month < month:
        year = today.year
        day_start = 1
    elif today.month == month:
        year = today.year
        day_start = today.day
    else:
        year = today.year + 1
        day_start = 1

    day_end = calendar.monthrange(year, month)[1]

    start_date = str(year) + '-' + str(month) + '-' + str(day_start)
    end_date = str(year) + '-' + str(month) + '-' + str(day_end)

    response = ita_search(faa_orig, faa_dest, start_date, end_date, duration)
    route_price, airlines = ita_response_airline_parse(response)

    deal_stars = deal_checker(faa_orig, faa_dest, route_price)

    return render_template('check_prices.html', **locals())



def deal_checker(orig, dest, route_price):
    pred_price = DEST_PREDS_D[orig][dest]
    
    if type(route_price) is not float and type(route_price) is not int:
        avail_price = float(route_price.strip('USD'))
    else:
        avail_price = route_price

    delta_price = (2 * pred_price) - avail_price
    stars_int = int(stars_from_price(delta_price, PRICE_DIST_MEAN, PRICE_DIST_STD))
    return str(stars_int) + (' Stars' if stars_int > 1 else ' Star')




