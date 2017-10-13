# Supported Environment Variables

All commands will utilize the following environment variables to determine
necessary information for execution, unless otherwise noted.

<dl>
  <dt>Openstack Keystone Authorization Environment variables</dt>
  <dd>
    The Shipyard CLI/API Client will check for the presence of appropriate
    environment setup to do authentication on behalf of the user.
    The openrc variables that will be used are as follows:<br />
    OS_PROJECT_DOMAIN_NAME<br />
    OS_USER_DOMAIN_NAME<br />
    OS_PROJECT_NAME<br />
    OS_USERNAME<br />
    OS_PASSWORD<br />
    OS_AUTH_URL<br />
    OS_IDENTITY_API_VERSION<br />
  </dd>
</dl>

# Shipyard command options
The base shipyard command supports options that determine cross-CLI behaviors.
These options are positionally immediately following the shipyard command as
shown here:
```
shipyard <--these options> subcommands...

shipyard
  [--context-marker=<uuid>]
  [--os_{various}=<value>]
  [--debug/--no-debug]
  <subcommands, as noted in this document>
```
<dl>
  <dt>--context-marker=&lt;uuid&gt;</dt>
  <dd>
    Specifies a UUID (8-4-4-4-12 format) that will be used to correlate logs,
    transactions, etc... in downstream activities triggered by this
    interaction. If not specified, Shipyard will supply a new UUID to serve
    as this marker. (optional)
  </dd>
  <dt>--os_{various}=&lt;value&gt;</dt>
  <dd>
    See supported Openstack Keystone Authorization Environment variables above
    for the list of supported names, converting to a downcase version of the
    environment variable.<br />
    E.g.: --os_auth_url=http://...:80/v3
    While these options are optional, if not specified, the environment
    variables will be used instead. The Keystone os_auth_url should reference
    the exposed keystone:port for the target Shipyard environment, as this
    Keystone will be used to discover the instance of Shipyard.
  </dd>
</dl>

## Context Marker


# Commit Commands
## commit configdocs
Attempts to commit the Shipyard Buffer documents, first invoking validation
by downstream components.
```
shipyard commit configdocs
    [--force]

Example:
    shipyard commit configdocs
```
<dl>
  <dt>--force</dt>
  <dd>
    Force the commit to occur, even if validations fail.
  </dd>
</dl>

# Control commands
## pause, unpause, stop
Three separate commands with a common format that allow for controlling
the processing of actions created in Shipyard.
<dl>
  <dt>pause</dt>
  <dd>pause something in progress e.g. an executing action</dd>
  <dt>unpause</dt>
  <dd>unpause something paused e.g. a paused action</dd>
  <dt>stop</dt>
  <dd>stops an executing or paused item e.g. an action</dd>
</dl>

```
shipyard pause
    <type>
    <id>

shipyard unpause
    <type>
    <id>

shipyard stop
    <type>
    <id>

shipyard
    pause|unpause|stop
    <qualified name>

Example:

    shipyard pause action 01BTG32JW87G0YKA1K29TKNAFX

    shipyard unpause action 01BTG32JW87G0YKA1K29TKNAFX

    shipyard stop action 01BTG32JW87G0YKA1K29TKNAFX

    shipyard pause action/01BTG32JW87G0YKA1K29TKNAFX
```
<dl>
  <dt>&lt;type&gt;</dt>
  <dd>
    The type of entity to take action upon.  Currently supports: action
  </dd>
  <dt>&lt;id&gt;</dt>
  <dd>
    The id of the entity to take action upon.
  </dd>
    <dt>&lt;qualified name&gt;</dt>
  <dd>
    The qualified name of the item to take the specified action upon
  </dd>

</dl>

# Create Commands
## create action
Invokes the specified workflow through Shipyard.
See [Action Commands](API_action_commands.md) for supported actions
Returns the id of the action invoked so that it can be queried subsequently.
```
shipyard create action
    <action command>
    --param=<parameter>    (repeatable)

Example:
    shipyard create action redeploy_server --param="server-name=mcp"
```
<dl>
  <dt>&lt;action command&gt;</dt>
  <dd>
    The action to invoke.
    See [Action Commands](API_action_commands.md) for supported actions
  </dd>
  <dt>--param=&lt;parameter&gt;</dt>
  <dd>
    A parameter to be provided to the action being invoked. (repeatable)
  </dd>
</dl>

## create configdocs
Load documents into the Shipyard Buffer. The use of one or more filename or
a single directory option must be specified.

```
shipyard create configdocs
    <collection>
    [--append | --replace]
    --filename=<filename>    (repeatable)
        |
     --directory=<directory>

Example:
    shipyard create configdocs design --append --filename=site_design.yaml
```
Note: If neither append or replace are specified, the Shipyard API default
value of rejectoncontents will be used.

Note: Either --filename or --directory must be specified, but both may not be
specified for the same invocation of shipyard.
<dl>
  <dt>&lt;collection&gt;</dt>
  <dd>
    The collection to load.
  </dd>
  <dt>--append</dt>
  <dd>
    Add the collection to the Shipyard Buffer. This will fail if the
    collection already exists.
  </dd>
  <dt>--replace</dt>
  <dd>
    Clear the shipyard buffer and replace it with the specified contents.
  </dd>
  <dt>--filename=&lt;filename&gt;</dt>
  <dd>
    The file name to use as the contents of the collection. (repeatable)
    If any documents specified fail basic validation, all of the documents
    will be rejected.  Use of filename parameters may not be used in
    conjunction with the directory parameter.
  </dd>
  <dt>--directory=&lt;directory&gt;</dt>
  <dd>
    A directory containing documents that will be joined and loaded as a
    collection. Any documents that fail basic validation will reject the
    whole set. Use of the directory parameter may not be used with the filename
    parameter.
  </dd>
</dl>

# Describe Commands
## describe
Retrieves the detailed information about the supplied namespaced item
```
shipyard describe
    <namespaced item>

Example:
    shipyard describe action/01BTG32JW87G0YKA1K29TKNAFX
      Equivalent to:
        shipyard describe action/01BTG32JW87G0YKA1K29TKNAFX

    shipyard describe step/01BTG32JW87G0YKA1K29TKNAFX/preflight
      Equivalent to:
    shipyard describe step preflight --action=01BTG32JW87G0YKA1K29TKNAFX

    shipyard describe validation/01BTG32JW87G0YKA1K29TKNAFX/01BTG3PKBS15KCKFZ56XXXBGF2
      Equivalent to:
    shipyard describe validation 01BTG3PKBS15KCKFZ56XXXBGF2 \
        --action=01BTG32JW87G0YKA1K29TKNAFX
```

## describe action
Retrieves the detailed information about the supplied action id.
```
shipyard describe action
    <action id>

Example:
    shipyard describe action 01BTG32JW87G0YKA1K29TKNAFX
```

## describe step
Retrieves the step details associated with an action and step.
```
shipyard describe step
    <step id>
    --action=<action id>

Example:
    shipyard describe step preflight --action=01BTG32JW87G0YKA1K29TKNAFX
```
<dl>
  <dt>&lt;step id&gt;</dt>
  <dd>
    The id of the step found in the describe action response.
  </dd>
  <dt>--action=&lt;action id&gt;</dt>
  <dd>
    The action id that provides the context for this step.
  </dd>
</dl>

## describe validation
Retrieves the validation details assocaited with an action and validation id
```
shipyard describe validation
    <validation id>
    --action=<action id>

Example:
    shipyard describe validation 01BTG3PKBS15KCKFZ56XXXBGF2 \
        --action=01BTG32JW87G0YKA1K29TKNAFX
```
<dl>
  <dt>&lt;step id&gt;</dt>
  <dd>
    The id of the validation found in the describe action response.
  </dd>
  <dt>--action=&lt;action id&gt;</dt>
  <dd>
    The action id that provides the context for this validation.
  </dd>
</dl>

# Get Commands
## get actions
Lists the actions that have been invoked.
```
shipyard get actions
```

## get configdocs
Retrieve documents loaded into Shipyard, either committed or from the
Shipyard Buffer.
```
shipyard get configdocs
    <collection>
    [--committed | --buffer]

Example:
    shipyard get configdocs design
```
<dl>
  <dt>&lt;collection&gt;</dt>
  <dd>
    The collection to retrieve for viewing.
  </dd>
  <dt>--committed</dt>
  <dd>
    Retrieve the documents that have last been committed for this
    collection
  </dd>
  <dt>--buffer</dt>
  <dd>
    Retrive the documents that have been loaded into Shipyard
    since the prior commit. If no documents have been loaded
    into the buffer for this collection, this will return an empty
    response (default)
  </dd>
</dl>

## get renderedconfigdocs
Retrieve the rendered version of documents loaded into Shipyard. Rendered
documents are the "final" version of the documents after applying Deckhand
layering and substitution.
```
shipyard get renderedconfigdocs
    [--committed | --buffer]

Example:
    shipyard get renderedconfigdocs
```
<dl>
  <dt>--committed</dt>
  <dd>
    Retrieve the documents that have last been committed.
  </dd>
  <dt>--buffer</dt>
  <dd>
    Retrieve the documents that have been loaded into Shipyard
    since the prior commit. (default)
  </dd>
</dl>

# help commands
Provides topical help for shipyard.  Note that --help will provide more
specific command help.
```
shipyard help
    [<topic>]

Example:
    shipyard help configdocs
```
<dl>
  <dt>[&lt;topic&gt;]</dt>
  <dd>
    The topic of the help to be displayed. If this parameter is not specified
    the list of avaialable topics will be displayed.
  </dd>
</dl>
