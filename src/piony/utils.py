import dateutil.parser


def parse_date(r):
    return dateutil.parser.parse(r).date()
