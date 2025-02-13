#!/usr/bin/env python3
import click
from datetime import date, timedelta, datetime

from crawlers.officiele_bekendmakingen import Officiele_Bekendmakingen
from crawlers.kb import KB
from crawlers.pbl import PBL
from crawlers.naturalis import Naturalis
from crawlers.ep import EP
from config import WEBDAV
from utils import logging

class DateParamType(click.ParamType):
    name = 'date'

    def convert(self, value, param, ctx):
        try:
            return datetime.strptime(value, '%Y-%m-%d')
        except ValueError:
            self.fail('%s is not a valid date' % value, param, ctx)

DATETIME_TYPE = DateParamType()

@click.group()
def cli():
    pass

@cli.command()
@click.option('--start-record')
@click.option('--end-record')
def officiele_bekendmakingen(start_record, end_record):
    officiele_bekendmakingen = Officiele_Bekendmakingen(WEBDAV)
    officiele_bekendmakingen.run(start_record, end_record)

@cli.command()
@click.option('--start-page', default='1')
def kb(start_page):
    kb = KB(WEBDAV)
    kb.run(start_page)

@cli.command()
@click.option('--start-page', default='0') # Note: first page has page=0
def pbl(start_page):
    pbl = PBL(WEBDAV)
    pbl.run(start_page)

@cli.command()
@click.option('--resumption-token')
def naturalis(resumption_token):
    naturalis = Naturalis(WEBDAV)
    naturalis.run(resumption_token)

@cli.command()
@click.option('--start-date') # Search this day and backwards in time (format YYYY-mm-dd)
def ep(start_date):
    ep = EP(WEBDAV)
    ep.run(start_date)

if __name__ == '__main__':
    cli()
