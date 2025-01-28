#!/usr/bin/env python3
import click
from datetime import date, timedelta, datetime

from crawlers.officiele_bekendmakingen import Officiele_Bekendmakingen
from crawlers.kb import KB
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
@click.option('--start_date', type=DATETIME_TYPE)
@click.option('--end_date', type=DATETIME_TYPE)
def kb(start_date, end_date):
    kb = KB(WEBDAV)
    #kb.run(start_date, end_date)
    kb.run()

if __name__ == '__main__':
    cli()
