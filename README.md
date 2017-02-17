fara
====

This project is a scrapy spider for scraping information about foreign
principals, registered under the Foreign Agents Registration Act (FARA).

It takes around 5-6 minutes to collect all data with AUTOTHROTTLE enabled (see
settings).


INSTALLATION
------------
Download and unzip the zip file to a convenient location.


INSTALLING DEPENDENCIES
-----------------------
If you are satisfied that `scrapy` and `pytest` are present and working in your
environment you can skip this step as the fara spider itself needs no
installation other than unzipping.

Otherwise, to ensure all dependencies are present, install to a conda env.
Instructions to install Miniconda are here: https://conda.io/docs/install/quick.html

    WINDOWS
    conda create -n fara python=2.7 scrapy=1.3.2 pytest=3.0.6 -c conda-forge
    activate fara

    LINUX
    conda create -n fara python=2.7 scrapy=1.3.2 pytest=3.0.6 -c conda-forge
	source activate fara


TESTING
-------
Once the dependencies are installed, run the integration test (from inside the
project root directory):

    pytest -v


USAGE
-----
Run the spider (again, from inside the project root directory):

    scrapy crawl fara

By default the results are output to "<datestamp>.fara.json" in the project root 
directory. This can be changed by setting the `FEED_URI` parameter in the
`fara.settings.py` module, or from the command line when running the crawler.

    scrapy crawl fara -s FEED_URI="/path/to/output.json"


OUTPUT EXAMPLE
--------------
{
    "exhibit_urls": [{
        "date": "2014-07-03 00:00:00",
        "foreign_principal": "Transformatin and Continuity",
        "exhibit_url": "http://www.fara.gov/docs/6065-Exhibit-AB-20140703-5.pdf"
    }],
    "url": "https://efile.fara.gov/pls/apex/f?p=171:200:0::NO:RP,200:P200_REG_NUMBER,P200_DOC_TYPE,P200_COUNTRY:6065,Exhibit%20AB,AFGHANISTAN",
    "country": "AFGHANISTAN",
    "state": "VA",
    "reg_num": "6065",
    "foreign_principal": "Transformation and Continuity",
    "address": "8105 Ainsworth Avenue\r\nSpringfield\u00a0\u00a022152",
    "date": "2014-07-03 00:00:00",
    "registrant": "Roberti + White, LLC"
}


OPTIONS
-------
`NUM_RESPONSES`
This sets how how many foreign principal rows are returned in the initial call
(by default we populate them all in a single call but this is not always
desirable, for example in integration testing. It can be set in
`fara.settings.py` or from the command line.

For example to call 2 rows from the live site to check results are as expected:

    scrapy crawl fara -s NUM_RESPONSES=2 -s HTTPCACHE_ENABLED=False


IMPLEMENTATION NOTES
--------------------
The process is to first set the session cookie by a GET request to:
	https://efile.fara.gov/pls/apex/f?p=171:130:0::NO:RP,130:P130_DATERANGE:N

This then allows us to make a POST to:
	https://efile.fara.gov/pls/apex/wwv_flow.show

This is an APEX form to which we submit a number of parameters. Most useful for
our purposes is the `p_widget_num_return` which controls the number of results
per page. If we set this high then we receive all the foreign principal rows in
a single call. The default for `All` is 100000. Currently there are in the
order of 500 items so this allows plenty of time for growth.

Next we extract the required data which are mainly contained within the foreign
principal row apart from the exhibit links, and add them to our item.

Finally we make a GET request to the link found in the foreign principal row to
see the exhibits stored for this foreign principal's registering agent, e.g:
	https://efile.fara.gov/pls/apex/f?p=171:200:0::NO:RP,200:P200_REG_NUMBER,P200_DOC_TYPE,P200_COUNTRY:6065,Exhibit%20AB,AFGHANISTAN

From here we extract 0 (see ANALYSIS [1] below) or more exhibit descriptions.
These are returned as a list of dicts (see ANALYSIS [2] for reasoning) as
follows:

    [{"date": datetime.datetime(), 
     "url": "http://www.fara.gov/docs/<doc link>",
     "foreign_pricipal": "<foreign principal name>"}, ...]

The item is passed through a pipeline to prepare it for serialisation to JSON 
(converting empty strings and lists to None), and finally added to a `jsonlines`
file with the name `(datestamp).fara.json` stored in the project root directory.


ANALYSIS
--------
1) Missing data
In some cases there appears to be a bug with FARA where countries with brackets
or dots in their name return zero results for exhibits, suggesting an issue on
the backend with SQL sanitisation. The approach I've taken here is to return
None, though it may be advisable to raise the issue with the site owners.

Those with brackets:
	CONGO (KINSHASA) (ZAIRE)
	CONGO (BRAZZAVILLE)
	COTE D'IVOIRE (IVORY COAST)
	TIMOR-LESTE (EAST TIMOR)

Those with dots:
	ST. BARTS
	ST. LUCIA
	ST. VINCENT AND THE GRENADINES

There are other countries with dots, brackets, or both, but these have no
registered foreign agents at the moment.

The other missing data issue identified is that there are no exhibit URLs 
available for two of the foreign principals in the CAYMAN ISLANDS. These are
Polymet Alloys Inc. (only registerd 02/16/2017 so may be available later),
and Government of the Cayman Islands (registered 03/04/1974).

The URLs which fail (currently 17) are logged at ERROR level during scraping,
but the data which could be gathered is retained.

2) Exhibit links
If the approach had been to retrieve just the most recent PDF link, there is a
risk that some of the URLs refer to a different foreign principal than is
intended. This is because some of the registering agents register on behalf of
multiple foreign principals. There are also different document types stored.
Retrieving only the most recent leaves potential sources of information behind.

For this reason, we return details on all the exhibits available, which can be
used to disambiguate them at a later date if required, for example by a fuzzy
comparison of the foreign_principal names, or fuzzy date matching, or even a
combination of the two. A stub function, `faraspider.disambiguate_doclinks` has
been added to contain this logic.
