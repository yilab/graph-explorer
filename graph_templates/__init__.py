#!/usr/bin/env python2
import re
"""
Graph template
"""


class GraphTemplate:
    # color in light resp. dark version
    # better would be just a "base" and programatically compute lighter/darker versions as needed
    colors = {
        'blue': ('#5C9DFF', '#375E99'),
        'yellow': ('#FFFFB2', '#FFFF00'),
        'green': ('#80CC80', '#009900'),
        'brown': ('#694C2E', '#A59482'),
        'red': ('#FF5C33', '#B24024'),
        'purple': ('#FF94FF', '#995999'),
        'turq': ('#75ACAC', '#197575'),
        'orange': ('#FFC266', '#FF9900'),
        'white': '#FFFFFF',
        'black': '#000000'
    }

    """
    Class for graph templates
    set 2 variables:
    * targets. first match wins
    * pattern_graph: similar, but usually more specific to make sure you only yield 1 graph per "thing that you're graphing"
    """

    def __init__(self):
        for (id, config) in self.target_types.items():
            # because sometimes a target_type covers multiple metric naming
            # patterns, we must support a list of possible matching regexes.
            # we can't just do '|'.join(list of regexes)
            # because then we can't repeat group names.
            # first match wins
            if isinstance(config['match'], basestring):
                config['match'] = [config['match']]
            self.target_types[id]['match_object'] = []
            for regex in config['match']:
                # can raise sre_constants.error ! and maybe other regex errors.
                self.target_types[id]['match_object'].append(re.compile(regex))

    def get_target_id(self, target):
        target_key = ['targets']
        for tag_key in sorted(target['tags'].iterkeys()):  # including the tag key allows to filter out all http things by just writing 'http'
            tag_val = target['tags'][tag_key]
            if tag_val:
                target_key.append('%s:%s' % (tag_key, tag_val))
        return ' '.join(target_key)

    def generate_targets(self, target_type, match):
        """
        emit one or more targets in a dict like {'targetname': <target spec>}
        this implementation just sets target to the metric (match.string),
        and sets all appropriate tags.  if you override this function,
        you should probably still set these tags cause they are relied on.
        depending on target_type you can use different graphite functions
        in your target.
        """
        tags = match.groupdict()
        tags.update({'target_type': target_type, 'template': self.classname_to_tag()})
        target = {
            'target': match.string,
            'tags': tags
        }
        target = self.configure_target(target)
        return {self.get_target_id(target): target}

    def configure_target(self, target):
        return target

    def generate_graphs(self):
        """
        emit one or more graphs in a dict like {'graphname': <graph dict>}
        """
        return {}

    def list_targets(self, metrics):
        """
        For given list of metrics, list all possible targets according to our pattern
        The return value is as follows: {
            'id (targetstring)' : {
                'targetstring': '<..>',
                'names': { for each tag : a name }, # will be shown in legend. if group_by server, servername will be in title, no need to repeat it here
                'default_group_by': '<default group_by tag>'
            }
        }
        """
        targets = {}
        for metric in metrics:
            for (id, config) in self.target_types.items():
                for match_object in config['match_object']:
                    match = match_object.search(metric)
                    if match is not None:
                        targets.update(self.generate_targets(id, match))
                        continue
        return targets

    def list_graphs(self, metrics):
        """
        For given list of metrics, list all possible graphs according to our pattern
        The return value is as follows: {
            'graph-id' : <graph dict, to be merged in with defaults>
        }
        """
        graphs = {}
        for metric in metrics:
            match = self.pattern_object_graph.search(metric)
            if match is not None:
                graphs.update(self.generate_graphs(match))
        return graphs

    def classname_to_tag(self):
        '''
        FooBarHTTPTemplate -> foo_bar_http
        from http://stackoverflow.com/questions/1175208/elegant-python-function-to-convert-camelcase-to-camel-case/1176023#1176023
        '''
        name = self.__class__.__name__.replace('Template', '')
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

# vim: ts=4 et sw=4:
