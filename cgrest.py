from os import listdir
from functools import wraps
import os.path
import web
import json

urls = (
        '/', 'index',
        '/subsystems/*$', 'subsystems',
        '/subsystems/[\w\.\/]+$', 'subsystems',
        '/group/*$', 'group',
        '/group/[\w\.\/]+$', 'group',
        )

render = web.template.render('templates/')

cgpath = '/sys/fs/cgroup'

def get_path_contents(cgpath=cgpath, subpath=''):

    path = os.path.join(cgpath, subpath)
    content = {
               'subgroups':    {},
               'controlfiles': {},
               'tasks':        {},
               }

    for name in listdir(path):
        # directories mean subgroups
        if os.path.isdir(os.path.join(path, name)):
            content['subgroups'][name] = {}
        elif name == 'tasks':
           file = os.path.join(path, 'tasks')
           tasks = [] 
           with open(file, 'r') as f:
               for line in f:
                   line = line.rstrip('\n')
                   tasks.append(line)
           content['tasks'] = tasks
        elif name != 'tasks' and os.path.isfile(os.path.join(path, name)): 
           values = []
           file = os.path.join(path, name)
           try:
               with open(file, 'r') as f:
                   for line in f:
                       line = line.rstrip('\n')
                       values.append(line)
           except:
               pass
               #values = []
           content['controlfiles'].update({ name: values })

    return content


def get_subsystems(root_hierarchy='', cgpath=cgpath, homedomain='http://localhost'):
    #todo: path validation (remove ../../ etc)
    subsystems = {
            'subsystems': {}
            }

    urlmap = 'subsystems'
    if root_hierarchy == '':
            
        for name in listdir(cgpath):
            if os.path.isdir(os.path.join(cgpath, name)):
                subsystems['subsystems'].update( {
                            name: {
                                'uri': os.path.join(homedomain, urlmap, name),
                                }
                        })
    else:
        subsystems = get_path_contents(os.path.join(cgpath, root_hierarchy))
        for name in subsystems['subgroups'].keys():
            subsystems['subgroups'][name] = {
                    'uri': os.path.join(homedomain, urlmap, root_hierarchy, name),
                    }
                            
    return subsystems


def get_group(current_group='', cgpath=cgpath, homedomain='http://localhost'):
    subsystems = get_subsystems(homedomain=homedomain)
    urlmap = 'group'
    
    #add basic attributes to group resource          
    parent, name = os.path.split(current_group)
    
    group = {
            'name': name,
            'parent':    {
                'hierarchy': parent,
                'uri': os.path.join(homedomain, urlmap, parent),
            },
            'subsystems': subsystems['subsystems'],
            'subgroups': {},
            'controlfiles': {},
            'tasks': {},
        }

    for system in subsystems['subsystems'].keys():
        newgroup = get_path_contents(cgpath, os.path.join(system, current_group))
        # add uri for every subgroup
        for name in newgroup['subgroups'].keys():
            newgroup['subgroups'][name] = { 
                    'uri':  (os.path.join(homedomain, urlmap,
                       current_group, name)) ,
                    }
        # create key for current subsystem's tasks
        group['tasks'].update({ system + '.tasks': newgroup.pop('tasks') })
        group['controlfiles'].update(newgroup['controlfiles'])
        group['subgroups'].update(newgroup['subgroups'])
    
    return group


def contentdecorator(func):
    @wraps(func)
    def getdata(*args, **kwargs):
        template = web.template.frender('templates/' +
            args[0].__class__.__name__ + '.html')

        if web.ctx.env.get('HTTP_ACCEPT') == 'application/json':
            web.header('Content-Type', 'application/json')
            return json.dumps(func(*args, **kwargs), indent=4)
        else:
            web.header('Content-Type', 'text/html')
            return template(func(*args, **kwargs)) 

    return getdata


class index:

    @contentdecorator
    def GET(self):
        content = { 
                'subsystems': {
                    'uri': os.path.join(web.ctx.homedomain, 'subsystems')
                    },
                'group': {
                    'uri': os.path.join(web.ctx.homedomain, 'group')
                    }
                }
        
        return content

class subsystems:
    
    @contentdecorator
    def GET(self):
        ctxpath = web.ctx.path
        parent = os.path.relpath(web.ctx.path, '/subsystems')
        if parent == '.':
            parent = ''

        subsystems = get_subsystems(parent, homedomain=web.ctx.homedomain)
        
        return subsystems

class group:

    @contentdecorator 
    def GET(self):
        ctxpath = web.ctx.path
        parent = os.path.relpath(web.ctx.path, '/group')
        if parent == '.':
            parent = ''
        group = get_group(parent, homedomain=web.ctx.homedomain)
        
        return group           

    def POST(self):
        pass

if __name__ == "__main__":
    app = web.application(urls, globals())
    app.run()
