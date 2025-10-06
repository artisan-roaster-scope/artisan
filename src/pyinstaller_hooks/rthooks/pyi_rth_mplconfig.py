# empty matplotlib runtime hook which prevents setting the MPLCONFIGDIR to a different temporary directory on each startup
# causing the MPL font cache to be recreated on each (slow) app startup
