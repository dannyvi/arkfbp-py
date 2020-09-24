import importlib
import os

from django.core.management.base import BaseCommand, CommandError

from arkfbp.common.extension.transformer import AddNodeTransformer


class Command(BaseCommand):
    help = "For vscode extension to add a node in flow's main.py"

    def handle(self, **options):
        flow = options.get('flow')
        node_clz = options.get('node')
        node_id = options.get('id')
        next_node_id = options.get('next')
        coord_x = options.get('x')
        coord_y = options.get('y')
        node_clz_alias = options.get('alias')
        try:
            clz = importlib.import_module(f'{flow}.main')
            _ = clz.Main()
        except ModuleNotFoundError:
            raise CommandError('Run failed, Invalid flow.')

        try:
            _ = node_clz.split('.')
            clz_path = '.'.join(_[:-1])
            clz = importlib.import_module(clz_path)
            exec(f'_ = clz.{_[-1]}')
        except ModuleNotFoundError:
            raise CommandError('Run failed, Invalid node.')

        if not node_id:
            raise CommandError('Run failed, Invalid node id.')

        filepath = ''
        _ = flow.split('.')
        _.append('main.py')
        for x in _:
            filepath = os.path.join(filepath, x)

        visitor = AddNodeTransformer(node_clz, node_id, coord_x=float(coord_x), coord_y=float(coord_y),
                                     next_node_id=next_node_id,
                                     clz_as=node_clz_alias)
        visitor.execute(filepath)

    def add_arguments(self, parser):
        parser.add_argument('--flow', type=str, help='Specifies the import path for name of flow.')
        parser.add_argument('--node', type=str, help='Specifies the import path for node.')
        parser.add_argument('--id', type=str, help='Specifies the id for node.')
        parser.add_argument('--next', type=str, help='Specifies the next node id for the node.')
        parser.add_argument('--x', type=str, help='Specifies the coord x for node.')
        parser.add_argument('--y', type=str, help='Specifies the coord y for node.')
        parser.add_argument('--alias', type=str, help='Specifies the alias for node class.')
