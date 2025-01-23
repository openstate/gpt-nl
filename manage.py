#!/usr/bin/env python3

import click
from datetime import date, timedelta, datetime

from crawlers.officiele_bekendmakingen import Officiele_Bekendmakingen
from config import WEBDAV


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
@click.option('--start_date', type=DATETIME_TYPE)
@click.option('--end_date', type=DATETIME_TYPE)
def officiele_bekendmakingen(start_date, end_date):
    officiele_bekendmakingen = Officiele_Bekendmakingen(WEBDAV)
    #officiele_bekendmakingen.run(start_date, end_date)
    officiele_bekendmakingen.run()

if __name__ == '__main__':
    cli()
