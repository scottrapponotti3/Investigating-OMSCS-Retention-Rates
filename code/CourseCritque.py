# coding=utf8
import pandas as pd
import numpy as np
import scipy
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import json
import os
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import matplotlib
matplotlib.use('QT5Agg')
plt.plot()
plt.close()

if __name__ == '__main__':

    # IMPORTANT TO CHECK YOUR Browser Version to make sure it matches the chromedriver
    # This chromedriver version is for 95.0.4638.69
    root = os.getcwd()
    DRIVER_PATH = root + '/chromedriver'
    driver = webdriver.Chrome(executable_path=DRIVER_PATH)
    options = Options()
    options.headless = True
    options.add_argument("--window-size=1920,1200")

    # Get CSV file of the course critique classes
    # This file was manually collected for CS and ISYE courses that have both a traditional and online class
    # Course critique cannot be scraped using selenium since it is not housed as HTML
    courseCritique = pd.read_csv(os.path.normpath(root + os.sep + os.pardir)+'/data/CourseCritque.csv', encoding="utf-8")

    # Get overall course scores from OMS Reviews
    driver = webdriver.Chrome(options=options, executable_path=DRIVER_PATH)
    driver.get('https://omscentral.com/courses')
    elements = driver.find_elements_by_class_name('MuiTableRow-root')

    #Get list of courses to scrap then create a dataframe from results
    courses = list(np.unique(courseCritique.Class))
    courses = [x.replace(' ', '-') for x in courses]
    courseList = []
    for e in elements:
        e_text = e.text
        if e_text.split(' ')[0] in courses:
            id = e_text.split(' ')[0]
            diff = float(e_text.split('\n')[1])
            workload = float(e_text.split('\n')[2])
            sat = float(e_text.split('\n')[3])
            courseDict = dict(zip(['Class', 'Difficulty', 'Workload', 'Satisfaction'],
                                  [id, diff, workload, sat]))
            courseList.append(courseDict)
    courseData = pd.DataFrame(courseList)
    driver.quit()
    courseData['Class'] = [x.replace('-', ' ') for x in courseData['Class']]

    courseCritique = courseCritique[courseCritique['Size'].str.contains('Very Large')]
    courseCritique['isOnline'] = np.where(courseCritique.Section.isin(['O03', 'O01']), 1, 0)

    online = courseCritique[courseCritique.isOnline == 1].groupby(['Class'])['W%'].mean().reset_index().rename(columns = {'W%':'Retention_Online'})
    trad = courseCritique[courseCritique.isOnline == 0].groupby(['Class'])['W%'].mean().reset_index().rename(columns = {'W%':'Retention_Trad'})

    all = online.merge(trad, how = 'inner', on = 'Class')
    all = all.merge(courseData, how='left', on='Class')

    # Create density plots of traditional and online courses
    ax = sns.distplot(all.Retention_Online, label = 'Online')
    ax = sns.distplot(all.Retention_Trad, label = 'Trad')
    plt.xlabel('1-Retention Rate (%)')
    plt.ylabel('Density')
    plt.title('Online vs. Traditional Retention Rates')
    plt.legend(loc = 'best')
    plt.savefig('RetentionDist.png')

    # Create plots comparing traditional and online retention rates
    # Create plots of online traditional rates vs. workload and difficulty of courses
    fig = plt.figure(figsize=(13.5, 5.5))
    ax1 = fig.add_subplot(131)
    ax1.set_title('Trad vs. Online Retention', size=12)
    ax2 = fig.add_subplot(132)
    ax2.set_title('Online Retention vs. Workload', size=12)
    ax3 = fig.add_subplot(133)
    ax3.set_title('Online Retention vs. Difficulty', size=12)
    ax1.plot(all['Retention_Trad'], all['Retention_Online'], marker="o", linestyle="", alpha=0.8, markersize=5, color='black',
               markeredgecolor='none')
    m, b, r_value, p_value, std_err = scipy.stats.linregress(all['Retention_Trad'], all['Retention_Online'])
    ax1.plot(all['Retention_Trad'], m * all['Retention_Trad'] + b)
    ax1.text(5, 35, 'rsq = {}'.format(round(r_value, 3)), fontsize=11)
    ax1.text(5, 33.5, 'p-val = {}'.format(round(p_value, 2)), fontsize=11)
    ax1.set_xlabel('1-Traditional Retention Rate(%)')
    ax1.set_ylabel('1-Online Retention Rate(%)')

    ax2.plot(all['Retention_Online'], all['Workload'], marker="o", linestyle="", alpha=0.8, markersize=5, color='black',
             markeredgecolor='none')
    m, b, r_value, p_value, std_err = scipy.stats.linregress(all['Retention_Online'], all['Workload'])
    ax2.plot(all['Retention_Online'], m * all['Retention_Online'] + b)
    ax2.text(15, 27, 'rsq = {}'.format(round(r_value, 3)), fontsize=11)
    ax2.text(15, 26, 'p-val = {}'.format(round(p_value, 3)), fontsize=11)
    ax2.set_xlabel('1-Online Retention Rate(%)')
    ax2.set_ylabel('Workload (hrs/wk)')

    ax3.plot(all['Retention_Online'], all['Difficulty'], marker="o", linestyle="", alpha=0.8, markersize=5,
             color='black', markeredgecolor='none')
    m, b, r_value, p_value, std_err = scipy.stats.linregress(all['Retention_Online'], all['Difficulty'])
    ax3.plot(all['Retention_Online'], m * all['Retention_Online'] + b)
    ax3.text(30, 2.75, 'rsq = {}'.format(round(r_value, 3)), fontsize=11)
    ax3.text(30, 2.65, 'p-val = {}'.format(round(p_value, 3)), fontsize=11)
    ax3.set_xlabel('1-Online Retention Rate(%)')
    ax3.set_ylabel('Difficulty (1-5)')
    plt.tight_layout()
    plt.savefig('LinearRegPlots.png')

    # Get the top 5 classes in terms of retention rates
    # Create bar plot
    top5 = all.sort_values('Retention_Online', ascending=False).head()
    rt_Online = list(top5['Retention_Online'])
    rt_Trad = list(top5['Retention_Trad'])
    br1 = np.arange(len(rt_Online))
    barWidth = 0.25
    br2 = [x + barWidth for x in br1]
    br3 = [x + barWidth for x in br2]

    fig = plt.figure()
    plt.bar(br1, rt_Online, color='b', width=barWidth,
            edgecolor='grey', label='Online', alpha = 0.6)
    plt.bar(br2, rt_Trad, color='g', width=barWidth,
            edgecolor='grey', label='Traditional', alpha = 0.6)
    plt.xlabel('Courses')
    plt.ylabel('1-Retention Rate(%)')
    plt.title('Top 5 Lowest Online Retention Rates')
    plt.xticks([r + barWidth for r in range(len(rt_Online))],
               list(top5['Class']))
    plt.legend(loc = 'best')
    plt.savefig('HighDropRateBarPlot.png')

    # Run p-test to determine significance of difference in retention rate
    online['isOnline'] = 1
    trad['isOnline'] = 0
    both = pd.concat([online.rename(columns = {'Retention_Online':'Retention'}),
                      trad.rename(columns = {'Retention_Trad':'Retention'})])

    trueDiff = np.array(both.groupby(['isOnline'])['Retention'].mean())[0] - \
               np.array(both.groupby(['isOnline'])['Retention'].mean())[1]
    diffList = []
    n_iter = 10000
    for i in range(n_iter):
        all_copy = both.copy()
        y_rand = np.array(all_copy['isOnline'])
        np.random.shuffle(y_rand)
        all_copy['isOnline'] = y_rand
        diff = np.array(all_copy.groupby(['isOnline'])['Retention'].mean())[0] - \
                        np.array(all_copy.groupby(['isOnline'])['Retention'].mean())[1]
        diffList.append(diff)
    print(len(np.where(-1*trueDiff < diffList)[0])/len(diffList))

    # Analyze Survey Data
    # Copy and Paste Survey Data from Site to Python then write the file locally for analysis
    # surveyData = [{"id":"1626104557558","text":"Select your age:","answers":["50 - 64","30 - 39","40 - 49","18 - 29","18 - 29","18 - 29","30 - 39","30 - 39","18 - 29","18 - 29","40 - 49","30 - 39","18 - 29","18 - 29","18 - 29","30 - 39","40 - 49","18 - 29","18 - 29","30 - 39","30 - 39","30 - 39","18 - 29","18 - 29","18 - 29","18 - 29","40 - 49","40 - 49","18 - 29","18 - 29","18 - 29","40 - 49","30 - 39","18 - 29","30 - 39","18 - 29","18 - 29","30 - 39"]},{"id":"1626104575444","text":"Are you White, Black or African American, American Indian or Alaskan Native, Asian, Native Hawaiian or other Pacific Islander, or some other race?","answers":["African American","Other","White","White","White","White","Asian","White","White","White","Other","White","Other","White","White","White","Asian","American Indian or Alaskan Native","White","White","Other","Asian","Asian","White","Other","White","Other","Asian","White","White","White","White","White","Asian","Asian","White","Asian","White"]},{"id":"1626104950996","text":"What is your gender?","answers":["Male","Male","Male","Female","Female","Male","Female","Male","Female","Male","Male","Male","Male","Male","Male","Male","Female","Female","Female","Male","Male","Female","Female","Female","Female","Female","Male","Female","Female","Male","Female","Male","Male","Male","Female","Male","Male","Male"]},{"id":"1626104974867","text":"Are you married?","answers":["Yes","Yes","Yes","No","No","No","No","Yes","Yes","No","No","Yes","Yes","No","No","Yes","Yes","No","Yes","Yes","No","Yes","No","No","No","Yes","Yes","Yes","No","Yes","No","Yes","Yes","No","No","No","No","Yes"]},{"id":"1626104998715","text":"If you are employed how many hours do you work per week?","answers":["40-50","40-50","40-50","40-50","20-39","40-50","40-50","40-50","40-50","40-50","40-50","20-39","40-50","1-19","40-50","40-50","40-50","50+","40-50","50+","40-50","50+","","20-39","40-50","50+","40-50","40-50","40-50","40-50","40-50","40-50","","40-50","40-50","40-50","40-50","40-50"]},{"id":"1626105037244","text":"Are you enrolled in an online or traditional/blended graduate level program? ","answers":["Online","Online","Online","Online","Traditional/Blended","Online","Online","Online","Traditional/Blended","Online","Online","Online","Online","Online","Online","Online","Online","Online","Online","Online","Online","Online","Online","Online","Traditional/Blended","Online","Online","Online","Online","Online","Traditional/Blended","Online","Online","Online","Online","Online","Online","Online"]},{"id":"1626105078795","text":"What subject are you currently enrolled in (for example Computer Science)?","answers":["Computer Science / Machine Learning / Interactive Intelligence","Computer Science","Computer Science","Cybersecurity","Mathematics","Computer Science","computer science","HCI","Aerospace engineering ","Computer Science","Computer science ","Computer Science","Computer Science","Comp Sci","Computer Science","Computer Science","Computer Science","Biology","Computer Science ","Computer Science","Computer Science","Educational Technology CS6460","Computer Science","Computer Science - Educational Technology","Digital Media","Computer Science","Computer Science","Computer Science","Computer Science","Computer Science","Civil Engineering ","Data Analytics ","Computer Science","Computer Science ","EdTech","Computer Science","Computer Science","Computer Science"]},{"id":"1626105109801","text":"Before starting the program, had you taken classes on the subject matter before? ","answers":["Yes","Yes","Yes","Yes","Yes","Yes","No","Yes","Yes","Yes","Yes","Yes","Yes","Yes","Yes","Yes","Yes","No","Yes","Yes","Yes","No","No","Yes","Yes","Yes","Yes","No","Yes","Yes","No","Yes","Yes","Yes","Yes","Yes","Yes","Yes"]},{"id":"1626105133179","text":"Before starting the program, had you gained experience in the subject matter from work?","answers":["Yes","Yes","Yes","Yes","No","Yes","No","Yes","Yes","Yes","Yes","Yes","Yes","No","No","Yes","Yes","No","Yes","Yes","Yes","No","No","Yes","Yes","Yes","Yes","Yes","Yes","Yes","Yes","Yes","No","Yes","Yes","Yes","Yes","Yes"]},{"id":"1626105223092","text":"If yes to previous question, how many years of relevant work experience to your subject have you had?","answers":["10+ years","7 to 10 years","10+ years","4 to 7 years","","1 to 3 years","1 to 3 years","4 to 7 years","1 to 3 years","4 to 7 years","10+ years","10+ years","1 to 3 years","","","7 to 10 years","7 to 10 years","1 to 3 years","1 to 3 years","10+ years","1 to 3 years","","","1 to 3 years","1 to 3 years","1 to 3 years","10+ years","10+ years","1 to 3 years","1 to 3 years","1 to 3 years","1 to 3 years","","1 to 3 years","7 to 10 years","1 to 3 years","4 to 7 years","7 to 10 years"]},{"id":"1626105321739","text":"How many courses have you finished in your respective program?","answers":["7-10","4-6","7-10","1-3","4-6","1-3","4-6","7-10","1-3","1-3","1-3","4-6","4-6","1-3","1-3","7-10","7-10","1-3","7-10","7-10","4-6","4-6","1-3","7-10","1-3","1-3","1-3","4-6","1-3","7-10","10+","1-3","4-6","4-6","4-6","1-3","7-10","4-6"]},{"id":"1626105482960","text":"Do you feel there was enough communication or interaction between you and fellow students/instructors?","answers":["4","3","2","4","2","5","3","3","1","3","5","4","3","4","2","3","2","2","3","4","4","5","4","4","4","3","1","2","2","4","2","2","4","4","3","2","2","3"]},{"id":"1626105592894","text":"Did you feel higher satisfaction in courses with higher interaction with students and instructors?","answers":["3","4","4","4","5","5","5","4","4","4","4","5","3","4","4","5","3","4","4","5","4","3","5","5","5","5","5","3","5","3","5","2","4","4","4","5","4","5"]},{"id":"1626105621816","text":"Did you feel engaged and motivated in the courses in your program? ","answers":["5","3","4","4","3","5","3","4","2","4","4","4","4","3","3","4","4","3","4","4","4","5","4","4","4","4","2","4","3","4","4","4","5","4","4","4","3","3"]},{"id":"1626105638101","text":"Were you able to stay focused during lectures and/or help sessions? ","answers":["4","3","4","3","2","3","4","4","2","4","4","3","3","4","2","3","4","3","4","3","3","4","4","4","4","3","3","4","2","3","2","4","4","4","4","3","4","4"]},{"id":"1626105652893","text":"Were there enough support systems in place in your courses if you had questions or needed help with assignments?","answers":["4","4","4","3","4","5","4","4","2","3","4","4","4","4","3","3","4","4","4","3","3","3","2","3","3","4","2","4","2","5","2","3","4","4","4","4","4","4"]},{"id":"1626105793308","text":"Which of the following means of course engagement would you prefer? (Select all that apply)","answers":["Other","Weekly quizzes;Weekly status checks with instructors/TAs;Discussion boards to ask questions for instructors and other students;Detailed feedback from instructors/TAs on assignments","Weekly status checks with instructors/TAs;Discussion boards to ask questions for instructors and other students;Detailed feedback from instructors/TAs on assignments","Weekly quizzes;Weekly status checks with instructors/TAs;Detailed feedback from instructors/TAs on assignments","Weekly quizzes;Detailed feedback from instructors/TAs on assignments","Discussion boards to ask questions for instructors and other students;Detailed feedback from instructors/TAs on assignments;Other","Weekly quizzes;Weekly status checks with instructors/TAs;Discussion boards to ask questions for instructors and other students;Detailed feedback from instructors/TAs on assignments","Discussion boards to ask questions for instructors and other students","Detailed feedback from instructors/TAs on assignments;Other","Discussion boards to ask questions for instructors and other students;Detailed feedback from instructors/TAs on assignments","Discussion boards to ask questions for instructors and other students;Detailed feedback from instructors/TAs on assignments;Other","Discussion boards to ask questions for instructors and other students;Detailed feedback from instructors/TAs on assignments","Other","Weekly status checks with instructors/TAs;Discussion boards to ask questions for instructors and other students;Detailed feedback from instructors/TAs on assignments","Detailed feedback from instructors/TAs on assignments","Weekly status checks with instructors/TAs;Discussion boards to ask questions for instructors and other students;Detailed feedback from instructors/TAs on assignments","Weekly quizzes;Weekly status checks with instructors/TAs;Detailed feedback from instructors/TAs on assignments","Weekly quizzes;Discussion boards to ask questions for instructors and other students;Detailed feedback from instructors/TAs on assignments","Discussion boards to ask questions for instructors and other students","Discussion boards to ask questions for instructors and other students;Detailed feedback from instructors/TAs on assignments","Weekly status checks with instructors/TAs;Detailed feedback from instructors/TAs on assignments","Detailed feedback from instructors/TAs on assignments;Other","Detailed feedback from instructors/TAs on assignments","Discussion boards to ask questions for instructors and other students;Detailed feedback from instructors/TAs on assignments","Weekly status checks with instructors/TAs;Discussion boards to ask questions for instructors and other students","Weekly status checks with instructors/TAs;Discussion boards to ask questions for instructors and other students;Detailed feedback from instructors/TAs on assignments","Weekly status checks with instructors/TAs","Weekly quizzes;Weekly status checks with instructors/TAs;Discussion boards to ask questions for instructors and other students;Detailed feedback from instructors/TAs on assignments","Discussion boards to ask questions for instructors and other students;Detailed feedback from instructors/TAs on assignments","Weekly status checks with instructors/TAs;Discussion boards to ask questions for instructors and other students;Detailed feedback from instructors/TAs on assignments;Other","Weekly status checks with instructors/TAs;Detailed feedback from instructors/TAs on assignments","Discussion boards to ask questions for instructors and other students;Detailed feedback from instructors/TAs on assignments;Other","Discussion boards to ask questions for instructors and other students","Discussion boards to ask questions for instructors and other students;Detailed feedback from instructors/TAs on assignments","Weekly quizzes;Weekly status checks with instructors/TAs","Discussion boards to ask questions for instructors and other students;Detailed feedback from instructors/TAs on assignments","Discussion boards to ask questions for instructors and other students;Detailed feedback from instructors/TAs on assignments","Weekly quizzes;Weekly status checks with instructors/TAs;Discussion boards to ask questions for instructors and other students;Detailed feedback from instructors/TAs on assignments"]},{"id":"1626105894334","text":"What was the reason(s) for satisfaction in your program’s courses? (Select all that apply)","answers":["Course was challenging;Good communication with TAs/instructors;Enjoyed the course structure (ie. projects, tests, number of HW assignments);Other","Course’s material had real world value;Good communication with TAs/instructors","Course’s material had real world value;Course was challenging;Good communication with TAs/instructors;Enjoyed the course structure (ie. projects, tests, number of HW assignments)","Course’s material had real world value;Course was challenging;Enjoyed the course structure (ie. projects, tests, number of HW assignments)","Course was challenging;Enjoyed the course structure (ie. projects, tests, number of HW assignments)","Course’s material had real world value;Course was challenging;Good communication with TAs/instructors;Enjoyed the course structure (ie. projects, tests, number of HW assignments)","Course’s material had real world value;Good communication with TAs/instructors","Course’s material had real world value;Enjoyed the course structure (ie. projects, tests, number of HW assignments)","Good communication with TAs/instructors;Enjoyed the course structure (ie. projects, tests, number of HW assignments)","Course’s material had real world value;Course was challenging","Course’s material had real world value;Course was challenging;Good communication with TAs/instructors;Enjoyed the course structure (ie. projects, tests, number of HW assignments);Other","Course’s material had real world value;Good communication with TAs/instructors;Enjoyed the course structure (ie. projects, tests, number of HW assignments)","Enjoyed the course structure (ie. projects, tests, number of HW assignments)","Course’s material had real world value;Good communication with TAs/instructors;Enjoyed the course structure (ie. projects, tests, number of HW assignments)","Course’s material had real world value;Good communication with TAs/instructors;Enjoyed the course structure (ie. projects, tests, number of HW assignments)","Course’s material had real world value;Course was challenging;Good communication with TAs/instructors","Course was challenging;Enjoyed the course structure (ie. projects, tests, number of HW assignments)","Course’s material had real world value;Course was challenging;Good communication with TAs/instructors","Course’s material had real world value","Course was challenging;Enjoyed the course structure (ie. projects, tests, number of HW assignments)","Course’s material had real world value;Course was challenging;Good communication with TAs/instructors;Enjoyed the course structure (ie. projects, tests, number of HW assignments)","Course’s material had real world value;Course was challenging;Good communication with TAs/instructors;Enjoyed the course structure (ie. projects, tests, number of HW assignments)","Course’s material had real world value;Good communication with TAs/instructors;Enjoyed the course structure (ie. projects, tests, number of HW assignments)","Course’s material had real world value;Good communication with TAs/instructors","Course’s material had real world value;Course was challenging;Good communication with TAs/instructors;Enjoyed the course structure (ie. projects, tests, number of HW assignments)","Good communication with TAs/instructors;Enjoyed the course structure (ie. projects, tests, number of HW assignments)","Course was challenging;Good communication with TAs/instructors;Enjoyed the course structure (ie. projects, tests, number of HW assignments)","Course’s material had real world value;Course was challenging;Good communication with TAs/instructors;Enjoyed the course structure (ie. projects, tests, number of HW assignments)","Course’s material had real world value;Course was challenging;Good communication with TAs/instructors","Course’s material had real world value;Good communication with TAs/instructors;Enjoyed the course structure (ie. projects, tests, number of HW assignments)","Other","Course’s material had real world value;Course was challenging;Good communication with TAs/instructors;Enjoyed the course structure (ie. projects, tests, number of HW assignments)","Course was challenging;Enjoyed the course structure (ie. projects, tests, number of HW assignments)","Course’s material had real world value;Course was challenging","Good communication with TAs/instructors","Course’s material had real world value;Good communication with TAs/instructors;Enjoyed the course structure (ie. projects, tests, number of HW assignments)","Course’s material had real world value;Good communication with TAs/instructors;Enjoyed the course structure (ie. projects, tests, number of HW assignments)","Course’s material had real world value;Course was challenging;Good communication with TAs/instructors"]},{"id":"1626105969443","text":"Have you ever dropped a class in your program?","answers":["Yes","Yes","Yes","Yes","Yes","Yes","Yes","No","Yes","No","Yes","Yes","Yes","Yes","No","Yes","Yes","No","No","Yes","No","Yes","No","No","No","No","Yes","No","No","No","Yes","Yes","Yes","No","Yes","No","Yes","Yes"]},{"id":"1626105994076","text":"If yes, did you enjoy the class that you dropped?","answers":["Yes","No","Yes","Yes","No","Yes","Yes","No","Yes","","No","No","Yes","No","","No","No","No","","Yes","No","Yes","","","Yes","","No","No","","","No","No","Yes","","Yes","","No","Yes"]},{"id":"1626106015516","text":"If yes, what was the reason(s) for dropping out of a class? (Select all that apply)","answers":["Did not have enough time;Low cost penalty for dropping;Personal issue came up;Did not enjoy the structure of the class;Other","Did not have enough time;Personal issue came up;Did not enjoy the material;Did not enjoy the structure of the class;Was not prepared/not doing well","Did not have enough time;Personal issue came up;Was not prepared/not doing well","Did not have enough time;Was not prepared/not doing well","Did not have enough time;Did not enjoy the material;There was little engagement or feedback from instructors or TA;Did not enjoy the structure of the class","Did not have enough time","Was not prepared/not doing well","Other","Personal issue came up;Other","","Did not have enough time;Did not enjoy the material;Was not prepared/not doing well;Other","Did not enjoy the material;Did not enjoy the structure of the class","Did not have enough time;Personal issue came up;Did not enjoy the structure of the class","","","Low cost penalty for dropping;Did not enjoy the material;There was little engagement or feedback from instructors or TA;Did not enjoy the structure of the class","","Personal issue came up","","Did not have enough time;Personal issue came up","","Did not have enough time;Personal issue came up","","","","","Did not enjoy the material;There was little engagement or feedback from instructors or TA;Did not enjoy the structure of the class;Was not prepared/not doing well;Other","","","","There was little engagement or feedback from instructors or TA;Did not enjoy the structure of the class","Did not have enough time;Low cost penalty for dropping;Personal issue came up;Did not enjoy the material;Did not enjoy the structure of the class;Was not prepared/not doing well","Did not have enough time;Personal issue came up","","Did not have enough time","","Did not have enough time;Low cost penalty for dropping;Personal issue came up;Did not enjoy the material","Did not have enough time"]}]
    # with open('surveyData.json', 'w') as json_file:
    #     json.dump(surveyData, json_file)

    # Opening JSON file that contains responses to student survey
    f = open(os.path.normpath(root + os.sep + os.pardir)+'/data/surveyData.json')

    # returns JSON object as a dictionary
    surveyData = json.load(f)

    # Create Bar Plots visualizing the background of students
    fig = plt.figure(figsize=(12.5, 9.5))
    gs = GridSpec(ncols=2, nrows=2, figure=fig)
    ax_1 = fig.add_subplot(gs[0,0])
    ax_1.set_title('% Students in Online/Trad')
    ax_2 = fig.add_subplot(gs[0,1])
    ax_2.set_title('% CS Students')
    ax_3 = fig.add_subplot(gs[1,0])
    ax_3.set_title('% Students with Prior Work Exp')
    ax_4 = fig.add_subplot(gs[1,1])
    ax_4.set_title('% Students Working')

    for survey in surveyData:
        if survey['id'] == '1626105223092':
            for idx, s in enumerate(survey['answers']):
                if s == '':
                    survey['answers'][idx] = '0'
                else:
                    survey['answers'][idx] = survey['answers'][idx].replace(' years', '')

            unique, count = np.unique(survey['answers'], return_counts=True)
            idx = np.where(unique == '10+')[0][0]
            val, c = unique[2], count[2]
            unique, count = list(unique), list(count)
            unique.remove(val)
            unique.append(val)
            count.remove(c)
            count.append(c)
            count = list(count / np.sum(count))

            ax_3.bar(unique, count, color='b', width=0.7,
                    edgecolor='black', alpha=0.6)
            ax_3.set_xlabel('Years Work Experience')
            ax_3.set_ylabel('Percentage Response')

        elif survey['id'] == '1626105037244':
            unique, count = np.unique(survey['answers'], return_counts=True)
            count = list(count / np.sum(count))
            ax_1.bar(unique, count, color='g', width=0.2,
                    edgecolor='grey', alpha=0.6)
            ax_1.set_xlabel('Program')
            ax_1.set_ylabel('Percentage Response')

        elif survey['id'] == '1626105078795':
            for idx, s in enumerate(survey['answers']):
                if 'Computer ' in s or s == 'Comp Sci' or s == 'HCI' or s == 'Cybersecurity' or 'Educational Technology' in s:
                    survey['answers'][idx] = 'Computer Science'
                else:
                    survey['answers'][idx] = 'Other'

            unique, count = np.unique(survey['answers'], return_counts=True)
            count = list(count / np.sum(count))
            ax_2.bar(unique, count, color='r', width=0.2,
                    edgecolor='black', alpha=0.6)
            ax_2.set_xlabel('Marriage Status')
            ax_2.set_ylabel('Percentage Response')

        elif survey['id'] == '1626104998715':
            for idx, s in enumerate(survey['answers']):
                if s == '':
                    survey['answers'][idx] = '0'

            unique, count = np.unique(survey['answers'], return_counts=True)
            count = list(count / np.sum(count))
            ax_4.bar(unique, count, color='orange', width=0.7,
                     edgecolor='grey', alpha=0.6)
            ax_4.set_xlabel('Number Working Hours/Week')
            ax_4.set_ylabel('Percentage Response')

        else:
            pass

    plt.tight_layout()
    plt.savefig('Background_BarPlot.png')

    # Create Bar Plots visualizing the results of 1-5 levels of students
    fig = plt.figure(figsize=(15.5, 9.5))
    gs = GridSpec(ncols=2, nrows=2, figure=fig)
    ax_1 = fig.add_subplot(gs[0, 0])
    ax_1.set_title('Interaction with Students/Teacher',size = 14)
    ax_2 = fig.add_subplot(gs[0, 1])
    ax_2.set_title('Satisfaction when High Interaction',size = 14)
    ax_3 = fig.add_subplot(gs[1, 0])
    ax_3.set_title('Course Engagement/Motivation',size = 14)
    ax_4 = fig.add_subplot(gs[1, 1])
    ax_4.set_title('Support Systems for Students',size = 14)
    # ax_5 = fig.add_subplot(gs[1, 1])
    # ax_5.set_title('% Students Working')
    labels = ['Strongly Disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly Agree']
    for survey in surveyData:
        unique, count = np.arange(5) + 1, np.zeros(5)
        for idx, n in enumerate(unique):
            count[idx] = len(np.where(np.array(survey['answers']) == str(n))[0])
        count = list(count / np.sum(count))
        if survey['id'] == '1626105482960':
            ax_1.bar(labels, count, color='g', width=0.4,
                     edgecolor='black', alpha=0.6)
            ax_1.set_ylabel('Percentage Response',size = 14)
            ax_1.set_ylim([0, 0.7])
        elif survey['id'] == '1626105592894':
            ax_2.bar(labels, count, color='b', width=0.4,
                     edgecolor='black', alpha=0.6)
            ax_2.set_ylim([0, 0.7])
        elif survey['id'] == '1626105621816':
            ax_3.bar(labels, count, color='r', width=0.4,
                     edgecolor='black', alpha=0.6)
            ax_3.set_ylabel('Percentage Response',size = 14)
            ax_3.set_ylim([0, 0.7])
        elif survey['id'] == '1626105652893':
            ax_4.bar(labels, count, color='orange', width=0.4,
                     edgecolor='black', alpha=0.6)
            ax_4.set_ylim([0, 0.7])
        else:
            pass

    plt.tight_layout()
    plt.savefig('Satisfaction_BarPlot.png')

    q16 = {'Weekly quizzes':0,
           'Weekly status checks with instructors/TAs':0,
           'Discussion boards to ask questions for instructors and other students':0,
           'Detailed feedback from instructors/TAs on assignments':0,
           'Other':0}
    q17 = {'Course’s material had real world value': 0,
           'Course was challenging': 0,
           'Good communication with TAs/instructors': 0,
           'Enjoyed the course structure (ie. projects, tests, number of HW assignments)': 0,
           'Other': 0}
    fig = plt.figure(figsize=(20.5, 9.5))
    gs = GridSpec(ncols=2, nrows=1, figure=fig)
    ax_1 = fig.add_subplot(gs[0, 0])
    ax_1.set_title('Student Course Engagement Preference', size = 14)
    ax_2 = fig.add_subplot(gs[0, 1])
    ax_2.set_title('Student Course Satisfaction Preference',size = 14)

    for survey in surveyData:
        if survey['id'] == '1626105793308':
            for responses in survey['answers']:
                for response in responses.split(';'):
                    q16[response] += 1

        elif survey['id'] == '1626105894334':
            for responses in survey['answers']:
                for response in responses.split(';'):
                    q17[response] += 1

        else:
            pass

    ax_1.bar(['Quizzes', 'TA Status Check', 'Discussion Boards', 'Feedback from TA', 'Other'],
             list(np.array(list(q16.values()))/len(survey['answers'])), color='green', width=0.4,
             edgecolor='black', alpha=0.6)
    ax_1.set_ylabel('Percentage Response', size = 12)
    ax_1.set_xticklabels(['Quizzes', 'TA Status Check',
                          'Discussion Boards', 'Feedback from TA', 'Other'],
                         rotation=15)
    ax_1.set_ylim([0, 1])

    ax_2.bar(['Interesting Material', 'Challenging Course', 'Communication with TA', 'Good Course Structure', 'Other'],
             list(np.array(list(q17.values())) / len(survey['answers'])), color='blue', width=0.4,
             edgecolor='black', alpha=0.6)
    ax_2.set_ylabel('Percentage Response', size = 12)
    ax_2.set_xticklabels(['Interesting Material', 'Challenging Course',
                          'Communication with TA', 'Good Course Structure', 'Other'],
                         rotation=15)
    ax_2.set_ylim([0, 1])

    dropPercent = np.sum(np.array(surveyData[18]['answers']) == 'Yes')/len(surveyData[18]['answers'])

    enjoyPercent = np.sum(np.array(surveyData[19]['answers']) == 'Yes') / \
                   (len(surveyData[19]['answers']) - np.sum(np.array(surveyData[19]['answers']) == ''))

    q20 = {'Did not have enough time': 0,
           'Low cost penalty for dropping': 0,
           'Did not enjoy the material': 0,
           'There was little engagement or feedback from instructors or TA': 0,
           'Personal issue came up': 0,
           'Did not enjoy the structure of the class': 0,
           'Was not prepared/not doing well':0,
           'Other': 0}

    for responses in surveyData[20]['answers']:
        for response in responses.split(';'):
            if response != '':
                q20[response] += 1

    for key, value in q20.items():
        q20[key] = value/np.sum(np.array(surveyData[20]['answers']) != '')

    plt.savefig('DropResults_BarPlot.png')
