# summon-update
A python script that queries the sierra API for recently updated items and transfers the resulting file to summon server for updating.

Can be invoked without arguments, in which case it searches for any bib records changed in the last 24 hours.

Can also be invoked with time/date strings in the format below, in whcih caseit will pull records changed in that time period.

example:

./update.py 2019-04-11T08:18:29 2019-04-11T14:18:29
