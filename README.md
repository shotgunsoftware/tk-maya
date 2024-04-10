[![GitHub release (latest by date including pre-releases)](https://img.shields.io/github/v/release/nfa-vfxim/tk-maya?include_prereleases)](https://github.com/nfa-vfxim/tk-maya) 
[![GitHub issues](https://img.shields.io/github/issues/nfa-vfxim/tk-maya)](https://github.com/nfa-vfxim/tk-maya/issues) 


# ShotGrid Engine for Maya <img src="icon_256.png" alt="Icon" height="24"/>

ShotGrid Integration in Maya

## Requirements

| ShotGrid version | Core version | Engine version |
|------------------|--------------|----------------|
| -                | v0.19.18     | -              |

## Configuration

### Booleans

| Name                       | Description                                                                                                                                 | Default value |
|----------------------------|---------------------------------------------------------------------------------------------------------------------------------------------|---------------|
| `automatic_context_switch` | Controls whether toolkit should attempt to automatically adjust its context every time the currently loaded file changes. Defaults to True. | True          |
| `debug_logging`            | Controls whether debug messages should be emitted to the logger                                                                             | False         |
| `use_sgtk_as_menu_name`    | Optionally choose to use 'Sgtk' as the primary menu name instead of 'ShotGrid'                                                              | False         |


### Integers

| Name                               | Description                                                                                                                                                                                                                                                                  | Default value |
|------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------|
| `compatibility_dialog_min_version` | Specify the minimum Application major version that will prompt a warning if it isn't yet fully supported and tested with Toolkit.  To disable the warning dialog for the version you are testing, it is recomended that you set this value to the current major version + 1. | 2015          |


### Lists

| Name                     | Description                                                                                                                                                                                                                                                                                                                                                                                                             | Default value |
|--------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------|
| `menu_favourites`        | Controls the favourites section on the main menu. This is a list and each menu item is a dictionary with keys app_instance and name. The app_instance parameter connects this entry to a particular app instance defined in the environment configuration file. The name is a menu name to make a favourite.                                                                                                            |               |
| `run_at_startup`         | Controls what apps will run on startup.  This is a list where each element is a dictionary with two keys: 'app_instance' and 'name'.  The app_instance value connects this entry to a particular app instance defined in the environment configuration file.  The name is the menu name of the command to run when the Maya engine starts up.  If name is '' then all commands from the given app instance are started. | []            |
| `launch_builtin_plugins` | Comma-separated list of tk-maya plugins to load when launching Maya. Use of this feature disables the classic mechanism for bootstrapping Toolkit when Maya is launched.                                                                                                                                                                                                                                                | []            |


### Templates

| Name               | Description                                                                                                                                                                                                    | Default value | Fields |
|--------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------|--------|
| `template_project` | Template to use to determine where to set the maya project location. This should be a string specifying the template to use but can also be empty if you do not wish the Maya project to be automatically set. |               |        |


