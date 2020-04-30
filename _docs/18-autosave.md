---
title: "Autosave"
permalink: /docs/autosave/
excerpt: ""
last_modified_at: 2018-05-15T15:59:00-04:00
toc: false
---

### Autosave

Menu>Config>Autosave

Pick and prefix and directory and choose to include a PDF or not.  You might want to consider a directory structure based upon coffee origin, roasting date or something else.  Many people save their profiles to a cloud drive so they can access them from multiple machines.

![autosave](/assets/images/gsg/autosave configuration.png)

[COMING IN RELEASE 2.4](https://github.com/artisan-roaster-scope/artisan/blob/master/wiki/ReleaseHistory.md)

The Autosave function has been greatly enhanced.  You now have the option of saving the .alog file and a .pdf to separate directories.  Further you have a great abiltiy to customize the name of your files using various strings which are documented in under Help in the dialog box.  As you enter the strings, the dialog box returns an example of the file save name.  Some examples from the strings are below.  

![autosave in 2.4](/assets/images/gsg/Autosave Configuration 2.jpg)

**Autosave Examples**

When designing these consider your sorting and searching options/patterns for where you store your profiles.  Note that the .alog files and PDFs can be stored to separate directories now.  

Home Roaster – basic batch prefix and number, along with the roast title and date:

String: ~batchprefix ~batchcounter ~title ~date
Output Example: CBB 663 Tanzania Mt. Kilimanjaro 2020-04-08   CBB is the batch prefix, 663 is the batch counter, Tanzania Mt. Kilimanjaro is the title of the roast, and the date.    

Home Roaster using a blend in the roast title and wanting to identify the beans:

String: ~batchprefix ~batchcounter ~title ~beans_line  ~date_long
Output Example: CBB 690 Hama O Rama Espresso Guji Zone Ethiopia - Ahuachapan El Salvador - Nyeri Kenya 4/27/2020

Production roaster interested in roaster’s name (in this case intials), machine name, drumspeed, weight, coffee name, and date.  Not shown but available are volume, density and moisture:  

~operator ~machine ~drumspeed  ~weight ~weightunits ~title ~date_long
MDH NC-500 72  540.0 g Hama O Rama Espresso 2020-04-27

Other date format options are available, and some other fields from Roast Properties.  See Help in the dialog box for more information and notes on specific cases. The string choices are:

![autosave fields](/assets/images/gsg/autosave fields.jpg)

