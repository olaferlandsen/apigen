#!/usr/bin/python
# encoding=utf8
import os, urllib2, sys, re, urlparse
from urlparse import urlparse, parse_qsl
from markdown import Markdown
from optparse import OptionParser
import plueprint
"""
"""
parser = OptionParser()
parser.add_option("-f", "--file", dest="filename", help="The input file path; example: apigen -i sample.md", metavar="FILE")
#parser.add_option("-u", "--update", dest="update", help="Update apigen if it exists", metavar="UPDATE")
parser.add_option("-i", "--interface", dest="interface", help="Write interfaces: using typedocs", metavar="INTERFACE", default=False, action="store_true")
parser.add_option("-a", "--annotations", dest="annotations", help="Write annotations: using typedocs", metavar="ANNOTATIONS", default=False, action="store_true")
#parser.add_option("-p", "--params", dest="params", help="Declare params", metavar="PARAMS")
parser.add_option("-v", "--version", dest="version", help="Show version information", metavar="VERSION", default=False, action="store_true")
parser.add_option("-o", "--output", dest="output", help="output", metavar="OUTPUT", default="src/providers")
parser.add_option("-c", "--camel", dest="camel", help="Force camelcase methods name on classes", metavar="CAMEL", default=False, action="store_true")
"""
"""
(options, args) = parser.parse_args()

options.output = re.sub('\/+', '/', options.output + '/')

"""
"""
reload(sys)
sys.setdefaultencoding('utf8')
"""
"""
VERSION  = '1.0.394 Beta'
NAME     = 'Reciario'
API_HOST = ''
"""
"""
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
"""
"""
class console(object):
    @staticmethod
    def log     (message):
        message = re.sub('(\*\*(.+?)\*\*)', bcolors.BOLD+ '\g<2>' + bcolors.ENDC + bcolors.OKGREEN, message)
        message = re.sub('(\_\_(.+?)\_\_)', bcolors.UNDERLINE+ '\g<2>' + bcolors.ENDC + bcolors.OKGREEN, message)
        print bcolors.OKGREEN  + bcolors.ENDC + bcolors.OKGREEN + message + bcolors.ENDC
    @staticmethod
    def error   (message):
        message = re.sub('(\*\*(.+?)\*\*)', bcolors.BOLD+ '\g<2>' + bcolors.ENDC + bcolors.WARNING, message)
        message = re.sub('(\_\_(.+?)\_\_)', bcolors.UNDERLINE+ '\g<2>' + bcolors.ENDC + bcolors.WARNING, message)
        print bcolors.WARNING  + u'\u26A0 ' + bcolors.ENDC + bcolors.WARNING + message + bcolors.ENDC
    @staticmethod
    def fatal   (message):
        message = re.sub('(\*\*(.+?)\*\*)', bcolors.BOLD+ '\g<2>' + bcolors.ENDC + bcolors.FAIL, message)
        message = re.sub('(\_\_(.+?)\_\_)', bcolors.UNDERLINE+ '\g<2>' + bcolors.ENDC + bcolors.FAIL, message)
        print bcolors.FAIL  + u'\u00D7 ' + bcolors.ENDC + bcolors.FAIL + message + bcolors.ENDC
        sys.exit()
    @staticmethod
    def info    (message):
        message = re.sub('(\*\*(.+?)\*\*)', bcolors.BOLD+ '\g<2>' + bcolors.ENDC + bcolors.OKBLUE, message)
        message = re.sub('(\_\_(.+?)\_\_)', bcolors.UNDERLINE+ '\g<2>' + bcolors.ENDC + bcolors.OKBLUE, message)
        print bcolors.OKGREEN  + u'\u2713 ' +bcolors.ENDC + bcolors.OKBLUE + message + bcolors.ENDC
"""
"""
class BluePrintApiObject(object):
    @staticmethod
    def parse (bluePrintString):
        m = Markdown(extensions=["plueprint"])
        m.set_output_format("apiblueprint")
        api = m.convert(bluePrintString)
        global API_HOST
        API_HOST = api.host
        _api = {
            'server': api.host,
            'groups': {}
        }
        for item in api.actions:
            group = re.sub(r'(\?[\w\d\W\S\b]+)', '', item.uri)
            group = re.sub(r'([^/]+)(/.+)', '\g<1>', group)
            group = re.sub(r'/', '', group)
            group = re.sub(r'[^A-Za-z0-9_]+', '_', group)
            group = group.lower()
            if not group in _api['groups']:
                _api['groups'][group] = {
                    'path'      :   '',
                    'methods'   :   {}
                }
                console.info('API **'+group+'** detected')
            preparedName = re.sub(r'[^A-Za-z0-9_]+', ' ', item.id).title()
            preparedName = re.sub('\s+', ' ', preparedName)
            if options.camel is True:
                name = re.sub('\s+', '', preparedName)
                name = name[0].lower() + name[1:]
            else:
                name = re.sub(r'[^A-Za-z0-9_]+', '_', item.id)
                name = name.lower()
            ##
            method = item.request_method.lower()
            if method not in ['post', 'put', 'get', 'head', 'connect', 'patch', 'delete']:
                method = 'get'
            _api['groups'][group]['methods'][name] = {
                'method'        : method,
                'uri'           : item.uri_template.uri,
                'params'        : [],
                'contentType'   : '',
                'responseType'  : '',
                'options'       :   {
                    'headers'       :   {},
                    'cookies'       :   None
                },
                'interface': {}
            }
            console.info('\tFunction **'+group+'.'+ name + '()** has been detected')
            _params = re.findall('(\{(?P<name>[A-Za-z0-9_]+)\})', item.uri_template.uri)
            if _params is not None and len(_params) > 0:
                for _param in _params:
                    _api['groups'][group]['methods'][name]['params'].append({
                        'name'  :   _param[1],
                        'type'  :   'any',
                        'in'    :   'path'
                    })

            _params = parse_qsl(urlparse(item.uri_template.uri)[4], keep_blank_values= True)
            if _params is not None and len(_params) > 0:
                for (_key, _param) in _params:
                    _api['groups'][group]['methods'][name]['params'].append({
                        'name'  :   _key + '?',
                        'type'  :   'any',
                        'in'    :   'query'
                    })

            # posibble expected response
            try:
                _key = 201 if 201 in item.responses else 200
                if _key in item.responses:
                    interfaceName = preparedName
                    interfaceName = re.sub('[_\s]+', ' ', interfaceName)
                    interfaceName = interfaceName.title()
                    interfaceName = re.sub('\s+' , '', interfaceName)
                    _api['groups'][group]['methods'][name]['interface'] = {
                        'name': 'ResponseInterface' + interfaceName,
                        'data': item.responses[200][0].value()
                    }
            except ValueError, e:
                console.error("I can't parse a posibble interface from json response")

            ##
            #print "Requests:"
            if item.requests is not None and len(item.requests) > 0:
                for key in item.requests.keys():
                    if item.requests.get(key).media_type is not None:
                        _api['groups'][group]['methods'][name]['options']['headers']['content-type'] = item.requests.get(key).media_type[0] + '/' + item.requests.get(key).media_type[1];
                        _api['groups'][group]['methods'][name]['contentType'] = item.requests.get(key).media_type[0] + '/' + item.requests.get(key).media_type[1];
                    headers = item.requests.get(key).headers;
                    if item.requests.get(key).headers is not None:
                        for header in item.requests.get(key).headers:
                            _api['groups'][group]['methods'][name]['options']['headers'][header[0]] = header[1];
        ########
        return _api
"""
"""
GIST_APIGEN = 'https://gist.githubusercontent.com/olaferlandsen/44dd8f6e6be1878a2a4798973c72e68f/raw/apigen.ts'
"""
"""
TABS = '    '
"""
"""
class Utils(object):
    @staticmethod
    def listJoin(glue, _list):
        clean = ''
        index = 0
        for value in _list:
            if isinstance(value, (list, tuple)):
                _list[index] = Utils.listJoin(glue, value)
            index += 1
        return glue.join(_list)

    @staticmethod
    def is_string (value):
        return isinstance(value, str)
    """
    """
    @staticmethod
    def is_list(value):
        return isinstance(value, list)
    """
    """
    @staticmethod
    def is_int(value):
        return isinstance(value, (int, long))
    """
    """
    @staticmethod
    def is_float (value):
        return isinstance(value, float)
    """
    """
    @staticmethod
    def file_exists (paths):
        if Utils.is_list(paths):
            for path in paths:
                if Utils.is_string(path) and not Utils.file_exists(path):
                    return False
            return True
        else:
            return os.path.exists(paths)
    """
    """
    @staticmethod
    def is_file(path):
        return os.path.isfile(path)
    """
    """
    @staticmethod
    def is_dir(path):
        return os.path.isdir(path)
    """
    """
    @staticmethod
    def is_readable(path):
        return os.access(path, os.R_OK)
    """
    """
    @staticmethod
    def chunk_report(bytes_so_far, chunk_size, total_size):
        percent = float(bytes_so_far) / total_size
        percent = round(percent * 100, 2)
        sys.stdout.write("Downloaded %d of %d bytes (%0.2f%%)\r" % (bytes_so_far, total_size, percent))
        if bytes_so_far >= total_size:
            sys.stdout.write('\n')
    """
    """
    @staticmethod
    def chunk_read(response, chunk_size=8192, report_hook=None):
        total_size = response.info().getheader('Content-Length').strip()
        total_size = int(total_size)
        bytes_so_far = 0
        while 1:
            chunk = response.read(chunk_size)
            bytes_so_far += len(chunk)
            if not chunk:
                break
            if report_hook:
                report_hook(bytes_so_far, chunk_size, total_size)
        return bytes_so_far
"""
"""
class Apigen (object):
    """
    
    """
    def recursiveInterfaceDefinition (self, interface, tabs = '    ', start = False) :
        _interface = []
        ###
        if start is True:
            _interface.append('{')
        ###
        if isinstance(interface, dict):
            for key in interface:
                value = interface[key]
                type = self.getType(value)
                if type.lower() == 'object':
                    _interface.append(tabs + "'" + key  +"'" +  ': {' )
                    _interface.append(tabs + Utils.listJoin( tabs + '\n' + tabs, self.recursiveInterfaceDefinition(value, tabs='    ')))
                    _interface.append(tabs + '}')
                else:
                    _interface.append(tabs + "'" +key + "'" + ':' + type + ';')
        ###
        if start is True:
            _interface.append('}\n')
        return _interface
    """
    """
    def getType (self, value) :
        if isinstance(value, bool) or value is True or value is False:
            return 'boolean'
        elif isinstance(value, (basestring, str, unicode)):
            return 'string'
        elif isinstance(value, dict):
            return 'Object'
        elif isinstance(value, (int, long, float)):
            return 'number'
        elif isinstance(value, (list, tuple)):
            return 'Array<any>'
        elif value is None:
            return 'string|number|null'
        else:
            return 'any'
    """
    """
    def createClass(self, filename, className, methods, path):
        console.info('Creating ' + filename + '.ts')
        with open('src/providers/' + filename + '.ts', 'w+') as file:
            file.write('import {Injectable} from "@angular/core"\n')
            file.write('import {Apigen, ApigenInterface, ApigenResponseInterface} from "./apigen"\n')

            if options.interface is True:
                for method, structure in methods.iteritems():
                    if len(structure['interface']) > 0:
                        file.write('/**\n')
                        file.write(' *\n')
                        file.write(' * @interface\n')
                        file.write(' */\n')
                        file.write('export interface ' + (structure['interface']['name']) + ' {\n')
                        buffer = self.recursiveInterfaceDefinition(structure['interface']['data'], start=True)
                        file.write("\n".join(buffer))
            if options.annotations is True:
                file.write('/**\n')
                file.write(' *\n')
                file.write(' * @constructor\n')
                file.write(' */\n')
            file.write('@Injectable()\n')
            file.write('export class ' + className + ' extends Apigen implements ApigenInterface\n')
            file.write('{\n')

            if path is not None and len(path) > 0:
                if options.annotations is True:
                    file.write(TABS + '/**\n')
                    file.write(TABS + ' *\n')
                    file.write(TABS + ' * @property {string} path\n')
                    file.write(TABS + ' */\n')
                file.write(TABS + 'public path:string = "'+ path +'";\n')

            for method, structure in methods.iteritems():
                __response = 'Promise<ApigenResponseInterface>'
                if options.interface is True and len(structure['interface']) > 0:
                    __response = 'Promise<' + structure['interface']['name'] + '>'
                if options.annotations is True:
                    file.write(TABS + '/**\n')
                    file.write(TABS + ' *\n')
                    if structure['params'] is not None and len(structure['params']) > 0:
                        for item in structure['params']:
                            file.write(TABS+' * @param ')
                            file.write('{' + item['type'] + '} ')
                            file.write(re.sub('\?', '', item['name']))
                            if re.search('\?', item['name']):
                                file.write(' - Optional')
                            file.write("\n")
                    file.write(TABS + ' * @return {' + __response + '}\n')
                    file.write(TABS+' */\n')

                file.write(TABS+'public ' + method)
                file.write('(')
                if structure['params'] is not None and len(structure['params']) > 0:
                    index = 0
                    for item in structure['params']:
                        index+=1
                        file.write(item['name'] + ':' + item['type'])
                        if index <= len(structure['params']) - 1:
                            file.write(', ')
                file.write( '):'+__response+'\n')
                file.write(TABS +'{\n')
                file.write(TABS + TABS +'return this.xhr' + structure['method'].title() + '(')
                if structure['uri'] is not None and len(structure['uri']) > 0:
                    uri = structure['uri']
                    for param in structure['params']:
                        if param['in'] == 'path':
                            uri = re.sub(r'\{' + re.escape(param['name']) + '\}', "' + "+param['name']+" + '", uri)
                    file.write("'" + uri + "'")
                file.write(')\n')
                file.write(TABS +'}\n')
            file.write('}\n')
            file.close()
    """
    """
    def downloadApigen (self):
        with open('src/providers/apigen.ts', 'w+') as file:
            response = urllib2.urlopen(GIST_APIGEN)
            file.write(response.read())
            file.close()
            return True
        return False
    """
    """
    def isCordova(self):
        return Utils.file_exists (['www','src'])
    """
    """
    def isApigen(self):
        return Utils.file_exists('src/providers/apigen.ts')
    """
    """
    def process (self, bluePrintObject):
        if not self.isApigen():
            console.error('Apigen no existe, lo descargaremos...')
            if self.downloadApigen():
                console.log('Apigen descargado correctamente');
        for name, group in bluePrintObject['groups'].iteritems():
            filename = re.sub('[^A-Za-z0-9]+', '-', name) + '-apigen'
            className = re.sub('[^A-Za-z0-9]+', '', re.sub('[^A-Za-z0-9]+', ' ', name).title()) + 'Apigen'
            self.createClass(filename, className, group['methods'], group['path'])
    """
    """
"""
"""

if options.version is True:
    console.info(VERSION + " **(" + NAME + ")**")
    console.info("read more in **https://github.com/olaferlandsen/apigen**")
    sys.exit()
elif options.filename is not None:
    if Utils.file_exists(options.filename):
        if not Utils.is_readable(options.filename):
            console.fatal("Input file is not redeable")
        elif not Utils.file_exists(options.output):
            console.error("Output path does not exists.")
            console.info("I will create the output directory")
            os.makedirs(options.output)
        if not Utils.file_exists(options.output + 'apigen.ts'):
            console.error("apigen.ts file does not exists.")
            console.info("I will download and store it on output directory")
            with open( options.output + 'apigen.ts', 'w+') as file:
                response = urllib2.urlopen(GIST_APIGEN)
                content = response.read()
                file.write(content)
                file.close()
        console.info("Parsing file...")
        response = open(sys.argv[2])
        apiary = BluePrintApiObject.parse(response.read())
        apigen = Apigen()
        apigen.process(apiary)
        fileader = open(options.output + 'apigen.ts', 'r').read()
        with open(options.output + 'apigen.ts', 'w+') as file:
            fileader = re.sub("public\s+server\:string\s+?\=\s+?'(.*?)'", "public server:string = '" + API_HOST + "'", fileader)
            file.write(fileader)
            file.close()
        console.info("End...")
    else:
        console.error("Input file does not exists")
else:
    console.fatal("Sorry, i don't know what are you doing...")
sys.exit()