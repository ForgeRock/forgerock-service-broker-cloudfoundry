import bottle
import requests
import json
import os
import logging
import re
import sys
import ConfigParser
#import settings

#The contents of this file are subject to the terms of the 
#Common Development and Distribution License (the License). 
#You may not use this file except in compliance with the License.
#You can obtain a copy of the License at: 
#https://opensource.org/licenses/CDDL-1.0. 
#See the License for specific language governing permission and 
#limitations under the License.
#
#
#Copyright 2016 ForgeRock, Inc. All Rights Reserved.

# Read config from protected .ini file
config = ConfigParser.SafeConfigParser()
config.read('config.ini')

testmode = config.get('Section1', 'test_mode')

#running in Cloud Foundry?
if 'VCAP_APPLICATION' in os.environ:
    vcap_application = json.loads(os.environ['VCAP_APPLICATION'])
    if (vcap_application.get('application_id',0) and vcap_application.get('application_name',0)):
        ##yes running in CF
        logging.basicConfig(stream=sys.stdout,level=logging.DEBUG,format='%(asctime)s %(message)s')      
else:
    #no, running locally
    current_file = re.split("\.",os.path.basename(__file__))
    logging.basicConfig(filename=(current_file[0] + '.log'),level=logging.DEBUG,format='%(asctime)s %(message)s')

logging.info('Started')

#keep track of instance id's and bind id's
#To do this right, an external data store should be used
#Alpha code :)
#Explore storing this in openDJ
instanceid_2_bindid = {}
bindid_2_clientid = {}

#headers
http_content_type_json = {'Content-Type':'application/json'}

openam_oidc_dynamic_register_data = {'redirect_uris':'[https:/foo.com/register]'}

#URI to dynamically register OIDC client
openam_oidc_dynamic_register_URI = 'openam/oauth2/connect/register'

#Forgerock endpoints
openam_URL = config.get('Section1', 'openam_url')

@bottle.error(401)
@bottle.error(409)
def error(error):
    bottle.response.content_type = 'application/json'
    return '{"error": "%s"}' % error.body

def authenticate(username, password):
    #Future enhancement - Authenticate against openam
    return True
#
#
# Catalog
#
#
@bottle.route('/v2/catalog', method='GET')
@bottle.auth_basic(authenticate)
def catalog():
    """

    """
    catalog_dict = {'services': \
                [{'id': 'fr-broker', \
                'name': 'fr-openam',
                'description': 'Forgerock OpenAM Identity APIs', \
                'bindable': True, \
                'plans': \
                [{'id': 'openam-oidc', \
                'name': 'oidc', \
                'description': 'Dynamically Register an OIDC client upon bind'}] \
                }] \
                }

    return json.dumps(catalog_dict)

#
#
#Provision
#
#
@bottle.route('/v2/service_instances/<instance_id>', method='PUT')
@bottle.auth_basic(authenticate)
def provision(instance_id):
    """
       For 1.0 Forgerock Service Broker, provision will be a No Op as
       it is assumed that OpenAM is already provisioned and available at
       openam_URL above.
    """

    theresponse = [{"dashboard_url":"http://" + openam_URL}]

    #Incoming request does not have the proper content type
    if bottle.request.content_type != 'application/json':
        bottle.abort(415, 'Unsupported Content-Type: expecting application/json')
        logging.debug('request aborted: Content-Type must be application/json')

    #Must have instance id
    if instance_id != None:
        #instance_id must not exist
        if instance_id in instanceid_2_bindid:
            bottle.response.status = 200
            logging.debug('Failure duplicate instance_id= |%s|',instance_id)
            logging.debug('Failure inst2client= |%s|',instanceid_2_bindid[instance_id])
            return dict(data=theresponse)

        instanceid_2_bindid[instance_id] = "NOTBOUND"
        logging.debug('Success instance_id= |%s|',instance_id)
        logging.debug('Success inst2client= |%s|',instanceid_2_bindid[instance_id])
        # return created status code
        bottle.response.status = 201 
        return dict(data=theresponse)
    else:
        bottle.abort(400, 'Must have instance_id')
        logging.debug('request aborted: instance_id= |%s|',instance_id)

#
#
# DeProvision
#
#
@bottle.route('/v2/service_instances/<instance_id>', method='DELETE')
@bottle.auth_basic(authenticate)
def deprovision(instance_id):
    """

    """
    # deprovision the service
    #instance_id must exist
    if instance_id in instanceid_2_bindid:
        del instanceid_2_bindid[instance_id]
        bottle.response.status = 200
    else:
        bottle.response.status = 410

    # send response
    return {}
#
#
#######Bind
#
#
@bottle.route('/v2/service_instances/<instance_id>/service_bindings/<binding_id>', method='PUT')
@bottle.auth_basic(authenticate)
def bind(instance_id, binding_id):
    """

    """

    credentials = {'credentials': { \
        'uri': openam_URL, \
        'username': 'empty', \
        'password': 'empty', \
      }}

    error_response = {'error':'unspecified'}
    
    #setup openam URL for oidc registration
    if testmode == 0:
        url = openam_URL
    else:
        url = openam_URL + openam_oidc_dynamic_register_URI

    logging.debug('url set to %s',url)
    logging.debug('oidc-uri = %s', openam_oidc_dynamic_register_URI)
    headers = http_content_type_json

    #Check content type
    if bottle.request.content_type != 'application/json':
        bottle.abort(415, 'Unsupported Content-Type: expecting application/json')
        logging.debug('request aborted: Content-Type must be application/json')

    #Instance ID must exist and be unbound
    if instance_id in instanceid_2_bindid:
        #It exists
        if instanceid_2_bindid[instance_id] == binding_id:
            #It is already bound
            bottle.response.status = 409
            logging.debug('Failure instance_id|binding_id combination already exists %s|%s|%s|%s',instance_id, binding_id, instanceid_2_bindid[instance_id],bindid_2_clientid[binding_id])
            error_response['error'] = ('binding_id already exists:', binding_id)
            return dict(data=error_response)
        elif instanceid_2_bindid[instance_id] != 'NOTBOUND':
            #It is already bound - but to some other binding_id.  This is bad.
            bottle.response.status = 409
            logging.debug('Failure instance_id is already bound to another binding_id %s|%s|%s',instance_id, binding_id, instanceid_2_bindid[instance_id])
            error_response['error'] = ('instance_idalready bound to another binding_id:', binding_id)
            return dict(data=error_response)
    else:
        bottle.response.status = 409
        logging.debug('Failure instance_id must exist %s|%s',instance_id, binding_id)
        error_response['error'] = ('instance_id must exist:', instance_id)
        return dict(data=error_response)

    #Everything is ok, let's POST to openam to register client
    #
    try:
        openam_response = requests.post(url, json={"redirect_uris":["https:/foo.com/register"]}, headers=headers,timeout=(10.0,10.0))
        openam_response.raise_for_status()
    except requests.exceptions.ConnectionError as e:
        bottle.response.status = 500
        error_response['error'] = str(e.args[0])
        logging.debug('Connection Error:  %s ',str(e.args))
        logging.debug('Connection error to %s',url)
        return dict(data=error_response)
    except requests.exceptions.ConnectTimeout as e:
        error_response['error'] = 'Connection Timeout to ' + setting.am_URL
        logging.debug('Error: Connection Timeout to %s',url)
        logging.debug('Error: result.statuscode = %s',openam_response.status_code)
        return dict(data=error_response)
    except requests.exceptions.HTTPError as e:
        bottle.response.status = openam_response.status_code
        error_response['error'] = e.args[0]
        logging.debug('HTTP Error:  %s ',e.args[0])
        return dict(data=error_response)


    

    #Request Failed
    if openam_response.status_code != 201:
        logging.debug('request Failed')
        logging.debug('request url=%s',url)
        logging.debug('request headers=%s',headers)
        logging.debug('request failed statsuscode=%s',openam_response.status_code)
        error_response['error'] = 'oidc registration failed. am error =  ' + str(openam_response.status_code)
        return dict(data=error_response)

    #Request Succeeded
    if openam_response.status_code == 201:
        result_dict = openam_response.json()
        bottle.response.status = openam_response.status_code
        logging.debug('Success status code = 201')
        logging.debug('instance_id=%s',instance_id)
        logging.debug('registration_access_token =%s',result_dict['registration_access_token'])
        logging.debug('json result =%s',openam_response.json())

        #load credentials
        credentials['credentials']['username'] = result_dict['client_id']
        credentials['credentials']['password'] = result_dict['client_secret']

        #
        instanceid_2_bindid[instance_id] = binding_id
        bindid_2_clientid[binding_id] = result_dict['client_id']
        logging.debug('updating dicts %s|%s', instanceid_2_bindid[instance_id],bindid_2_clientid[binding_id])
              
        return json.dumps(credentials)

    """
    
    """
##
#
# Unbind
#
#
@bottle.route('/v2/service_instances/<instance_id>/service_bindings/<binding_id>', method='DELETE')
@bottle.auth_basic(authenticate)
def unbind(instance_id, binding_id):
    """
    """
    # unbind the service
    #instance_id must exist
    if instance_id in instanceid_2_bindid:
        #binding_id must exist
        if instanceid_2_bindid[instance_id] == binding_id:
            instanceid_2_bindid[instance_id] = 'NOTBOUND'
            del bindid_2_clientid[binding_id]
            bottle.response.status = 200
        else:
            bottle.response.status = 410
    else:
        bottle.response.status = 410
    
    # send response
    return {}

if __name__ == '__main__':
    port = int(os.getenv('PORT', '8080'))
    bottle.run(host='0.0.0.0', port=port, debug=True, reloader=False)