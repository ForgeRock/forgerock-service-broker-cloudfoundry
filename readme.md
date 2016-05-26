## The Cloud Foundry Service Broker for the Forgerock Identity Platform

This project enables Cloud Foundry administrators to provide application developers with the ability to bind to an existing Forgerock OpenAM installation and participate in Oauth 2 flows.

Specifically, the broker allows the creation of an [OAuth 2.0 Client Credentials Grant Process](https://backstage.forgerock.com/#!/docs/openam/13/admin-guide/chap-oauth2#figure-oauth2-client-cred)  

See installation and use instructions below.

### About OpenAM
OpenAM is an "all-in-one" access management solution that provides the following features in a single unified project:

+ Authentication
    - Adaptive 
    - Strong  
+ Single sign-on (SSO)
+ Authorization
+ Entitlements
+ Federation 
+ Web Services Security

OpenAM provides mobile support out of the box, with full OAuth 2.0 and OpenID Connect support - modern protocols that 
provide the most efficient method for developing secure native or HTML5 mobile applications optimized for bandwidth and 
CPU.

The project is led by ForgeRock who integrate the OpenAM, OpenIDM, OpenDJ, OpenICF, and OpenIG open source projects to 
provide a quality-assured Identity Platform. Support, professional services, and training are available for the Identity
 Platform, providing stability and safety for the management of your digital identities. 

To find out more about the services ForgeRock provides, visit [www.forgerock.com][commercial_site].

To view the OpenAM project page, which also contains all of the documentation, visit
 [https://forgerock.org/openam/][project_page]. 

For a great place to start, take a look at [Getting Started With OpenAM][getting_started_guide]

For further help and discussion, visit the [community forums][community_forum].

###Getting the Code  

The central project repository lives on the ForgeRock Bitbucket Server at 
[https://stash.forgerock.org/projects/CLOUD/repos/forgerock-service-broker-cloudfoundry](https://stash.forgerock.org/projects/CLOUD/repos/forgerock-service-broker-cloudfoundry).

Mirrors exist elsewhere (for example GitHub) but all contributions to the project are managed by using pull requests to the central repository.

There are two ways to get the code - if you want to run the code unmodified you can simply clone the central repo (or a reputable mirror):

`git clone https://stash.forgerock.org/scm/cloud/forgerock-service-broker-cloudfoundry.git`

If, however, you are considering contributing bug fixes, enhancements, or modifying the code you should fork the project
 and then clone your private fork, as described below:


1. Create an account on [BackStage](https://backstage.forgerock.com) - You can use these credentials to create pull requests, report bugs, and
download the enterprise release builds.
1. Log in to the Bitbucket Server using your BackStage account credentials.
1. Fork the `forgerock-service-broker-cloudfoundry` project. This will create a fork for you in your own area of Bitbucket Server. Click on your 
profile icon then select 'view profile' to see all your forks.
1. Clone your fork to your machine.  


Obtaining the code this way will allow you to create pull requests later.  


##How to use the broker

###Configuring OpenAM  

   These instructions are for openam 13.0
   
   You will need to configure **Open Dynamic Client Registration**  
   
   
   1. Login to the openam console as an administrator
   1. Select the "Realm" you wish to configure
   1. Select "Services" from the list of options on the left hand side
   1. Select "Oauth 2 Provider" from the list of services
   1. Enable "Allow Open Dynamic Client Registration:" by selecting the checkbox
   1. Enable "Generate Registration Access Tokens:" by selecting the checkbox
   1. Click save
   

####Installing the broker 
  
   To fully test the broker, you need to have an app to bind to the broker.  There is a companion test app [here] (https://github.com/ForgeRock/forgerock-service-broker-testapp). The test app will be used in the instructions below.  
   
   More information on Managing Service Brokers [here](http://docs.cloudfoundry.org/services/managing-service-brokers.html)

1. **Push the broker**  
After cloning the repo, edit the config.ini file. Use the URL of the openam you configured above.

   `openam_url: http://your.openam.url.here/`  

   Make sure you login to the CF CLI.  Then, from the project directory, push the broker as a CF app.  
    
   `cf push myfrbroker`  
    
 You can use any unique name in your Cloud Foundry instance.  List the apps to see your running broker.  
  
 `cf apps`  

  In the above apps listing, take note of the URL of your broker.  You will need it in the next step.  

1. **Create the broker** 

  To this point, you just have another cf app.  It is up and running and has implemented the service broker API, but the Cloud Controller does not know it exists as a service broker.  
  
 `cf create-service-broker name-of-service-broker username password http://myfrbroker.your.app.url/
`  

 **name-of-service-broker** - This is the name you want to use for the service broker (not the app).  When you list service brokers, this is the name you will see.  Again, must be unique in your instance of CF.  

  **username** - The Cloud Controller will use this username to authenticate to the broker.  You can change it later if you need to.  
  
 **password** - The Cloud Controller will use this password to authenticate to the broker.  

 **App URL** - This is the URL of the app you pushed above.  Again you kind find it at anytime by running "cf apps".   

 **Note:** At this time, the broker will accept **any** username/password pair. This will be enhanced in the future to authenticate against openam.

 **list brokers**  
`cf service-brokers`  

 Your service broker should now show up on this list

 **Show services in broker and status:**  
`cf service-access`   

 The service(s), plan(s) and access will be listed. Take note of the service name and plan. At this point, the access column lists _private_ instead of _all_.  A provision or bind request will fail as a result.

 **Show the broker in the marketplace**  
 `cf marketplace`  

1. **Enable service within the broker:**  
enabling the broker will allow access for provision and bind calls (and all other broker API calls)

 `cf enable-service-access fr-openam`  

 another `cf service-access` will show access enabled for _all_

1. **Create instance of the service**
`cf create-service fr-openam oidc yet-another-name`

 "yet-another-name" is now listed  
 
 `cf services`

1. **Bind to an app (Finally!)**  

  Clone the test app from here: [https://github.com/ForgeRock/forgerock-service-broker-testapp](https://github.com/ForgeRock/forgerock-service-broker-testapp).   
Then from the test app project directory:  
`cf push frtestapp`

  Bind the test app to the service instance created above
`cf bind-service frtestapp yet-another-name` 

  Check the VCAP_SERVICES environment variables to confirm the binding  
   
  
 `cf env frtestapp`  

 You should see username, password and URI variables.

####Test the oauth 2 flow

   You can use the following curl commands to test the flow.  
   
   Get an oauth token from openam using credentials of a valid oauth client:  
   
   `curl --user username:password -v --data-urlencode "grant_type=client_credentials" http://your.openam.url:8080/openam/oauth2/access_token`  
   
   This will return a JSON payload that will include the access_token
   
   Call the test app API
   `curl -H "Authorization: Bearer access_token_from_above" http://your.testapp.url/oauthinfo`
   
   The test app will use the credentials from VCAP_SERVICES to call openam and validate the token.


#### Licensing

The contents of this file are subject to the terms of the Common Development and Distribution License (the License). You may not use this file except in compliance with the License.
 
You can obtain a copy of the License at:  [https://opensource.org/licenses/CDDL-1.0](https://opensource.org/licenses/CDDL-1.0).  See the License for specific language governing permission and limitations under the License.

 
### Disclaimer
This is an alpha release of unsupported code made available by ForgeRock for community development subject to the license contained in the software. The code is provided on an "as is" basis, without warranty of any kind, to the fullest extent permitted by law. ForgeRock does not warrant or guarantee the individual success developers may have in implementing the code on their development platforms or in production configurations.

ForgeRock does not warrant, guarantee or make any representations regarding the use, results of use, accuracy, timeliness or completeness of any data or information relating to the alpha release of unsupported code. ForgeRock disclaims all warranties, expressed or implied, and in particular, disclaims all warranties of merchantability, and warranties related to the code, or any service or software related thereto.

ForgeRock shall not be liable for any direct, indirect or consequential damages or costs of any type arising out of any action taken by you or others related to the code.

Copyright © 2016 ForgeRock, Inc. All Rights Reserved. 


## All the Links

- [Cloud Foundary Service Broker Spec][service_broker_spec]  
- [Getting Started with OpenAM guide][getting_started_guide]
- [ForgeRock's commercial website][commercial_site]
- [ForgeRock's community website][community_site]
- [ForgeRock's BackStage server][backstage] 
- [OpenAM Project Page][project_page]
- [Community Forums][community_forum]
- [Enterprise Build Downloads][enterprise_builds]
- [Enterprise Documentation][enterprise_docs]
- [Nightly Build Downloads][nightly_builds]
- [Nightly Documentation][nightly_docs]
- [Central Project Repository][central_repo]
- [Issue Tracking][issue_tracking]
- [Contributors][contributors]
- [Coding Standards][coding_standards]
- [Contributions][contribute]
- [How to Buy][how_to_buy]


[commercial_site]: https://www.forgerock.com
[community_site]: https://www.forgerock.org
[backstage]: https://backstage.forgerock.com
[project_page]: https://forgerock.org/openam/
[community_forum]: https://forgerock.org/forum/fr-projects/openam/
[enterprise_builds]: https://backstage.forgerock.com/#!/downloads/OpenAM/OpenAM%20Enterprise#browse
[enterprise_docs]: https://backstage.forgerock.com/#!/docs/openam
[nightly_builds]: https://forgerock.org/downloads/openam-builds/
[nightly_docs]: https://forgerock.org/documentation/openam/
[central_repo]: https://stash.forgerock.org/projects/OPENAM
[issue_tracking]: http://bugster.forgerock.org/
[docs_project]: https://stash.forgerock.org/projects/OPENAM/repos/openam-docs/browse
[contributors]: https://stash.forgerock.org/plugins/servlet/graphs?graph=contributors&projectKey=OPENAM&repoSlug=openam&refId=all-branches&type=c&group=weeks
[coding_standards]: https://wikis.forgerock.org/confluence/display/devcom/Coding+Style+and+Guidelines
[how_to_buy]: https://www.forgerock.com/platform/how-buy/
[contribute]: https://forgerock.org/projects/contribute/
[service_broker_spec]:http://docs.cloudfoundry.org/services/api.html#api-overview  
[getting_started_guide]:https://forgerock.org/openam/doc/bootstrap/getting-started/index.html