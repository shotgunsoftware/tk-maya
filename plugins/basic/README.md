# Maya Basic Toolkit workflow plugin

This is a Shotgun Pipeline Toolkit plugin, 
embedding the Shotgun Pipeline Toolkit and allowing
you to easily run and deploy Toolkit Apps and Engines.

The plugin will appear as `shotgun.py` inside of Maya
and will load the `tk-config-basic` configuration.

It is auto-updating and will attempt to check for new
versions of this configuration during startup.

The plugin can either run directly from the engine,
via the toolkit launch application, or as a standalone plugin.

### Technical Details

This is a Maya Module that enables basic Shotgun integration
inside Maya. The plugin source is located in the [toolkit maya engine repository](https://github.com/shotgunsoftware/tk-maya/tree/develop/plugin/plugins/basic).
Maya version 2014 and above are supported.
You can read more about maya modules [here](http://help.autodesk.com/view/MAYAUL/2017/ENU/?guid=__files_GUID_CB76E356_753B_4837_8C5B_3296C14872CA_htm).


# Engine-based plugin

If you are using toolkit's application launcher `tk-multi-launchapp`, you can 
configure this to start up the plugin as part of launching maya.

This is all done as part of the maya engine configuration. Simply include 
the parameter `launch_builtin_plugins: [basic]` as part of your engine configuration
and the launch app will load the plugin whenever maya is launched for that context:

```
  tk-maya:
    apps:
      ...

    launch_builtin_plugins: [basic]  
    location:
      type: app_store
      name: tk-maya
      version: v1.2.3
```


# Standalone Plugin

## Building the plugin

If you want to run the plugin as a standalone module, you 
first need to build it. The build process will prepare the 
plugin for a standalone run and will cache all necessary
toolkit components in a special `bundle_cache` directory 
that comes with the plugin.

In order to build it into a plugin which can be loaded into maya, it needs to be 
built using a [build script](https://github.com/shotgunsoftware/tk-core/blob/master/developer/build_plugin.py)
that comes as part of the Toolkit Core API.

In order to build the plugin, follow these steps:

- Clone the Toolkit API: `git clone git@github.com:shotgunsoftware/tk-core.git`

- Clone the Toolkit Maya Engine: `git@github.com:shotgunsoftware/tk-maya.git`

- Checkout the plugin branch: `git checkout develop/plugin`
 
- The build script is located in the `developer` subfolder and called `build_plugin.py`

- In order to build the plugin in `/tmp/maya_plugin, run `python build_plugin.py MAYA_ENGINE/plugins/basic /tmp/maya_plugin`


A more complete example would be:

```
mkdir /tmp/build_example
cd /tmp/build_example

# checkout code
git clone git@github.com:shotgunsoftware/tk-core.git
git clone git@github.com:shotgunsoftware/tk-maya.git

# switch to develop/plugin branch
cd /tmp/build_example/tk-maya
git checkout develop/plugin

# build the plugin
cd /tmp/build_example/tk-core/developer
python build_plugin.py /tmp/build_example/tk-maya/plugins/basic /tmp/build_example/built_plugin
```


## Using the plugin

The easiest way to get the plugin loaded is to add an entry to the 
`MAYA_MODULE_PATH`. 

For example, if you have put the plugin in
`/Users/john.smith/Documents/shotgun_basic`, just add this path to your existing
Maya module path and restart maya.

### Using a maya.env file

If you are using a `Maya.env` file, you can define the `MAYA_MODULE_PATH`
environment variable there.

For example, on Linux and Mac OS X: `MAYA_MODULE_PATH=$HOME/Documents/shotgun_basic`

For example, on Windows: `MAYA_MODULE_PATH=%HOME%\Documents\shotgun_basic`

For more information about Maya plugins and `maya.env`, please see the Maya Documentation.


# Additional documentation resources

If you are a developer making changes to this plugin or it's components,
you may find the following resources useful:

- Read more about Plugin development 
  in our [Toolkit Developer Documentation](http://developer.shotgunsoftware.com/tk-core/bootstrap.html#developing-plugins).

- The plugin needs to be built before it can be executed. You do this by 
  executing the build tools found [here](https://github.com/shotgunsoftware/tk-core/blob/master/developer).

- For more information about Toolkit, see http://support.shotgunsoftware.com/



