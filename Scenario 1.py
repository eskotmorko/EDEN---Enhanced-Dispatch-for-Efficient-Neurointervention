# -*- coding: utf-8 -*-
"""
Created on Thu Nov 28 21:30:25 2024

@author: esatm
"""


#Importing libraries
from geopy import distance
import openrouteservice as ors
import csv
from geopy.geocoders import Nominatim as napi


#Declaring ors variable
client = ors.Client(base_url='http://localhost:8080/ors')

#Geolocator for adresses
geolocator = napi(user_agent="Routesolver")

#Variables for statistics
cantReachAnywhere = 0
lineNumber = 0
numberOfLines = 67577

#Open the source file
with open('C:/Insert_Your_Local_Directory/Your_LVO_site_Data.csv', 'r') as siteFile:
    with open('C:/Insert_Your_Local_Directory/resultsFile.csv', 'w', newline='') as resultsFile:
        #Declare pointer and give delimiter
        dataReader = csv.reader(siteFile, delimiter=';')
        dataWriter = csv.writer(resultsFile,delimiter=';')
        
        
        #Skipping and writing the first line containing headers
        dataWriter.writerow(next(dataReader))
        
        
        for siteLine in dataReader:
            #Open EMS station file
            with open('C:/Insert_Your_Local_Directory/EMstationFile.csv', 'r') as stationFile:
                
                #Skip the header line
                next(stationFile)
                
                #Declare variable, set up the pointer and give delimiter
                stationReader = csv.reader(stationFile, delimiter=';')
                
                #Declaring route options
                routeOptions = []
                
                #In our data, LVO  site is in the 14th ja 15th column
                siteCoordinate = [ siteLine[14], siteLine[15] ]
            
                #Next we are going to find out which EMS station is the 3 closest
                for stationLines in stationReader:
                    
                    #Station coordinates are in column 3 and 4
                    stationCoordinates = [stationLines[4], stationLines[3]]
                    
                    #Etäisyys pisteen ja aseman välillä
                    distance = distance.distance( siteCoordinate, stationCoordinates ).km
                    
                    #Save the data in dict
                    routeOption = {
                        "length": distance,
                        "stationX": stationLines[4],
                        "stationY": stationLines[3]                        
                        }
                    
                    #If the number of route options are below 3, then the current one is considered one of the closest 3
                    if len(routeOptions) < 3:
                        routeOptions.append( routeOption )
                    else:
                        for routeNumber in routeOptions:  
                            #If the length is bigger than those that are saved, then continue
                            if distance > routeNumber["length"]:    
                                continue
                            #Else save current route, put them in order and pop back the last one
                            else:
                                
                                routeOptions.append(routeOption)
                                
                                routeOptions = sorted(routeOptions, key=lambda x: x["length"])
                                
                                routeOptions = routeOptions[:3]
                                
                                break
    
                #EMS station start points
                startPoints = [ (routeOptions[0]["stationX"], routeOptions[0]["stationY"]),
                     (routeOptions[1]["stationX"], routeOptions[1]["stationY"]),
                     (routeOptions[2]["stationX"], routeOptions[2]["stationY"])]
    
                
                #Destination 
                LVOdestination = ( siteLine[15], siteLine[14] )
    
                #Saving all the coordinates in one list
                allCoordinates = startPoints + [LVOdestination]
                
                #Calling the distance matrix to solve route durations
                matrix = client.distance_matrix(locations = allCoordinates, destinations=[3], profile='dLineng-car',metrics=['duration'],
                                                units='km')
                
                
                #Saving the route lenghts and delete route with itself
                routeLengths = matrix['durations']
                matrix["durations"].pop()
                
                #Increase lineNumber for the statistics
                lineNumber = lineNumber+1
                
                #Now we see if OpenRouteService can't calculate the road to LVO site
                if any(arvo is None for Line in routeLengths for arvo in Line):
                    cantReachAnywhere = cantReachAnywhere + 1
                #Else there is at least 1 road that can go from EM station to LVO site
                else:
                        
                    shortestTime = min(routeLengths)
                    shortestRouteIndex = routeLengths.index(shortestTime)
                    shortestStartingPoint = startPoints[shortestRouteIndex]
                    
                    #Change seconds to minutes
                    toMinutes = shortestTime / 60
                    
                    siteLine.append(toMinutes)
                    
                    #Now calculate route to Tays
                    TaysCoordinates = [(23.81334,61.50548)]
                    TaysRoute = TaysCoordinates + [LVOdestination]
                    TaysMatrix = client.distance_matrix( locations = TaysRoute, profile='dLineng-car',metrics=['duration'],
                                                    units='km')
                    TaysLength = max(TaysMatrix['durations'][0]) / 60
                    
                    siteLine.append(TaysLength)
                    
                    dataWriter.writerow( siteLine )
                    ready = float(lineNumber/numberOfLines) * 100
                    print(ready)
    
                    
print("There were total of " , cantReachAnywhere, "cases where route couldn't be calculated")