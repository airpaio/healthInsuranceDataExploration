
# coding: utf-8

# This document is a basic demonstration of the type of data analysis that I could do for your company.  It's not a full fledged and detailed analysis, but is more of a showing of my capabilities of using programming to do data analysis and create data visualizations.  

# In[1]:

import numpy as np
import pandas as pd
import plotly.plotly as py
import plotly.offline as ploff

from ggplot import *
from subprocess import check_output
#from plotly.offline import init_notebook_mode, plot

ploff.init_notebook_mode()


# We will be looking at **ACA US Health Insurance Marketplace** data on health and dental plans offered to individuals and small businesses over the years 2014-2016.
# 
# This data was initially released by the **Centers for Medicare & Medicaid Services (CMS)**, and downloaded from https://www.kaggle.com/hhsgov/health-insurance-marketplace where the zipped file was 734.9MB and took 4-5 minutes to download over a 150MBs internet connection. The uncompressed file came out to be 11.53GB.  This is pretty huge for my Macbook Air to handle, so we will only take a look at the Rates.csv (1.97GB) data set where each record relates to one issuer’s rates based on plan, geographic rating area, and subscriber eligibility requirements over plan years 2014, 2015, and 2016.  
# 
# A data dictionary can be found for this data set at https://www.cms.gov/CCIIO/Resources/Data-Resources/Downloads/Rate_DataDictionary_2016.pdf  
# 
# There are several variables in the Rates data set, and we'll only be reading in a subset of them for this quick exploration of the data.  In particular, we will explore the variables
# 
# * **BusinessYear** - year of the insurance plan, i.e., 2014, 2015, or 2016  
# * **StateCode** - state where the data record is from
# * **Age** - Age of the individuals plan, or FamilyOption if the plan covers an entire family, or fo the high end we simply have the age '65 or older'
# * **IndividualRate** - monthly premium rate for an individual
# * **Couple** - monthly premium for a couple

# In[2]:

# read in the data
headers = ['BusinessYear', 'StateCode', 'Age', 
           'IndividualRate', 'Couple']

# read in chuncks for memory efficiency
filePath = 'data/health-insurance-marketplace/Rate.csv'
chunks = pd.read_csv(filePath, iterator=True, chunksize=1000,
                    usecols=headers)
rates = pd.concat(chunk for chunk in chunks)


# In[10]:

# take a look at a few random rows of data
randomRows = rates.sample(n=6)
randomRows


# We can get descriptive statistics on various columns of data...

# In[13]:

# get descriptive stats on rates for couples
pd.set_option('display.float_format', lambda x: '%.2f' % x)
print rates['Couple'].describe()


# In[14]:

# and descriptive stats for rates on Individuals
print rates['IndividualRate'].describe()


# Uh Oh!  The max rate for individuals is $999999.00  
# The data dictionary describes the Rate as the dollar value for the insurance premium cost applicable to the subscriber.  With this information, I am assuming that the rates are on a per month time frequency.
# There was discussion online about these strange values possibly being a coded value for missing data. Whether it's a data entry error or just a missing value code, we will go ahead and filter it out since it's just unreasonable for an individual to have to pay that much for health insurance.

# In[15]:

# filter out the strange values and run descriptive statistice again
ratesInd9000 = rates[rates.IndividualRate < 9000]
print ratesInd9000['IndividualRate'].describe()


# The max has gone down to $5503 now, which still seems unreasonable, but should require more investigation before we decide to filter it out.  
# 
# Before investigating further, let's look at a couple of distribution plots

# In[17]:

# lets plot a distribution for the Couple rates
ggplot(aes(x='Couple'), data=rates) +     geom_histogram(binwidth=10) +     ggtitle('Distribution of Couple Rates')


# In[20]:

# and the same distribution plot for IndividualRates
ggplot(aes(x='IndividualRate'), data=ratesInd9000) +     geom_histogram(binwidth=25, colour='red') +     ggtitle('Distribution of Individual Rates')


# There seem to be a huge amount, nearly 2.5 million individuals that pay less than $25 for health insurance premiums. Is this reasonable? Perhaps this could represent the population of poor people who may have their insurance substantially subsidized.
# 
# On the other hand, notice the x-axis extends out to 6000.  This is because of the max premium value being \$5503.  Let's dig into this a bit more.  In the distribution plot for Individuals, the right tail seems to die off aroun \$1200-1500.  Let's get a count of how many premiums are greater than $1200.

# In[34]:

indRate1200 = ratesInd9000[ratesInd9000.IndividualRate > 1200].count()['IndividualRate']
percentageOfTotalInd9000 = indRate1200 / ratesInd9000['IndividualRate'].describe()['count']
print '%i individual plans have a rate greater than $1200. Thats %% %f of the total number of IndividualRate plans that we filtered out below $9000' % (indRate1200, percentageOfTotalInd9000)


# It seems like there is still a large number of people that have to pay a substantial amount for their insurance premiums. Taking it further, lets see if we can figure out where these people may be located who are paying the most for their insurance. 
# 
# Here, I will be doing something that is similar to 'pivot tables' in Excel.  I will be grouping the IndividualRate data for the year 2014 by the average cost for each state.

# In[45]:

# setup an IndividualRate data frame for the year 2014.
columns = ['BusinessYear', 'StateCode', 'IndividualRate']
indRates = pd.DataFrame(ratesInd9000, columns=columns)
indRates2014 = indRates[indRates.BusinessYear == 2014]
indRates2014 = indRates2014.dropna(subset=['IndividualRate'])
randomRows2014 = indRates2014.sample(n=6)
randomRows2014


# In[46]:

indRates2014['IndividualRate'].describe()


# In[48]:

indMean2014 = indRates2014.groupby('StateCode', as_index=False).mean()
indMean2014


# In[50]:

for col in indMean2014.columns:
    indMean2014[col] = indMean2014[col].astype(str)
    
# set color scale
colors = [[0.0, 'rgb(242,240,247)'], [0.2, 'rgb(218,218,235)'],
         [0.4, 'rgb(188,189,220)'], [0.6, 'rgb(158,154,200)'],
         [0.8, 'rgb(117,107,177)'], [1.0, 'rgb(84,39,143)']]

indMean2014['text'] = indMean2014['StateCode'] + ' ' + 'Individuals' + ' ' + indMean2014['IndividualRate']

data = [dict(
    type = 'choropleth',
    colorscale = colors,
    autocolorscale = False,
    locations = indMean2014['StateCode'],
    z = indMean2014['IndividualRate'].astype(float),
    locationmode = 'USA-states',
    text = indMean2014['text'],
    marker = dict(
            line = dict(
                color = 'rgb(255,255,255)',
                width = 2
            )
        ),
        colorbar = dict(
            title = 'Rates USD'
        )
    )]

layout = dict(
    title = '2014 US Health Insurance Marketplace Average Rates by States for Individuals',
    geo = dict(
        scope = 'usa',
    projection = dict(type='albers usa'),
    showlakes = True,
    lakecolor = 'rgb(255,255,255)',
    ),
)

fig = dict(data=data, layout=layout)

ploff.iplot(fig)


# Judging by the color scales on the map, Alaska has the highest average rates of about \$650.  Some of the northern and midwestern states have some high rates as well, coming in at around $450.  
# 
# We could go on and on to find out which state[s] have the highest rates by going on to do a distribution and outlier analysis in each of the individual states (especially those with higher average rates.)  Also, it would probably be hard with only 3 years worth of rates data, but we could possibly build a forecast for rates in the year 2017.

# In[ ]:



