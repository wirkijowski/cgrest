from os import listdir
import os.path
import web
import json

urls = (
        '/', 'index',
        '/subsystems', 'subsystems',
        '/group/*$', 'group',
        '/group/[\w\.\/]+$', 'group',
        )

render = web.template.render('templates/')

cgpath = '/sys/fs/cgroup'

def get_subsystems(cgpath=cgpath, homedomain='http://localhost'):
    #todo: path validation (remove ../../ etc)
    subsystems = {}
    for name in listdir(cgpath):
        if os.path.isdir(os.path.join(cgpath, name)):
            subsystems[name] = {
                    'uri': os.path.join(homedomain, 'subsystems', name),
                    }
            
    return subsystems

def get_group(current_group='', cgpath=cgpath, homedomain='http://localhost'):
    subsystems = get_subsystems(homedomain=homedomain)

    parent, name = os.path.split(current_group)
    group = {
            'name':         name,
            'parent':       {
                'hierarchy': parent,
                'uri': os.path.join(homedomain, 'group', parent),
                },
            'subsystems':   subsystems, 
            'subgroups':    {},
            'controlfiles': {},
            'tasks':        {},
            }
    # for each subsystem check what hierarhies are connected to it
    # or deeper levels of hierarchies; only one down
    for system in subsystems.keys():
        path = os.path.join(cgpath, system, current_group) 
        for name in listdir(path):
            # subhierarchies are directories
            if os.path.isdir(os.path.join(path, name)):
                # check if hierarchy already added into our structure
                if name in group['subgroups']:
                    templist = group['subgroups'][name]['subsystems'] 
                    templist.append(system)
                    group['subgroups'][name]['subsystems'] = templist
                # if not, add hierarchy and remeber to what system it's
                # attached to
                else:
                    group['subgroups'][name] = {
                            'uri': (os.path.join(homedomain, 'group',
                                current_group, name)) ,
                            'subsystems': [system, ],
                            }
            elif name.startswith((system + '.')):
                values = []
                file = os.path.join(path, name)
                try:
                    with open(file, 'r') as f:
                        for line in f:
                            line = line.rstrip('\n')
                            values.append(line)
                except:
                    pass
                   # values = []
                controlfile = { name: values }
                group['controlfiles'] = dict(group['controlfiles'].items() + controlfile.items() )

            elif name == 'tasks':
                file = os.path.join(path, 'tasks')

                tasks = [] 
                with open(file, 'r') as f:
                    for line in f:
                        line = line.rstrip('\n')
                        tasks.append(line)
                taskdict = { system + '.tasks': tasks }
                group['tasks'] = dict(group['tasks'].items() + taskdict.items() )
    
    return group

class index:
    def GET(self):
        links = [ 'subsystems', 'group' ]
        return render.index(links)

class subsystems:

    def GET(self):
        subsys = get_subsystems(homedomain=web.ctx.homedomain)
        return json.dumps(subsys, indent=4)
     #   return render.subsystems(subsys)

   
class group:
    def GET(self):
        ctxpath = web.ctx.path
        parent = os.path.relpath(web.ctx.path, '/group')
        if parent == '.':
            parent = ''
        group = get_group(parent, homedomain=web.ctx.homedomain)
#        return render.group(group, ctxpath)
        return json.dumps(group, indent=4)

    def POST(self):
        pass

if __name__ == "__main__":
    app = web.application(urls, globals())
    app.run()
