import os
from os import path
import shutil
from pbr import extra_files

from django.core.management import CommandError
from django.core.management.utils import handle_extensions
from django.core.management.templates import TemplateCommand
from django.template import Context, Engine

import arkfbp


class Command(TemplateCommand):
    help = (
        "Creates a Arkfbp Node for the given node name"
    )
    missing_args_message = "You must provide an node name."
    app_name = 'nodes'
    app_or_project = 'app'

    def handle(self, **options):
        node_name = options.pop('name')
        target = options.pop('directory')
        options.update(template=f'file://{arkfbp.__path__[0]}/common/django/conf/node_template')

        if target is None:
            top_dir = os.getcwd()
            try:
                os.makedirs(top_dir)
            except FileExistsError:
                pass
            except OSError as e:
                raise CommandError(e)
        else:
            top_dir = os.path.abspath(path.expanduser(target))
            if not os.path.exists(top_dir):
                raise CommandError("Destination directory '%s' does not "
                                   "exist, please create it first." % top_dir)
        extensions = tuple(handle_extensions(options['extensions']))

        base_name = 'app_name'
        base_subdir = 'app_template'
        base_directory = 'app_directory'
        camel_case_name = 'camel_case_node_name'
        camel_case_value = ''.join(x for x in node_name.title() if x != '_')

        context = Context({
            **options,
            base_name: self.app_name,
            base_directory: top_dir,
            camel_case_name: camel_case_value,
        }, autoescape=False)
        template_dir = self.handle_template(options['template'], base_subdir)
        prefix_length = len(template_dir) + 1

        for root, dirs, files in os.walk(template_dir):
            path_rest = root[prefix_length:]
            relative_dir = path_rest.replace(base_name, self.app_name)
            if relative_dir:
                target_dir = path.join(top_dir, relative_dir)
                if not path.exists(target_dir):
                    os.mkdir(target_dir)

            for filename in files:
                old_path = path.join(root, filename)
                if filename == 'node.py-tpl':
                    new_path = f'{path.join(top_dir, relative_dir, node_name.replace(base_name, self.app_name))}.py-tpl'
                else:
                    new_path = path.join(top_dir, relative_dir, filename.replace(base_name, self.app_name))
                for old_suffix, new_suffix in self.rewrite_template_suffixes:
                    if new_path.endswith(old_suffix):
                        new_path = new_path[:-len(old_suffix)] + new_suffix
                        break  # Only rewrite once

                if path.exists(new_path):
                    raise CommandError("%s already exists, overlaying a "
                                       "project or app into an existing "
                                       "directory won't replace conflicting "
                                       "files" % new_path)
                if new_path.endswith(extensions) or filename in extra_files:
                    with open(old_path, 'r', encoding='utf-8') as template_file:
                        content = template_file.read()
                    template = Engine().from_string(content)
                    content = template.render(context)
                    with open(new_path, 'w', encoding='utf-8') as new_file:
                        new_file.write(content)
                else:
                    shutil.copyfile(old_path, new_path)
                try:
                    shutil.copymode(old_path, new_path)
                    self.make_writeable(new_path)
                except OSError:
                    self.stderr.write(
                        "Notice: Couldn't set permission bits on %s. You're "
                        "probably using an uncommon filesystem setup. No "
                        "problem." % new_path, self.style.NOTICE)
