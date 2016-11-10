# Maya Basic Toolkit workflow plugin

This is a Shotgun Pipeline Toolkit plugin, 
embedding the Shotgun Pipeline Toolkit and allowing
you to easily run and deploy Toolkit Apps and Engines.



## Using the Plugin

This is a Maya Module that enables basic Shotgun integration
Inside of Maya. Maya version 2014 and above are supported.

### Adding to MAYA_MODULE_PATH

The easiest way to get the plugin loaded is to add an entry to the 
`MAYA_MODULE_PATH`. For example, if you have unzipped the plugin into
a `/Users/john.smith/Documents/toolkit_maya_plugin`, simply execute

```
export MAYA_MODULE_PATH=$MAYA_MODULE_PATH:/Users/john.smith/Documents/toolkit_maya_plugin
```

in a shell and then launch maya from that shell. On windows, you can set up the 
environment variable in your computer preferences.

### Using a maya.env file

If you are using a `Maya.env` file, you can define the `MAYA_MODULE_PATH`
environment variable there.

For example, on Linux and Mac OS X: `MAYA_MODULE_PATH=$HOME/my_maya_modules/tk-maya-basic`

For example, on Windows: `MAYA_MODULE_PATH=%HOME%\my_maya_modules\tk-maya-basic`

For more information about Maya plugins and `maya.env`, please see the Maya Documentation.




## Building the plugin

The plugin source is located in the [toolkit maya engine repository](https://github.com/shotgunsoftware/tk-maya/tree/develop/plugin/plugins/basic).

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


### Additional documentation resources

If you are a developer making changes to this plugin or it's components,
you may find the following resources useful:

- Read more about Plugin development 
  in our [Toolkit Developer Documentation](http://developer.shotgunsoftware.com/tk-core/bootstrap.html#developing-plugins).

- The plugin needs to be built before it can be executed. You do this by 
  executing the build tools found [here](https://github.com/shotgunsoftware/tk-core/blob/master/developer).

- For more information about Toolkit, see http://support.shotgunsoftware.com/



