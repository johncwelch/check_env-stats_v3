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
# v1.2 additions of Juniper support
# v1.3 addition of Juniper temp support

import os
import sys
from optparse import OptionParser

scriptversion = "1.3"

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
        common_options = "snmpwalk -OvQ -v 2c"
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
def check_foundry(hostname,community,mode,verbose,version,secLevel,authProt,authPass,encryptProt,encryptPass,userName):
    #command = common_options + " -c " + community + " " + hostname + " "
    
    #if check on version to build command
    if version == "2":
        command = common_options + " -c " + community + " " + hostname + " "
    elif version == "3":
        #gonna be a lot of checking in here. SO MANY IF STATMENTS
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
def check_hp(hostname,community,mode,verbose,version,secLevel,authProt,authPass,encryptProt,encryptPass,userName):
    fail("HP functions not yet implemented.")

# Function for Juniper equipment
#1 = Chassis Fram
#2 = PSU/PEM
#4 = FAN 
#6 = AEFB
#7 = FPIC
#8 = PIC
#9 = Routing Engine
#12 = CB
#20 = MIC

# use JNXMIBS tables? 
#cpu load avail
def check_juniper(hostname,community,mode,verbose,version,secLevel,authProt,authPass,encryptProt,encryptPass,userName):
     #if check on version to build command
    if version == "2":
        if mode == "temp":
        	  #the initial string for temp is different
            command = "snmpwalk -OQ -v 2c -m ALL -c " + community + " " + hostname + " " 
        else:
            #non-temp string
            command = common_options + " -c " + community + " " + hostname + " "
    elif version == "3":
        #gonna be a lot of checking in here. SO MANY IF STATMENTS
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
            #temp version
            if mode == "temp":
                command = "snmpwalk -OQ -v 3 -m ALL -l " + secLevel + " -u " + userName + " " + hostname + " "
     	  #non-temp version
            else:
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
            #temp version
            if mode == "temp":
                command = "snmpwalk -OQ -v 3 -m ALL -l " + secLevel + " -u " + userName + " -a " + authProt + " -A " + authPass + " " + hostname + " "
            #non-temp version
            else:
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
            #temp version
            if mode == "temp":
                command = "snmpwalk -OQ -v 3 -m ALL -l " + secLevel + " -u " + userName + " -a " + authProt + " -A " + authPass + " " + " -x " + encryptProt + " -X " + encryptPass + " " + hostname + " "
            else:    
                command = common_options + " -l " + secLevel + " -u " + userName + " -a " + authProt + " -A " + authPass + " " + " -x " + encryptProt + " -X " + encryptPass + " " + hostname + " "
     
        else:
            fail("Invalid seclevel, valid levels are: noAuthNoPriv, authNoPriv, authPriv")
            sys.exit()
            
    #corresponds to .iso.org.dod.internet.private.enterprises.juniperMIB.jnxMibs
    junosRootHardwareMIB = ".1.3.6.1.4.1.2636.3"
    
    if mode == "volt":
        fail("voltage table does not exist in Juniper's MIB.")
        
    if mode == "temp":
        junosTempListOID = junosRootHardwareMIB + ".1.13.1.7"
        #get a list of temp oids
        junosTempList = os.popen(command + junosTempListOID).read().split('\n')
       
        #delete the last blank line
        junosTempList = junosTempList[:-1]
        
        #create a temp list
        junosTempListFiltered = []
        #iterate through junosTempList
        for item in junosTempList:
        	  #if the item doesn't end in 0
        	  #note this has to be an equals, not endswith, since both 40 and 0 "end" in zero
        	  #but one is valid, the other is not.
            #split at " = "
            itemTest = item.split(" = ",1)[-1]
            #test for zero. since itemTest is actually a string/char
            #test it as an int
            if int(itemTest) != 0:
                #shove it on the end of the new list
                junosTempListFiltered.append(item)
        #check to see if there's no temps returned. If so, error our
        if len(junosTempListFiltered) == 0:
            fail("No components are returning temp data")
        #set the original list to the filtered list
        junosTempList = junosTempListFiltered
        
        #create individual lists
        splitList = []
        componentIDNum = []
        componentTemp = []
        
        #split initial return to get temp and component ID
        for item in junosTempList:
            #splitting on first period gets us the component ID and the temp
            #we also explicitly grab the last item, since that's what we care about
            itemSplit = item.split(".",1)[-1]
            #append last item to list
            splitList.append(itemSplit)
        
        for item in splitList:
            #we're going to iterate through splitList and shove the component ID into one list and the component temp into another
            #since you can split a string on a set of chars, not just one, we split on " = ", which gets rid of trailing/leading spaces
            #a thing that is rather convenient.

            #grab temp
            itemTemp = item.split(" = ",1)[-1]
            #grab component ID
            itemComp = item.split(" = ",1)[0]

            #shove temp in temp list
            componentTemp.append(itemTemp)

            #shove component ID in component ID list
            componentIDNum.append(itemComp)
        
        #now get the list of components. We delay this until now because if there's no valid temp readings, why do this at all?
        #list init
        junosComponentNameList = []
        junosComponentNameTmpList = []
        junosComponentNameListOID = junosRootHardwareMIB + ".1.13.1.5"
        #return list, split at newlines so it's not all just one massive string
        junosComponentNameTmpList = os.popen(command + junosComponentNameListOID).read().split('\n')
        #delete the last blank line
        junosComponentNameTmpList = junosComponentNameTmpList[:-1]
        
        #now, iterate through the component ID list. 
        #use enumerate to search the entire component tmp list at once. if we find the item, then append that index to the real list
        for item in componentIDNum:
            #this returns an index value NOT AN INT. If theItem from componentIDNum is in
            #junosComponentNameTmpList, then we get [int], else we get []
            theIndex = [i for i, compListItem in enumerate(junosComponentNameTmpList) if item in compListItem]
            #we don't want to append empty list items
            if theIndex != []:
                #grab the actual int value from the index. since theIndex will always only have
                #one value, we just grab the first one, aka item 0. Yes, I get there's a
                #Potential danger here of multiple matches, but for the snmp use case, 
                #that's not going to happen
                appendIndex = theIndex[0]
                #append junosComponentNameList with the appropriate item in junosComponentNameTmpList 
                #that matches the item in componentIDNum
                junosComponentNameList.append(junosComponentNameTmpList[appendIndex])
        
        #now we split the list so that we only have the component names, not the whole oid description
        #this will become the desc. Yes, ugly, but it works.
        
        #clear out junosComponentNameTmpList
        junosComponentNameTmpList = []
        
        for itemIndex,item in enumerate(junosComponentNameList):
        	junosComponentNameList[itemIndex] = item.split(" = ",1)[-1]
        
        #assign values to desc and valu for return
        desc = junosComponentNameList
        valu = componentTemp
        
        #account for verbose
        if verbose:
        	print(junosComponentNameListOID,desc,junosTempListOID,valu)
        	
        return(desc,valu)
        
        #for item in junosComponentNameList:
        #	itemTemp = item.split(" = ",1)[-1]
        
        
        
        #print("Component Temps")
        #for item in componentTemp:
        #    print(item)
        
        #print("Filtered component names")
        #for item in junosComponentNameList:
        #    print(item)
        
    if mode == "fans":
         #operating states:
			#unknown(1),	WARNING
			#running(2),	OK
			#ready(3),		WARNING?
			#reset(4),		CRITICAL
			#runningAtFullSpeed(5),	CRITICAL
			#down(6),		CRITICAL
			#standby(7)	OK
	   #build oids for count/descr/state
        junosFanCountOID = junosRootHardwareMIB + ".1.6.1.7.4"
        junosFanDescrOID = junosRootHardwareMIB + ".1.6.1.6.4"
        junosFanOperState = junosRootHardwareMIB + ".1.13.1.6.4"
        
        #run snmpwalk command, strip newline off of results
        #scalar value with the count of all fans on a given box
        junosFanCount = os.popen(command + junosFanCountOID).read().replace('\n', '')
        #scalar value describing fans
        junosFanDescr = os.popen(command + junosFanDescrOID).read().replace('\n', '')
        #ditch double quotes
        junosFanDescr = junosFanDescr.replace('\"', '')
        
        desc = os.popen(command + junosFanDescrOID).read()[:-1].replace('\"', '').split('\n')
        valu = os.popen(command + junosFanOperState).read()[:-1].replace('\"', '').split('\n')
        
        #if verbose is specified
        if verbose:
            print_verbose(junosFanDescrOID,desc,junosFanOperState,valu)
        
        #check for missing desc/valu (not implemented)
        if desc[0] == '' or valu[0] == '':
            fail("description / value table empty or non-existent.")
            
        #if there's more values than descr's, let's fix that 
        #this is going to happen a lot since desc is a scalar on the junipers
        descLength = len(desc)
        valuLength = len(valu)
        if descLength < valuLength:
            #get the number of descriptions we need to make it match
            loopCount = valuLength - descLength
            #loopCount = int(loopCount)
            
            #append a description onto the desc list so the lengths match
            for x in range(0,loopCount):
                desc.append(junosFanDescr)
        return(desc,valu)
        
        
    if mode == "power":
        #operating states:
			#unknown(1),	WARNING
			#running(2),	OK
			#ready(3),		WARNING?
			#reset(4),		CRITICAL
			#runningAtFullSpeed(5),	CRITICAL
			#down(6),		CRITICAL
			#standby(7)	OK
    #get count of PSU's
        junosPSUCountOID = junosRootHardwareMIB + ".1.6.1.7.2"
        junosPSUDescrOID = junosRootHardwareMIB + ".1.6.1.6.2"
        junosPSUOperState = junosRootHardwareMIB + ".1.13.1.6.2"
        #run snmpwalk command, strip newline off of results
        #scalar value with the count of all PSU's on a given box
        junosPSUCount = os.popen(command + junosPSUCountOID).read().replace('\n', '')
        #scalar value describing the PSUs
        junosPSUDescr = os.popen(command + junosPSUDescrOID).read().replace('\n', '')
        #get rid of the double quotes if we need it for an append.
        junosPSUDescr = junosPSUDescr.replace('\"', '')
        
        desc = os.popen(command + junosPSUDescrOID).read()[:-1].replace('\"', '').split('\n')
        #table values with operating state. this builds an array with each state as an element
        valu = os.popen(command + junosPSUOperState).read()[:-1].replace('\"', '').split('\n')
        
        #if verbose is specified
        if verbose:
            print_verbose(junosPSUDescrOID,desc,junosPSUOperState,valu)
        
        #check for missing desc/valu (not implemented)
        if desc[0] == '' or valu[0] == '':
            fail("description / value table empty or non-existent.")
        
        #if there's more values than descr's, let's fix that 
        #this is going to happen a lot since desc is a scalar on the junipers
        descLength = len(desc)
        valuLength = len(valu)
        if descLength < valuLength:
            #get the number of descriptions we need to make it match
            loopCount = valuLength - descLength
            #loopCount = int(loopCount)
            
            #append a description onto the desc list so the lengths match
            for x in range(0,loopCount):
                desc.append(junosPSUDescr)        
        
        return(desc,valu)
        
    #should never hit this
    sys.exit(errors['UNKNOWN'])
    #fail("Juniper functions not yet implemented.")

# Function to process data from SNMP tables
def process_data(description, value, warning, critical, performance,type,mode):
	string = ""
	status = "OK"
	perfstring = ""

	if critical and warning:
		if (type == "juniper") and (mode == "temp"):
			#warning and critical are lists, so...
			if int(critical[0]) <= int(warning[0]):
				fail("Warning value must be less than critical value")
			#list/tuple manipulation time
			#This will let us be a bit more specific in what we display as a value
			#combine description and value into list of tuples
			newList = zip(description,value)
			#convert to list of lists
			newList = [list(elem) for elem in newList]
			newListLength = len(newList)
			for item in newList:
				#check for critical first
				if int(item[-1]) >= int(critical[0]):
					#insert "CRITICAL" into item
					item.insert(0,'CRITICAL')
				#check for warning    
				elif int(item[-1]) >= int(warning[0]) and item[-1] < int(critical[0]):
					#insert warning
					item.insert(0,'WARNING')
				#it's all good    
				else:
					#insert OK
					item.insert(0,'OK')
                
			#output if there's no performance data
			if not performance:
			#print status text for each item and exit
				for index, item in enumerate(newList, start=1):
					print(item[0] + ": " + item[1] + " " + str(index) + ": " + str(item[2]))
			#we want perfdata
			else:
				#really the same as not, with a couple more steps
				for index,item in enumerate(newList, start=1):
					#get the normal output data
					regData = item[0] + ": " + item[1] + " " + str(index) + ": " + str(item[2])
					#build the perfdata string, no spaces in the name
					perfString = item[1].replace(' ','_') + "=" + str(item[2])
					#output both with a space bar space separator
					print(regData + " | " + perfString)
			
			#exit the script
			sys.exit(errors[status])
		#not temp AND juniper
		else:
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
		if type == "cisco":
			for d, v in zip(description,value):
				if len(string) != 0:
					string += ", "
				string += d + ": " + str(v)

			# Create performance data
			perfstring += d.replace(' ', '_') + "=" + str(v) + " "
             
		elif type == "juniper":
			#non-temp code
			if mode != "temp":
				#list/tuple manipulation time
				#This will let us be a bit more specific in what we display as a value
				#combine description and value into list of tuples
				newList = zip(description,value)
				#convert to list of lists
				newList = [list(elem) for elem in newList]
				newListLength = len(newList)
				#check status of item, insert result at beginning of item
				#operating states there as reference
				#operating states:
					#unknown(1),	WARNING
					#running(2),	OK
					#ready(3),	OK
					#reset(4),	CRITICAL
					#runningAtFullSpeed(5),	CRITICAL
					#down(6),		CRITICAL
					#standby(7)	OK
					#everything else	UNKNOWN
				for item in newList:
					if item[1] == 1:
						item.insert(0,'WARNING')
					elif item[1] == 2:
						item.insert(0,'OK')
					elif item[1] == 3:
						item.insert(0,'OK')
					elif item[1] == 4:
						item.insert(0,'CRITICAL')
					elif item[1] == 5:
						item.insert(0,'CRITICAL')
					elif item[1] == 6:
						item.insert(0,'CRITICAL')
					elif item[1] == 7:
						item.insert(0,'OK')
					else:
						item.insert(0,'UNKNOWN')
				 
				#output results without perfdata
				if not performance: 
					#print status text for each item and exit
					for index, item in enumerate(newList, start=1):
						print(item[0] + ": " + item[1] + " " + str(index) + ": " + str(item[2]))
			  
					sys.exit(errors[status])
			else:
				#list/tuple manipulation time
				#This will let us be a bit more specific in what we display as a value
				#combine description and value into list of tuples
				newList = zip(description,value)
				#convert to list of lists
				newList = [list(elem) for elem in newList]
				newListLength = len(newList)
				for item in newList:
					item.insert(0,'OK')
					print(item)
#			 
#				#output if there's no performance data
				if not performance:
				#print status text for each item and exit
					for index, item in enumerate(newList, start=1):
						print(item[0] + ": " + item[1] + " " + str(index) + ": " + str(item[2]))
				#there is perfdata requested
				else:
					#really the same as not, with a couple more steps
					for index,item in enumerate(newList, start=1):
						#get the normal output data
						regData = item[0] + ": " + item[1] + " " + str(index) + ": " + str(item[2])
						#build the perfdata string, no spaces in the name
						perfString = item[1].replace(' ','_') + "=" + str(item[2])
						#output both with a space bar space separator
						print(regData + " | " + perfString)

				#exit the script
				sys.exit(errors[status])
             
				#print(': '.join(description))
		elif type == "foundry":
			print type
		elif type == "hp":
			print type
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
    parser.add_option("-M", action="store", type="string", dest="mode", help="type of statistics to gather (temp,fans,power,volt) TEMPS IN CELSIUS")
    parser.add_option("-w", action="store", type="string", dest="warn", help="comma-seperated list of values at which to set warning. For Juniper temps, use a single integer")
    parser.add_option("-c", action="store", type="string", dest="crit", help="comma-seperated list of values at which to set critical. For Juniper temps, use a single integer")
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
    #added mode check, because for juniper, type is handled differently
    if type == "cisco": 
        (desc, value) = check_cisco(host,comm,mode,verb,vers,secl,aprot,apass,eprot,epass,user)
        process_data(desc, map(int,value), warn, crit, perf,type,mode)
    if type == "foundry": 
        (desc, value) = check_foundry(host,comm,mode,verb,vers,secl,aprot,apass,eprot,epass,user)
        process_data(desc, map(int,value), warn, crit, perf,type,mode)
    if type == "hp":
        (desc, value) = check_hp(host,comm,mode,verb,vers,secl,aprot,apass,eprot,epass,user)
        process_data(desc, map(int,value), warn, crit, perf,type,mode)
    if type == "juniper":
        (desc, value) = check_juniper(host,comm,mode,verb,vers,secl,aprot,apass,eprot,epass,user)
        process_data(desc, map(int,value), warn, crit, perf,type,mode)
    else:
        fail("-T only supports types of cisco, foundry, hp, or juniper") 

    # Should never get here
    sys.exit(errors['UNKNOWN'])

# Execute main() function
if __name__ == "__main__":
	main()
