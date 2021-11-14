from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import numpy as np
import pandas as pd
import os

if __name__ == '__main__':

    root = os.getcwd()
    DRIVER_PATH = root + '/chromedriver'
    driver = webdriver.Chrome(executable_path=DRIVER_PATH)

    options = Options()
    options.headless = True
    options.add_argument("--window-size=1920,1200")

    # Get individual course reviews (these were the top 5 lowest retention rate courses)
    courses = ['CS-6210', 'CS-7641', 'CS-6601', 'CSE-6250', 'CS-6262']
    driver = webdriver.Chrome(options=options, executable_path=DRIVER_PATH)

    #Loop through courses and grab the reviews
    reviewList = []
    for course in courses:
        driver.get("https://omscentral.com/reviews?course={}".format(course))

        driver.implicitly_wait(3)

        for i in range(0, 60):
            driver.execute_script('window.scrollBy(0, 1000)')
            time.sleep(1)

        time.sleep(10)

        reviews = driver.find_elements_by_class_name('jss22')

        for review in reviews:
            textString = review.text.split('\n')
            if len(textString) > 6:
                reviewDict = dict(zip(['Class', 'DateTime', 'Review', 'Semester', 'Difficulty', 'Satisfaction', 'Workload'],
                                      [textString[0], textString[1], textString[2], textString[3],
                                       textString[4], textString[5], textString[len(textString)-1]]))
                reviewList.append(reviewDict)
            else:
                reviewDict = dict(zip(['Class', 'DateTime', 'Review', 'Semester', 'Difficulty', 'Satisfaction', 'Workload'],
                                      [textString[0], textString[1], textString[2], textString[3],
                                       textString[4], 'None', textString[len(textString)-1]]))
                reviewList.append(reviewDict)

    reviewDF = pd.DataFrame(reviewList)
    driver.quit()