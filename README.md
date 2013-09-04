IOOS Metamap
============

Metamap is a web frontend to generate source mapping files to be used by [asascience-open/wicken](https://github.com/asascience-open/wicken).  It presents a spreadsheet-like interface that maps a **concept name** to XPath operators to extract data from formats like ISO 19115, NetCDF CF NCML etc.

![Metamap screenshot](http://f.cl.ly/items/3e3V3I2c1W433n3o2x0f/Screen%20shot%202013-09-04%20at%2010.26.07%20AM.png)

### Installing

metamap runs on Python 2.7.x and uses MongoDB.

```
mkvirtualenv metamap && workon metamap
pip install -r requirements.txt
```

**NOTE** wicken will be built and installed from the master branch on github. It requires numpy, which can lead to problems depending on platform - you may wish to `pip install numpy` first or if it fails.

### Running

A `Procfile` is included for use with foreman.  (`sudo gem install foreman`)

When using foreman, you'll want to create a `.env` file:

```
MONGO_URI=mongodb://<username>:<password>@localhost:27017/<db name ie metamap_dev>
APPLICATION_SETTINGS=development.py
SECRET_KEY=my_secret_key
LOG_FILE=yes
```

Username and password are optional.  If you specify them, you'll have to tell mongo about it:

```
$ mongo
MongoDB shell version: 2.4.4
connecting to: test
> use metamap_dev
switched to db metamap_dev
> db.addUser( { user: "mm_user", pwd: "wordpass", roles: [ "readWrite" ] } )
{
  "user" : "mm_user",
	"pwd" : "...",
	"roles" : [
		"readWrite"
	],
	"_id" : ObjectId("...")
}
```

Then start the server using `foreman start`.

### Using

metamap provides a spreadsheet-like interface for creating **mappings** between concept names and XPath queries from **Source Types**.  A **MapSet** is a logical grouping of mappings. A **source mapping** is a downloadable file that contains concept names, descriptions, and XPath queries for a *single* Source Type.

On first run a Default MapSet is created.  You'll need to add Source Types to the application in order to start creating mappings. Press the Source Columns button and enter some new Source Types such as ISO 19115, then press the Save button to update the MapSet to know about these Source Types. 

![Adding Source Types](http://f.cl.ly/items/1g3b2z2T0s1X3l1m0c36/Screen%20shot%202013-09-04%20at%2010.35.46%20AM.png)

#### Adding Mappings

The bottom row of the spreadsheet is for adding new mappings.  Simply begin typing in the Concept Name input box and press tab or use your mouse to change focus to another field and a new mapping will be added.

You can enter an optional description, then an XPath query for each of the Source Types you have added.  The XPath text boxes will auto expand as you focus them.  You do not need to fill out every text box, only the ones that apply.

![Editing Mappings](http://f.cl.ly/items/1Y0U453o093f1a0A3911/Screen%20shot%202013-09-04%20at%2010.39.14%20AM.png)

Mappings automatically save after you've edited them.  If you've added any Eval Sources, they will be updated right after a save.

#### MapSets

A MapSet is a logical grouping of mappings.  On first run, there is a Default MapSet created, but there can be many more in the application.

*COMING SOON* owner/author rights to MapSets

The MapSet dropdown on the navbar allows you to switch between existing MapSets or create new ones.  The numbers to the right indicate how many mappings exist in that MapSet.

##### Creating New

By selecting the New MapSet item on the MapSet dropdown, you can create a new MapSet.  You can optionally copy an existing MapSet with all of its mappings by selecting the checkbox and choosing a MapSet from the dropdown.

You will then be taken to the new MapSet's mapping spreadsheet. You will need to choose your Source Types for this MapSet.

##### Importing Source Mappings

If you have a downloaded Source Mapping (see downloading below), you can use that to create a new MapSet and import all the mappings that exist in it.  Choose the Import Source Mapping item in the MapSet dropdown and select a file to upload.

#### Source Types

Using the Source Columns button pops up a dialog where you can activate/deactivate Source Types for this MapSet, re-order them by dragging, or create new Source Types.  If you press Cancel, the MapSet will be restored to its former state, but any new Source Types you create will still exist.

#### Eval Sources

An Eval Source lets you upload a file or give a URL to an XML file associated with a Source Type.  When you enter XPath queries, these Eval Sources are queried and the results displayed along the bottom row.  You can use this to spot-check your XPath queries for correctness.

![Eval source](http://f.cl.ly/items/2R2e123D3d0I0N2H1d3e/Screen%20shot%202013-09-04%20at%2010.41.27%20AM.png)

##### Adding

To add a new Eval Source, press the Add Eval Source button on the bottom right to popup a dialog.  Give it a name, choose what Source Type it is, and pick a file or enter a URL.

*NOTE* the URL is retrieved at Eval Source add time, not queried live.

##### Evaluating

Eval Sources evaluate automatically when you're editing a mapping.  Applicable Eval Sources will either show up green with a checkmark or red with an error sign depending on if they evaluate ok or not.  You can also evaluate on demand by hovering over a mapping row and pressing the Eval button.

##### Editing/Removing

When hovering over an Eval Source, you can press the Info icon to bring up an editing dialog where you can change information about the Eval Source or remove it. If you don't specify a new file or URL and save it, the old data is preserved.

#### Downloading Source Mappings

A source mapping is a downloadable file that contains concept names, descriptions, and XPath queries for a single Source Type.

A dropdown on the navbar lets you pick from the known Source Types for this MapSet and has your browser download a JSON file that can be used with [asascience-open/wicken](https://github.com/asascience-open/wicken).

### Roadmap

- Authorship/ownership of MapSets
- "Overlaying" MapSets

### Contributors

- Dave Foster <dfoster@asascience.com>
