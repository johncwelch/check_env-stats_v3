# check_env-stats_v3
start of updating nagios probe for snmpv3 support

so this is the start of me updating Brady Lamprecht's nagios prob check_env_stats.py for SNMPv3

currently, it only works for cisco stuff and it doesn't do anything with engine ID's or contexts. That's coming, along with shoving the v3 support into the other hardware sections. It's pretty straightforward and decently commented.

8 May 19:

now works with Juniper (LIMITED). Shows PSU and Fan status, not RPMs or temps or voltages. RPMs would be completely new. That will be a while, if ever. voltages, I can't really test with due to limitations on my gear (ex4550s, so I have no idea what temps actually look like). Temps, I'm working on. Such a pain in the tuchas. 
