#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# DBpedia indexer
#
# Copyright (C) 2017 Koninklijke Bibliotheek, National Library of
# the Netherlands
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import os
import requests

VIRTUOSO_URL = 'http://openvirtuoso.kbresearch.nl/sparql?'
DEFAULT_GRAPH_URI = 'http://nl.dbpedia.org'

def get_uris(lang='nl'):
    '''
    Retrieve all relevant resource uris for specified language.
    '''
    if lang == 'nl':
        query = '''
        SELECT DISTINCT ?s WHERE {
            ?s <http://www.w3.org/2000/01/rdf-schema#comment> ?o .
            ?s <http://www.w3.org/2000/01/rdf-schema#label> ?q .
            FILTER(
                REGEX(?s, "^http://nl.dbpedia.org/resource/.{2,}", "i") &&
                !REGEX(?s, "(doorverwijspagina)", "i")
            )
        }
        '''
    else:
        query = '''
        SELECT DISTINCT ?s WHERE {
            ?s <http://www.w3.org/2000/01/rdf-schema#comment> ?o .
            ?s <http://www.w3.org/2000/01/rdf-schema#label> ?r .
            FILTER(
                REGEX(?s, "http://dbpedia.org/resource/.{2,}", "i") &&
                !REGEX(?s, "(disambiguation)", "i")
            )
            MINUS {
                ?t <http://www.w3.org/2002/07/owl#sameAs> ?s .
                ?t <http://www.w3.org/2000/01/rdf-schema#comment> ?q .
                ?t <http://www.w3.org/2000/01/rdf-schema#label> ?u .
                FILTER(
                    REGEX(?t, "^http://nl.dbpedia.org/resource/.{2,}", "i")
                )
            }
        }
        '''
    query = ' '.join(query.split())

    count_query = query.replace('DISTINCT ?s', 'count(DISTINCT ?s) as ?count')
    payload = {'default-graph-uri': DEFAULT_GRAPH_URI, 'format': 'json', 'query': count_query}
    response = requests.get(VIRTUOSO_URL, params=payload)
    count = int(response.json().get('results').get('bindings')[0].get('count').get('value'))
    print('Total number of records found: ' + str(count))

    limit = 1000000
    offset = 0
    while offset < count:
        print('Retrieving batch with offset: ' + str(offset))
        payload['query'] = query + ' LIMIT ' + str(limit) + ' OFFSET ' + str(offset)
        response = requests.get(VIRTUOSO_URL, params=payload)
        save_uris(response.json(), lang)
        offset += limit

def save_uris(record, lang='nl'):
    '''
    Save uris to plain text file, one uri per line.
    '''
    print('Saving batch of length: ' + str(len(record.get('results').get('bindings'))))

    filename = 'uris_' + lang + '.txt'
    mode = 'ab' if os.path.exists(filename) else 'wb'
    with open(filename, mode) as fh:
        for triple in record.get('results').get('bindings'):
            fh.write(triple.get('s').get('value').encode('utf-8') + '\n'.encode('utf-8'))

if __name__ == "__main__":
    get_uris('nl')
    get_uris('en')

