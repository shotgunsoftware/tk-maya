# Maya Basic Toolkit workflow plugin

This is a Shotgun Pipeline Toolkit plugin, 
embedding the Shotgun Pipeline Toolkit and allowing
you to easily run and deploy Toolkit Apps and Engines.


## Documentation for users

This is a Maya Module that enables basic Shotgun integration
Inside of Maya. Maya version 2014 and above are supported.

### Installing the Shotgun Maya Plugin

Simply add the path to this module to your `MAYA_MODULE_PATH`
environment variable, and a Shotgun plugin will appear in the
Plugin preferences inside Maya.

If you are using a `Maya.env` file, you can define the `MAYA_MODULE_PATH`
environment variable there.

For example, on Linux and Mac OS X: `MAYA_MODULE_PATH=$HOME/my_maya_modules/tk-maya-basic`

For example, on Windows: `MAYA_MODULE_PATH=%HOME%\my_maya_modules\tk-maya-basic`

For more information about Maya plugins and `maya.env`, please see the Maya Documentation.


## Documentation for developers

If you are a developer making changes to this plugin or it's components,
you may find the following resources useful:

- Read more about Plugin development 
  in our [Toolkit Developer Documentation](http://developer.shotgunsoftware.com/tk-core/bootstrap.html#developing-plugins).

- The plugin needs to be built before it can be executed. You do this by 
  executing the build tools found [here](https://github.com/shotgunsoftware/tk-core/blob/master/developer).

- For more information about Toolkit, see http://support.shotgunsoftware.com/



