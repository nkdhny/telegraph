from django.core.management.base import BaseCommand
from parso import parse
from crawler.models import ChannelMessage
import csv
import json


class Command(BaseCommand):
    def add_arguments(self, parser) -> None:
        parser.add_argument('--format', choices=['csv', 'json-fragment'])
        parser.add_argument('--output-file')

    def _to_csv(self, m: ChannelMessage):
        if self._writer is None:
            self._writer = csv.DictWriter(self._out_file, ['id', 'text'])
        self._writer.writerow(dict(id=m.tg_id, text=m.text))

    def _to_json(self, m: ChannelMessage):
        row = json.dumps(dict(id=m.tg_id, text=m.text))
        self._out_file.write(f'{row}\n')

    def handle(self, *args, **options):
        with open(options['output_file'], 'w') as self._out_file:
            format = None
            if options['format'] == 'csv':
                format = self._to_csv
                self._writer = None
            else:
                assert options['format'] == 'json-fragment'
                format = self._to_json

            for m in ChannelMessage.objects.all():
                format(m)
