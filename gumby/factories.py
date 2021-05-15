import datetime
import random
import uuid

from elasticsearch import Elasticsearch

from .models import (
    Encounter,
    GeoPoint,
    Individual,
    Sex,
)

SEXES = [x for x in Sex] + [None]
SUBMITTERS = ['julia', 'alice', 'henry', 'josh', 'fen', 'margo', 'kady', 'penny', 'eliot', 'quentin']
ALIASES = ['destiny', 'amanda', 'brook', 'alex', 'zoe', 'naomi', 'rick']
BINOMIAL_NOMENCLATURES = {
    # <genus>: [<species>, ...]
    'balaenoptera': ['acutorostrata', 'borealis', 'brydei', 'edeni', 'musculus', 'physalus'],
}


def random_date_delta():
    # Somewhere between one day and 2 years
    return datetime.timedelta(days=random.randint(1, 365 * 2))


def random_scientific_name_parts():
    genus = random.choice(list(BINOMIAL_NOMENCLATURES))
    species = random.choice(BINOMIAL_NOMENCLATURES[genus])
    return genus, species


def make_individual(**kwargs):
    """Produce a random individual documents with encounters"""
    genus, species = random_scientific_name_parts()
    props = {
        'id': uuid.uuid4(),
        'name': f'TI-{random.randint(0,99999):05}',
        'alias': random.choice(ALIASES),
        'genus': genus,
        'species': species,
        # 'last_sighting': datetime.datetime.now() - random_date_delta(),
        'sex': random.choice(SEXES),
        'encounter': [],
    }

    # ??? I'm just not sure we need to index the lastest-sighting separately.
    #     This may be redundant since we have the value in in the nested encounters.
    #     An aggregate in the query would probably work to provide this bit of data.
    # Determine the last_sighting value
    encounters = kwargs.get('encounter', [])
    try:
        latest_encounter = sorted(encounters, key=lambda x: x.date_occurred, reverse=True)[0]
    except IndexError:
        last_sighting = None
    else:
        last_sighting = latest_encounter.date_occurred
    finally:
        props['last_sighting'] = last_sighting

    return Individual(**(props | kwargs))


def make_encounter(**kwargs):
    random_central_geo_point = GeoPoint(
        lat=random.randint(-90 * 10**6, 90 * 10**6) * 10**-6,
        lon=random.randint(-180 * 10**6, 180 * 10**6) * 10**-6,
    )
    props = {
        'id': uuid.uuid4(),
        'point': GeoPoint(
            # TODO scatter slightly away from the central point
            lat=random_central_geo_point.lat,
            lon=random_central_geo_point.lon,
        ),
        'animate_status': None,
        'sex': random.choice(SEXES),
        'submitter_id': random.choice(SUBMITTERS),
        'date_occurred': datetime.datetime.now() - random_date_delta(),
    }

    return Encounter(**(props | kwargs))


def load_individuals_index_with_random_data():
    """Load the individuals index with data"""
    es = Elasticsearch()
    idx = 'individuals'

    for i in range(0, 50):
        encounters = [make_encounter() for i in range(0, random.randint(1, 20))]
        indv = make_individual(encounter=encounters)
        res = es.index(index=idx, body=indv.dict())
