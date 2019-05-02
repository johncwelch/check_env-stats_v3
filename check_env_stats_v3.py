#! /usr/bin/python
#
# Copyright (c) Brady Lamprecht
# Licensed under GPLv3
# March 2009
#
#
# SNMPv3 code by John Welch
# my code is BSD, the GPL can piss up a rope.
#
# check_env_stats plug-in for nagios
# Uses SNMP to poll for voltage, temerature, fan, and power supply statistics
#
# History:
#
# v0.1 Very basic script to poll given SNMP values (Foundry only)
# v0.2 Added functionality for temperature, fans, power supplies
# v0.3 Included Cisco support with the addition of voltage
# v0.4 Functions to set warning and critical levels were added
# v0.5 Now implements "-p" perfmon option for performance data
# v1.0 Code cleanup and a few minor bugfixes
# v1.1 first additions of SNMPv3 support.

import os
import sys
from optparse import OptionParser

scriptversion = "1.0"

errors = {
    "OK": 0,
    "WARNING": 1,
    "CRITICAL": 2,
    "UNKNOWN": 3,
    }

#common_options = "snmpwalk -OvQ -v 1"
common_options = ""
# function for setting common options
def set_common_options(snmpver):
    #this way we know which common_options we're setting
    global common_options
    if snmpver == "2":
        common_options = "snmpwalk -OvQ -v 1"
        #print(snmpwalkstring)
    elif snmpver == "3":
        common_options = "snmpwalk -OvQ -v 3"
        #print(snmpwalkstring)
    else:
        print "Invalid SNMP version, must be 2 or 3"
        sys.exit()

# Function for Cisco equipment
def check_cisco(hostname,community,mode,verbose,version,secLevel,authProt,authPass,encryptProt,encryptPass,userName):
    #if check on version to build command
    if version == "2":
        command = common_options + " -c " + community + " " + hostname + " "
    elif version == "3":
        #gonna be a lot of checking in here. SO MANY IF STATMENTS
        #print "SNMPv3"
        #Seclevel checking
        if secLevel == None or secLevel == "":
            fail("You must have a security level for snmpv3. Valid levels are: noAuthNoPriv, authNoPriv, authPriv")
            sys.exit()
        elif secLevel == "noAuthNoPriv":
            #for this level, you HAVE to still provide a username
            if userName == None or userName == "":
                fail("When using a security level of noAuthNoPriv, you must provide a username")
                sys.exit()
            
            #username provided
            command = common_options + " -l " + secLevel + " -u " + userName + " " + hostname + " "
            
        elif secLevel == "authNoPriv":
            #for this level, we need a username, an authentication protocol and an authentication passphrase
            if (userName == None or userName == "") or (authProt == None or authProt == "") or (authPass == None or authPass == ""):
               fail("When using a security level of authNoPriv, you must provide a username, an authentication protocol and an authentication passphrase")
               sys.exit()
            
            #username/authProt/authPass provided. Now we check for valid authProt (MD5 or SHA)
            if authProt != "MD5" and authProt != "SHA":
                fail("The authentication protocol must be MD5 or SHA")
                sys.exit()
               
            #auth protocol is valid, build the command
            command = common_options + " -l " + secLevel + " -u " + userName + " -a " + authProt + " -A " + authPass + " " + hostname + " "
          
        elif secLevel == "authPriv":
            if (userName == None or userName == "") or (authProt == None or authProt == "") or (authPass == None or authPass == ""):
               fail("When using a security level of authPriv, you must provide a username, an authentication protocol and an authentication passphrase")
               sys.exit
            if (encryptProt == None or encryptProt == "") or (encryptPass == None or encryptPass == ""):
               fail("When using a security level of authPriv, you must provide an encryption protocol and an encryption passphrase")
               sys.exit
            
            #check that authProt is valid
            if authProt != "MD5" and authProt != "SHA":
                fail("The authentication protocol must be MD5 or SHA")
                sys.exit()
            
            #check that encryptProt is valid
            if encryptProt != "DES" and encryptProt != "AES":
                fail("The authentication protocol must be AES or DES")
                sys.exit()
            
            #valid encrypt protocol, build the command
            command = common_options + " -l " + secLevel + " -u " + userName + " -a " + authProt + " -A " + authPass + " " + " -x " + encryptProt + " -X " + encryptPass + " " + hostname + " "
     
        else:
            fail("Invalid seclevel, valid levels are: noAuthNoPriv, authNoPriv, authPriv")
            sys.exit()
        
    else:
        print "Invalid SNMP version, must be 2 or 3"
        sys.exit()
    ciscoEnvMonObjects = "1.3.6.1.4.1.9.9.13.1"

    if mode == "volt":
        ciscoVoltDescTable = ciscoEnvMonObjects + ".2.1.2"
        ciscoVoltValuTable = ciscoEnvMonObjects + ".2.1.3"
        desc = os.popen(command + ciscoVoltDescTable).read()[:-1].replace('\"', '').split('\n')
        valu = os.popen(command + ciscoVoltValuTable).read()[:-1].replace('\"', '').split('\n')
        if verbose:
            print_verbose(ciscoVoltDescTable,desc,ciscoVoltValuTable,valu)
        if desc[0] == '' or valu[0] == '':
            fail("description / value table empty or non-existent.")
        return(desc,valu)

    if mode == "temp":
        ciscoTempDescTable = ciscoEnvMonObjects + ".3.1.2"
        ciscoTempValuTable = ciscoEnvMonObjects + ".3.1.3"
        desc = os.popen(command + ciscoTempDescTable).read()[:-1].replace('\"', '').split('\n')
        valu = os.popen(command + ciscoTempValuTable).read()[:-1].replace('\"', '').split('\n')
        if verbose:
            print_verbose(ciscoTempDescTable,desc,ciscoTempValuTable,valu)
        if desc[0] == '' or valu[0] == '':
            fail("description / value table empty or non-existent.")
        return(desc,valu)

    if mode == "fans":
        # Possible values:
        # 1=normal,2=warning,3=critical,4=shutdown,5=notPresent,6=notFunctioning
        ciscoFansDescTable = ciscoEnvMonObjects + ".4.1.2"
        ciscoFansValuTable = ciscoEnvMonObjects + ".4.1.3"
        desc = os.popen(command + ciscoFansDescTable).read()[:-1].replace('\"', '').split('\n')
        valu = os.popen(command + ciscoFansValuTable).read()[:-1].replace('\"', '').split('\n')
        if verbose:
            print_verbose(ciscoFansDescTable,desc,ciscoFansValuTable,valu)
        if desc[0] == '' or valu[0] == '':
            fail("description / value table empty or non-existent.")
        return(desc,valu)

    if mode == "power":
        # Possible values:
        # 1=normal,2=warning,3=critical,4=shutdown,5=notPresent,6=notFunctioning
        ciscoPowrDescTable = ciscoEnvMonObjects + ".5.1.2"
        ciscoPowrValuTable = ciscoEnvMonObjects + ".5.1.3"
        desc = os.popen(command + ciscoPowrDescTable).read()[:-1].replace('\"', '').split('\n')
        valu = os.popen(command + ciscoPowrValuTable).read()[:-1].replace('\"', '').split('\n')
        if verbose:
            print_verbose(ciscoPowrDescTable,desc,ciscoPowrValuTable,valu)
        if desc[0] == '' or valu[0] == '':
            fail("description / value table empty or non-existent.")
	return(desc,valu)

    # Should never get to here
    sys.exit(errors['UNKNOWN'])

# Function for Foundry equipment
def check_foundry(hostname,community,mode,verbose):
    command = common_options + " -c " + community + " " + hostname + " "
    foundrySNAgent = "1.3.6.1.4.1.1991.1.1"

    if mode == "volt":
        fail("voltage table does not exist in Foundry's MIB.")

    if mode == "temp":
        foundryTempDescTable = foundrySNAgent + ".2.13.1.1.3"
        foundryTempValuTable = foundrySNAgent + ".2.13.1.1.4"
        desc = os.popen(command + foundryTempDescTable).read()[:-1].replace('\"', '').split('\n')
        valu = os.popen(command + foundryTempValuTable).read()[:-1].replace('\"', '').split('\n')
        if verbose:
            print_verbose(foundryTempDescTable,desc,foundryTempValuTable,valu)
        if desc[0] == '' or valu[0] == '':
            fail("description / value table empty or non-existent.")
        return(desc,valu)

    if mode == "fans":
        # Possible values:
        # 1=other,2=normal,3=critical
        foundryFansDescTable = foundrySNAgent + ".1.3.1.1.2"
        foundryFansValuTable = foundrySNAgent + ".1.3.1.1.3"
        desc = os.popen(command + foundryFansDescTable).read()[:-1].replace('\"', '').split('\n')
        valu = os.popen(command + foundryFansValuTable).read()[:-1].replace('\"', '').split('\n')
        if verbose:
            print_verbose(foundryFansDescTable,desc,foundryFansValuTable,valu)
        if desc[0] == '' or valu[0] == '':
            fail("description / value table empty or non-existent.")
        return(desc, valu)

    if mode == "power":
        # Possible values:
        # 1=other,2=normal,3=critical
        foundryPowrDescTable = foundrySNAgent + ".1.2.1.1.2"
        foundryPowrValuTable = foundrySNAgent + ".1.2.1.1.3"
        desc = os.popen(command + foundryPowrDescTable).read()[:-1].replace('\"', '').split('\n')
        valu = os.popen(command + foundryPowrValuTable).read()[:-1].replace('\"', '').split('\n')
        if verbose:
             print_verbose(foundryPowrDescTable,desc,foundryPowrValuTable,valu)
        if desc[0] == '' or valu[0] == '':
            fail("description / value table empty or non-existent.")
        return(desc,valu)

    # Should never get to here
    sys.exit(errors['UNKNOWN'])

# Function for HP equipment
def check_hp(hostname,community,mode,verbose):
    fail("HP functions not yet implemented.")

# Function for Juniper equipment
def check_juniper(hostname,community,mode,verbose):
    fail("Juniper functions not yet implemented.")

# Function to process data from SNMP tables
def process_data(description, value, warning, critical, performance):
    string = ""
    status = "OK"
    perfstring = ""

    if critical and warning:
        if len(critical) != len(description):
            fail("number of critical values not equal to number of table values.")
        elif len(warning) != len(description):
            fail("number of warning values not equal to number of table values.")
        else:
	
            # Check for integer or string values

            # Check each table value against provided warning & critical values
            for d, v, w, c in zip(description,value,warning,critical):
                if len(string) != 0:
                    string += ", "
                if v >= c:
                    status = "CRITICAL"
                    string += d + ": " + str(v) + " (C=" + str(c) + ")"
                elif v >= w:
                    if status != "CRITICAL":
                        status = "WARNING"
                    string += d + ": " + str(v) + " (W=" + str(w) + ")"
                else:
                    string += d + ": " + str(v)

                # Create performance data
                perfstring += d.replace(' ', '_') + "=" + str(v) + " "

    # Used to provide output when no warning & critical values are provided
    else:
         for d, v in zip(description,value):
             if len(string) != 0:
                  string += ", "
             string += d + ": " + str(v)
             
             # Create performance data
             perfstring += d.replace(' ', '_') + "=" + str(v) + " "

    # If requested, include performance data
    if performance:
        string += " | " + perfstring

    # Print status text and return correct value.
    print status + ": " + string
    sys.exit(errors[status])

def print_verbose(oid_A,val_A,oid_B,val_B):
    print "Description Table:\n\t" + str(oid_A) + " = \n\t" + str(val_A)
    print "Value Table:\n\t" + str(oid_B) + " = \n\t" + str(val_B)
    sys.exit(errors['UNKNOWN'])

def fail(message):
    print "Error: " + message	
    sys.exit(errors['UNKNOWN'])

def main():
    args = None
    options = None	

    # Create command-line options
    parser = OptionParser(version="%prog " + scriptversion)
    parser.add_option("-H", action="store", type="string", dest="hostname", help="hostname or IP of device")
    parser.add_option("-C", action="store", type="string", dest="community", help="community read-only string [default=%default]", default="public")
    parser.add_option("-T", action="store", type="string", dest="type", help="hardware type (cisco,foundry,hp,juniper)")
    parser.add_option("-M", action="store", type="string", dest="mode", help="type of statistics to gather (temp,fans,power,volt)")
    parser.add_option("-w", action="store", type="string", dest="warn", help="comma-seperated list of values at which to set warning")
    parser.add_option("-c", action="store", type="string", dest="crit", help="comma-seperated list of values at which to set critical")
    parser.add_option("-p", action="store_true", dest="perf", help="include perfmon output")
    parser.add_option("-v", action="store_true", dest="verb", help="enable verbose output")
    #snmpv3 options
    parser.add_option("-V", action="store", type="string", dest="snmpver", help="version of snmp, use either 2 or 3")
    parser.add_option("-l", action="store", type="string", dest="secLevel", help="snmpv3 security level, use either noAuthNoPriv, authNoPriv, authPriv")
    parser.add_option("-a", action="store", type="string", dest="authProt", help="snmpv3 authentication protocol to use, use either MD5 or SHA")
    parser.add_option("-A", action="store", type="string", dest="authPass", help="snmpv3 authentication passphrase")
    parser.add_option("-x", action="store", type="string", dest="encryptProt", help="snmpv3 encryption protocol to use, use either DES or AES")
    parser.add_option("-X", action="store", type="string", dest="encryptPass", help="snmpv3 encryption passphrase")
    parser.add_option("-u", action="store", type="string", dest="userName", help="snmpv3 user name")
    (options, args) = parser.parse_args(args)

    # Map parser values to variables
    host = options.hostname
    comm = options.community
    type = options.type
    mode = options.mode
    warn = options.warn
    vers = options.snmpver
    secl = options.secLevel
    aprot = options.authProt
    apass = options.authPass
    eprot = options.encryptProt
    epass = options.encryptPass
    user = options.userName

    if warn:
        warn = map(int,options.warn.split(','))
    crit = options.crit
    if crit:
        crit = map(int,options.crit.split(','))
    perf = options.perf
    verb = options.verb

    # Check for required "-H" option
    if host:
        pass
    else:
        fail("-H is a required argument")

    # Check for required "-M" option and verify value is supported
    if mode:
        if mode == "temp" or mode == "fans" or mode == "power" or mode == "volt":
            pass
        else:
            fail("-M only supports modes of temp, fans, power, volt")
    else:
        fail("-M is a required argument")

    # Check for required "-T" option
    if type:
        pass
    else:
        fail("-T is a required argument")
        
     # check for snmp version (we HAVE to have this to decide what to use)
    if vers:
        set_common_options(vers)
    else:
        fail("-V, SNMP version is a required argument")


    # Check for valid "-T" option and execute appropriate check
    if type == "cisco": 
        (desc, value) = check_cisco(host,comm,mode,verb,vers,secl,aprot,apass,eprot,epass,user)
        process_data(desc, map(int,value), warn, crit, perf)
    if type == "foundry": 
        (desc, value) = check_foundry(host,comm,mode,verb)
        process_data(desc, map(int,value), warn, crit, perf)
    if type == "hp":
        (desc, value) = check_hp(host,comm,mode,verb)
        process_data(desc, map(int,value), warn, crit, perf)
    if type == "juniper":
        (desc, value) = check_juniper(host,commu,mode,verb)
        process_data(desc, map(int,value), warn, crit, perf)
    else:
        fail("-T only supports types of cisco, foundry, hp, or juniper") 

    # Should never get here
    sys.exit(errors['UNKNOWN'])

# Execute main() function
if __name__ == "__main__":
	main()
