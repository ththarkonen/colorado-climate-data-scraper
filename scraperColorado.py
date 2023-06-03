import chromedriver_autoinstaller
from selenium import webdriver
from bs4 import BeautifulSoup
import time
from scipy.io import savemat

chromedriver_autoinstaller.install()

chromeOptions = webdriver.ChromeOptions()
chromeOptions.add_argument('--incognito')
chromeOptions.add_argument('--headless')
driver = webdriver.Chrome( options = chromeOptions )


url = "https://climate.colostate.edu/data_access_new.html"
driver.get( url )

html = driver.page_source

soup = BeautifulSoup( html, 'html.parser')
options = soup.find_all("option")

stationIDs = []
previousID = ""
previousName = ""
previousLon = ""
previousLat = ""
previousElevation = ""

startingStationName = "AGATE 3 SW"
badStations = ["LIMON", "LIMON WSMO", "PAONIA 1 S"]

coloradoData = {}
keepSkipping = True

for option in options:

    stationID = option["value"]
    stationIDs.append( stationID )

    if( option.text == startingStationName ):
        keepSkipping = False

    if( keepSkipping or option.text in badStations ):
        continue

    coloradoData["id_" + stationID] = {}

    driver.execute_script("getMeta( arguments[0] );", stationID)

    html = driver.page_source
    soup = BeautifulSoup( html, 'html.parser')

    stationNotUpdated = True
    dataNotUpdated = True

    while( stationNotUpdated ):

        metadata = soup.find("p", {"id": "metadata"})

        try:

            stationContents = metadata.contents[0]
            stationName = stationContents.split(" ")[2:]
            stationName = " ".join( stationName )

            stationIdContents = metadata.contents[2]
            latLonContents = metadata.contents[4]
            elevationContents = metadata.contents[6]

            stationMetaID = stationIdContents.split(" ")[2]
            longitude = latLonContents.split(" ")[1]
            latitude = latLonContents.split(" ")[3]

            elevation = elevationContents.split(" ")[1]

            check = stationMetaID == previousID
            check = check or (longitude == previousLon and latitude == previousLat)

        except Exception as e:
            time.sleep(0.1)

            html = driver.page_source
            soup = BeautifulSoup( html, 'html.parser')
            continue

        if( check ):
            time.sleep(0.1)

            html = driver.page_source
            soup = BeautifulSoup( html, 'html.parser')
            continue
    
        print( [stationName, stationID, longitude, latitude, elevation] )

        previousID = stationID
        previousLon = longitude
        previousLat = latitude
        previousElevation = elevation
        stationNotUpdated = False

    while( dataNotUpdated ):

        driver.execute_script("quickGet('por')")

        html = driver.page_source
        soup = BeautifulSoup( html, 'html.parser')

        time.sleep(2)

        table = soup.find("div", {"id": "myModal"})
        tableData = soup.find_all("tr")
        
        tableVisible = "display: block" in table.get("style", "")

        if( tableVisible ):

            try:

                tableHeader = str( tableData[0] ).split("<th>")
                tableHeader = [ header.replace("</th>", "") for header in tableHeader]
                tableHeader = [ header.replace("</tr>", "") for header in tableHeader]
                tableHeader.pop(0)

                stationNameData = tableHeader[0]
                tableData = tableData[1:]

                coloradoData["id_" + stationID]["date"] = []
                coloradoData["id_" + stationID]["longitude"] = longitude
                coloradoData["id_" + stationID]["latitude"] = latitude
                coloradoData["id_" + stationID]["elevation"] = elevation
                
                coloradoData["id_" + stationID]["maxTemperature"] = []
                coloradoData["id_" + stationID]["minTemperature"] = []
                coloradoData["id_" + stationID]["precipitation"] = []
                coloradoData["id_" + stationID]["snow"] = []

                for row in tableData:
                    
                    row = str( row ).split("<td>")
                    row = [ item.replace("</td>", "") for item in row]
                    row = [ item.replace("</tr>", "") for item in row]
                    row.pop(0)

                    coloradoData["id_" + stationID]["date"].append( row[0] )
                    coloradoData["id_" + stationID]["maxTemperature"].append( row[1] )
                    coloradoData["id_" + stationID]["minTemperature"].append( row[2] )
                    coloradoData["id_" + stationID]["precipitation"].append( row[3] )
                    coloradoData["id_" + stationID]["snow"].append( row[4] )

            except:
                time.sleep(0.1)
                continue

        else:
            time.sleep(0.1)
            continue

        driver.execute_script("document.getElementById('myModal').style.display = 'none';")

        html = driver.page_source
        soup = BeautifulSoup( html, 'html.parser')

        print( tableHeader )
        print()

        previousName = stationNameData
        dataNotUpdated = False

    savemat("./coloradoData.mat", coloradoData)

