# Action API supported commands

## Supported actions
These actions are currently supported using the [Action API](API.md#ActionAPI)

None at this time.

----
## Actions under development
These actions are under active development

* deploy site  
Triggers the initial deployment of a site, using the staged design and secrets

* update site  
Triggers the an update to an existing site, using the staged design and secrets for the site  

* redeploy server  
Using parameters to indicate which server(s), triggers a redeployment of server to the last known good design and secrets

---
## Future actions
These actions are anticipated for development
* test region  
Invoke site validation testing - perhaps baseline is a invocation of all components regular "component" tests. This test would be used as a preflight-style test to ensure all components are in a working state.

* test component  
Invoke a particular platform component to test it. This test would be used to interrogate a particular platform component to ensure it is in a working state, and that its own downstream dependencies are also operational

* validate design  
Use parameters to test a design. Parameters may support both quick tests to ensure basic format and a complete design, or a more in-depth test that interfaces with particular platform components to ensure a good design