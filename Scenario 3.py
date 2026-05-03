# -*- coding: utf-8 -*-
"""
Created on Thu Jan 23 09:15:52 2025

@author: esatm
"""

import openrouteservice as ors
import csv

#Declaring variables
client = ors.Client(base_url='http://localhost:8080/ors')

#Variables for the statistics
lineNumber = 0
reachesByHelicopter = 0
cantReach = 0


#Open files. First file is source file for the LVO sites containing coordinates. Second file is the new file where travel times are being saved.
#Third file is a file containing helicopter traveling times
with open('C:/Insert_Your_Local_Directory_Here/coordinatesForLVO.csv', 'r') as coordinateFile:
    with open('C:/Insert_Your_Local_Directory_Here/resultsFile.csv', 'w', newline='') as timeResultsFile:
        with open('C:/Insert_Your_Local_Directory_Here/helicopterTimes.csv', 'r') as rendezvousSite:
            #Declare pointer for the reader. Set up the delimiter.
            coordinateReader = csv.reader(coordinateFile, delimiter=';')
            writer = csv.writer(timeResultsFile,delimiter=';')
            rendezvousReader = csv.reader(rendezvousSite, delimiter=';')
            
            
            #Skipataan ensimmäinen rivi
            kirjoittaja.writerow(next(koordinaattipisteLukija))
            next(kopteripisteLukija)
            
            #Copying the first line of coordinate file, which contains parameter names
            writer.writerow(next(coordinateReader))
            next(rendezvousReader)
            
            #Setting up  the constants
            #dispatchDelay = Delay from emergency call to ground unit starting engine.		
            dispatchDelay = 1.5
            #rooftopDelay = Delay transferring patient from helicopter to ED
            rooftopDelay = 12
            # groundUnitDelay = Delay transferring patient from ground unit to ED
            groundUnitDelay = 5
            #travelFactor = Ground unit travels 20 % faster with sirens on
            travelFactor = 0.8
            #onSceneTime = the time ground unit spends examining and loading patient on board
            onSceneTime = 20
            #helicopterDelay = Delay from the helicopter dispatch
            helicopterDelay = 6
            #transferDelay = delay of the patient transfer from ground unit to helicopter at rendezcvous point
            transferDelay = 8
            
            #Statistics for the limiting factor. 
            groundLimits = 0
            helicopterLimitsCounter = 0
            
            #Reading all the rendezvous points in one list called allCopterData
            
            allCopterData = []

            for copterLines in rendezvousReader:
                #Setting up the variables, defining them as 0
                routeChoice = {
                    "Xcoordinate": 0,
                    "Ycoordinate": 0,
                    "Coordinates": 0,
                    "FlyingFromBaseToRendez": 0,
                    "FlyingFromRendezToED": 0                        
                    }
                
                #Changing the variables for one route according to sourcefiles
                routeChoice["Xcoordinate"] = float(copterLines[13])
                routeChoice["Ycoordinate"] = float(copterLines[12])
                routeChoice["Coordinates"] =[float(copterLines[13]), float(copterLines[12])]
                routeChoice["FlyingFromBaseToRendez"] = float(copterLines[5])
                routeChoice["FlyingFromRendezToED"] = float(copterLines[8])
                
                #Saving route choice to list
                allCopterData.append(routeChoice)
                
            #Now that we have all the data, we can close the file
            rendezvousSite.close
            
            #Moving the rendezvouspoints coordinates to different list for easier access
            coordinates = []
            for line in allCopterData:
                coordinate = [line["Xcoordinate"], line["Ycoordinate"]]
                coordinates.append(coordinate)

            #Start to check line by line if we can reach Tays within 120 minutes
            for line in coordinateReader:
                
                #Setting up temporary time way over the average time. This fastestTime is needed for optimization
                fastestTime = 9999999
                helicopterLimits = False
                
                #From EMS station to LVO incident site with travelFactor
                groundUnitToLVOsite = float(line[16]) * 0.8
                
                #Setting up temporaryCoordinate variable, that original coordinates doesn't change
                tempCoordinates = coordinates.copy()
                
                #Saving LVO site coordinates from coordinates file
                coordinate = [line[15], line[14]]
                
                #Saving coordinate to tempCoordinates list
                tempCoordinates.append(coordinate)
                
                #Calling openRouteService matrix function Kutsutaan matrixia, jossa selvitellään pisteet, tapahtumapiste sijaitsee kohdassa 141
                matrix = client.distance_matrix(locations = tempCoordinates, destinations=[141], profile='driving-car',metrics=['duration'], units='km')
                
                #Increase the lineNumber calculator for the statistics
                lineNumber = lineNumber + 1
                
                #Changing seconds to minutes and multiply it with travelFactor
                for i in range(len(matrix["durations"])):
                    for j in range(len(matrix["durations"][i])):  #Matrix information is contained in list within a list, that's why 2 loops
                        matrix["durations"][i][j] = matrix["durations"][i][j] / 60 * travelFactor
                
                #Deleting travel route from LVO site to LVO site
                matrix["durations"].pop()
            
                #Start to go through the coordinates line by line
                for i in range(len(matrix["durations"])):
                    for j in range(len(matrix["durations"][i])):
                        
                        
                        #Checking if ground unit reaches LVO site in 120 minutes. If >120 minutes, route isn't suitable and continuing the loop
                        #If route EMS station->LVO site->Rendezvous site is already over 120 minutes, it takes too long
                        #Time is contains dipatchDelay, grounUnitToLVOsite, onSceneTime ja LVOsiteToRendezvous
                        #Summarizing values should be under 120 minutes
                        if(dispatchDelay + groundUnitToLVOsite + onSceneTime + matrix["durations"][i][j] > 120):
                            continue
                        
                        #If code reaches here, route from EMS station to rendezvous point via LVO site with all the constants are under 120 minutes
                        #Now we figure out the limiting factor. The code checks which unit (helicopter or ambulance) reaches rendezvous point first. 
                        #Ground unit time consist of dispatch delay, route to LVO site, onSceneTime, route to rendezvous site
                        #Helicopter time consist of helicopter dispatch delay and flight to rendezvous site
                        if(dispatchDelay + matrix["durations"][i][j]+ onSceneTime + groundUnitToLVOsite > helicopterDelay + allCopterData[i]["FlyingFromBaseToRendez"]):
                            
                            #If code reaches here, helicopter reaches first and ground unit is the limiting factor
                            #Now let's see if the patient reaches Tays with overall time.
                            #Overall time consist of dispatch delay, route to LVOsite, onSceneTime, LVO to rendezvous, transfer delay, flight to Tays, transferring patient to ED
                            #If overall time is under 120 minutes, patient reaches Tays within time limit
                            if(dispatchDelay + groundUnitToLVOsite + onSceneTime + matrix["durations"][i][j] + transferDelay + allCopterData[i]["FlyingFromRendezToED"] + rooftopDelay < 120):
                                
                                #See if current time is the fastest time
                                if( dispatchDelay + groundUnitToLVOsite + onSceneTime + matrix["durations"][i][j] + transferDelay + allCopterData[i]["FlyingFromRendezToED"] + rooftopDelay < fastestTime ):
                                    fastestTime = dispatchDelay + groundUnitToLVOsite + onSceneTime + matrix["durations"][i][j] + transferDelay + allCopterData[i]["FlyingFromRendezToED"] + rooftopDelay
                                    helicopterLimits = False
                        #Muuten käytetään kopterilla mentävää aikaa
                        
                        else:
                            #If code reaches here, ground unit reaches first and helicopter is the limiting factor
                            #Now let's see if the patient reaches Tays with overall time.
                            #Overall time consist of helicopter delay, flying from base to rendezvous, 
                            #transfer delay, flight to Tays, transferring patient to ED
                            #If overall time is under 120 minutes, patient reaches Tays within time limit
                            if( helicopterDelay + kaikkiKopteriTiedot[i]["LentoFtoK"] + transferDelay + allCopterData[i]["FlyingFromRendezToED"] + rooftopDelay < 120):
                                if( helicopterDelay + kaikkiKopteriTiedot[i]["LentoFtoK"] + transferDelay + allCopterData[i]["FlyingFromRendezToED"] + rooftopDelay < fastestTime ):
                                    fastestTime = helicopterDelay + kaikkiKopteriTiedot[i]["LentoFtoK"] + transferDelay + allCopterData[i]["FlyingFromRendezToED"] + rooftopDelay
                                    helicopterLimits = True

                #Add +1 to counters
                if( helicopterLimits == True ):
                    helicopterLimitsCounter += 1
                else:
                    groundLimits += 1
                    
                #Add data to row end
                line.append(fastestTime)
                line.append(helicopterLimits)
                #Write line
                kirjoittaja.writerow(line)
                
                #Print progress
                print(riviNumero/15521*100)
                
    #In the end, print out how many times helicopter and ground unit was limiting factor
    print("Helicopter was limiting factor in ", helicopterLimitsCounter, " cases")
    print("Ground unit was limiting factor in ", groundLimits, " cases")
                            
