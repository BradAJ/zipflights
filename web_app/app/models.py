from app import *

def ita_search(faa_orig, faa_dest, start_date, end_date, duration = None, out_constraints = None, return_constraints = None, month_search = True):
    """
    faa_orig, faa_dest: FAA airport code strs e.g. 'SFO'
    start_date, end_date: datetime objs e.g. datetime.date.today(), datetime.date(2015, 2, 28)
        NOTE: start_date is used as departure date if NOT month_search, similarly for end_date
    duration: int number of nights at destination e.g. 7. If None => One-way flight, SET duration = True for specificDate roundtrips!
    out/return_constraints: ITA flags e.g. 'N' for nonstops, 'ORD' to transfer there, or 'UA+' for 1 or more United flights.
    """
    

    search_url = 'http://matrix.itasoftware.com/xhr/shop/search'
    
    payload_d = {"pax":{"adults":1},"cabin":"COACH","changeOfAirport":False,"checkAvailability":True,"firstDayOfWeek":"SUNDAY"}
    trip_slice = {"originPreferCity":False,"destinationPreferCity":False, "isArrivalDate":False}
    
    def apt_code_parser(codes_in):
        return [codes_in] if type(codes_in) is not list else codes_in
    
    outbound_d = trip_slice.copy()
    outbound_d['origins'] = apt_code_parser(faa_orig)
    outbound_d['destinations'] = apt_code_parser(faa_dest)
    if out_constraints is not None:
        outbound_d['routeLanguage'] = out_constraints
    
    if month_search:
        search_type = 'calendar&summarizers=itineraryCarrierList%2Ccalendar'
        payload_d['startDate'] = start_date
        payload_d['endDate'] = end_date
        payload_d['layover'] = {"max":duration, "min":duration}
    else:
        search_type = 'specificDates&summarizers=solutionList%2CitineraryCarrierList%2CitineraryOrigins%2CitineraryDestinations'
        outbound_d['date'] = start_date
        outbound_d['dateModifier'] = {"minus":0, "plus":0}


    if duration is not None:    
        return_d = trip_slice.copy()
        return_d['origins'] = apt_code_parser(faa_dest)
        return_d['destinations'] = apt_code_parser(faa_orig)
        if return_constraints is not None:
            return_d['routeLanguage'] = return_constraints
        if not month_search:
            return_d['date'] = end_date
            return_d['dateModifier'] = {"minus":0, "plus":0}
        payload_d['slices'] = [outbound_d, return_d]
        
        
    else:
        payload_d['slices'] = [outbound_d]
    


    payload = urllib.quote_plus(json.dumps(payload_d))
    
    url_start_search = 'http://matrix.itasoftware.com/xhr/shop/search?name='
    return requests.post(url_start_search + search_type + '&format=JSON&inputs=' + payload)

def ita_response_airline_parse(response):

    airline_fares = ita_response_d(response)['result']['itineraryCarrierList']['groups']
    

    airlines = []
    for fare in airline_fares:
        if 'minPriceInSummary' in fare:
            route_price = fare['minPrice']
            airlines.append(fare['label']['shortName'])
    return route_price, airlines

def ita_response_hidden_parse(response, faa_orig, faa_dest):
    resp_d = ita_response_d(response)

    flights_d = dict()
    minprice = float(resp_d['result']['solutionList']['minPrice'].strip('USD'))
    flights_d['minprice'] = minprice
    for itin in resp_d['result']['solutionList']['solutions']:
        flightprice = float(itin['displayTotal'].strip('USD'))
        if flightprice <= (minprice + 1.0): #fixes sensitivity to cents.
            for slic in itin['itinerary']['slices']:
                flight = slic['flights'][0] #only interested in first flight here!
                if flight not in flights_d: 
                    result_d = dict()
                    result_d['carrier'] = itin['itinerary']['ext']['dominantCarrier']['shortName']
                    result_d['departing'] = slic['departure']
                    result_d['fake_dest'] = slic['destination']['code']
                    result_d['true_orig'] = slic['origin']['code']
                    if 'stops' in slic:
                        result_d['stops'] = slic['stops'][0]['code'] #Looking for non-stops only!
                    flights_d[flight] = result_d
    flights_d['out_flights'] = set()
    flights_d['back_flights'] = set()
    flights_d['carriers'] = set()
    for key in flights_d:
        if type(flights_d[key]) is dict and 'true_orig' in flights_d[key]:
            if faa_orig == flights_d[key]['true_orig']:
                flights_d['out_flights'].add(key)
                flights_d['carriers'].add(flights_d[key]['carrier'])
            elif faa_dest == flights_d[key]['true_orig']:
                flights_d['back_flights'].add(key)
                flights_d['carriers'].add(flights_d[key]['carrier'])
    flights_d['out_flights'] = sorted(list(flights_d['out_flights'])) if len(flights_d['out_flights']) != 0 else None
    flights_d['back_flights'] = sorted(list(flights_d['back_flights'])) if len(flights_d['back_flights']) != 0 else None
    
    return flights_d


def ita_response_d(response):
    return json.loads(response.content[4:])

def date_obj_to_s(date_obj):
    y = str(date_obj.year)
    m = '0' + str(date_obj.month) if date_obj.month < 10 else str(date_obj.month)
    d = '0' + str(date_obj.day) if date_obj.day < 10 else str(date_obj.day)
    return y + '-' + m + '-' + d

