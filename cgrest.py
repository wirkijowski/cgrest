from os import listdir
import os.path
import web

urls = (
        '/', 'index',
        '/subsystems', 'subsystems',
        '/groups', 'groups',
        '/groups/[\w\.\/]+$', 'groups',
        )

render = web.template.render('templates/')

cgpath = '/sys/fs/cgroup'

def get_subsystems(cgpath=cgpath):
    #todo: path validation (remove ../../ etc)

    return ([ name for name in listdir(cgpath) if
        os.path.isdir(os.path.join(cgpath, name)) ])

def get_groups(parent_group='', cgpath=cgpath):
    subsystems = get_subsystems()

    groups = {
            'controllers': []
            }
    # for each subsystem check what hierarhies are connected to it
    # or deeper levels of hierarchies; only one down
    for system in subsystems:
        path = os.path.join(cgpath, system, parent_group) 
        for name in listdir(path):
            # subhierarchies are directories
            if os.path.isdir(os.path.join(path, name)):
                # check if hierarchy already added into our structure
                if name in groups:
                    templist = groups[name]
                    templist.append(system)
                    groups[name] = templist
                # if not, add hierarchy and remeber to what system it's
                # attached to
                else:
                    groups[name] = [system, ]
            elif name.startswith((system + '.')):
                values = []
                file = os.path.join(path, name)
                try:
                    with open(file, 'r') as f:
                        for line in f:
                            line = line.rstrip('\n')
                            values.append(line)
                except:
                    values = []

                groups['controllers'].append([name, values])
            elif name == 'tasks':
                file = os.path.join(path, 'tasks')

                tasks = [] 
                with open(file, 'r') as f:
                    for line in f:
                        line = line.rstrip('\n')
                        tasks.append(line)

                groups[system + '.tasks'] = tasks 
    
    return groups

class index:
    def GET(self):
        links = [ 'subsystems', 'groups' ]
        return render.index(links)

class subsystems:

    def GET(self):
        subsys = get_subsystems()
        return render.subsystems(subsys)

class groups:
    def GET(self):
        ctxpath = web.ctx.path
        parent = os.path.relpath(web.ctx.path, '/groups')
        if parent == '.':
            parent = ''
        groups = get_groups(parent)
        return render.groups(groups, ctxpath)

if __name__ == "__main__":
    app = web.application(urls, globals())
    app.run()
