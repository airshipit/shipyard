# Action API supported commands

## Supported actions
These actions are currently supported using the [Action API](API.md#ActionAPI)

None at this time.

----
## Actions under development
These actions are under active development

* deploy_site  
Triggers the initial deployment of a site, using the latest committed
configuration documents. Steps:
  1) Concurrency check - to prevent concurrent site modifications by
  conflicting actions/workflows.
  2) Preflight checks - ensures all UCP components are in a responsive state.
  3) Get design version - uses Deckhand to discover the latest committed
  version of design for the site.
  4) Validate design - asks each involved UCP component to validate the design.
  This ensures that the design, which was previously committed is valid at the
  present time.
  5) Drydock build - orchestrates the Drydock component to configure hardware
  and the Kubernetes environment (Drydock -> Promenade)
  6) Check deployed node status - checks that the deployment of nodes is
  successful.
  7) Armada build - orchestrates Armada to configure software on the nodes as
  designed.

* update_site  
Triggers the initial deployment of a site, using the latest committed
configuration documents. Steps: (same as deploy_site)

* redeploy_server  
Using parameters to indicate which server(s), triggers a redeployment of server
to the last known good design and secrets

---
## Future actions
These actions are anticipated for development
* test region  
Invoke site validation testing - perhaps baseline is a invocation of all
components regular "component" tests. This test would be used as a
preflight-style test to ensure all components are in a working state.

* test component  
Invoke a particular platform component to test it. This test would be used to
interrogate a particular platform component to ensure it is in a working state,
and that its own downstream dependencies are also operational
