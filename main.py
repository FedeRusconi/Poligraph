import time
from polygraph import Polygraph
#from multiprocessing import Process, Queue
from threading import Thread 

def prelim_questions():
    """
    Preliminary questions to gather the subjects name and destination of results.
    """    
    print("Welcome to the polygraph test")
    #Ask for name
    name = input("What is your name? ")
    #Ask for email
    email = input("What email address would you like the results sent to? ")
    #Initialize class of Polygraph
    global polygraph
    polygraph = Polygraph(name, email)
    #Set up raspi pins
    polygraph.pins_setup()
    

def polygraph_questions():
    """    
    Poligraph sequence of questions asked, wait for response through switch, determine truth or lie based on sensors' return values
    """    
    #Start questions
    print("We will begin by asking some preliminary questions to determine a baseline")
    #Retrieve initial base values from heartbeat and gsr sensors
    gsr_reading = {"base": polygraph.retrieve_values()[0]}
    hb_reading = {"base": polygraph.retrieve_values()[1]}
    # QT1 ask the subject obvious answer questions to determine baseline for comparison when asking real questions
    print("Is your name " + polygraph.user_name + "?")
    #Wait for a switch to be pressed
    while True:
        #Answer is YES
        if polygraph.detect_switch() == 'y':
            print("You answered YES")
            #Retrieve values from sensors right after answer given
            gsr_reading['value'] = polygraph.retrieve_values()[0]
            hb_reading['value'] = polygraph.retrieve_values()[1]
            #Assign values to class            
            polygraph.qt1_gsr = gsr_reading
            polygraph.qt1_hb = hb_reading
            #Sleep is necessary to give time for user to release button
            time.sleep(0.2)
            break
        #Answer is NO
        elif polygraph.detect_switch() == 'n':
            print("You answered NO. Please try again.")
            #Re ask question
            print("Is your name " + polygraph.user_name + "?")
            #Sleep is necessary to give time for user to release button
            time.sleep(0.2)

    #Retrieve initial base values from heartbeat and gsr sensors
    gsr_reading = {"base": polygraph.retrieve_values()[0]}
    hb_reading = {"base": polygraph.retrieve_values()[1]}
    #QT2 ask the subject obvious answer questions to determine baseline for comparison when asking real questions
    print("Have you ever been to Mars?")
    #Wait for a switch to be pressed
    while True:
        #Answer is YES
        if polygraph.detect_switch() == 'y':
            print("You answered YES. Try again.")
            #Re ask question
            print("Have you ever been to mars?")
            #Sleep is necessary to give time for user to release button
            time.sleep(0.2)
            
        #Answer is NO    
        elif polygraph.detect_switch() == 'n':
            print("You answered NO")
            #Retrieve values from sensors right after answer given
            gsr_reading['value'] = polygraph.retrieve_values()[0]
            hb_reading['value'] = polygraph.retrieve_values()[1]
            #Assign values to class
            polygraph.qt2_gsr = gsr_reading
            polygraph.qt2_hb = hb_reading
            #Sleep is necessary to give time for user to release button
            time.sleep(0.2)
            break
    
    #Retrieve initial base values from heartbeat and gsr sensors
    gsr_reading = {"base": polygraph.retrieve_values()[0]}
    hb_reading = {"base": polygraph.retrieve_values()[1]}
    #QT3 ask the subject obvious answer questions to determine baseline for comparison when asking real questions
    print("Are you in Australia at this moment?")
    #Wait for a switch to be pressed
    while True:
        #Answer is YES
        if polygraph.detect_switch() == 'y':
            print("You answered YES")
            #Retrieve values from sensors right after answer given
            gsr_reading['value'] = polygraph.retrieve_values()[0]
            hb_reading['value'] = polygraph.retrieve_values()[1]
            #Assign values to class
            polygraph.qt3_gsr = gsr_reading
            polygraph.qt3_hb = hb_reading
            #Calculate comparison values
            polygraph.calculate_test_mean()
            #Sleep is necessary to give time for user to release button
            time.sleep(0.2)
            break
        #Answer is NO    
        elif polygraph.detect_switch() == 'n':
            print("You answered NO. Please try again")
            #Re ask question
            print("Are you in Australia at this moment?")
            #Sleep is necessary to give time for user to release button
            time.sleep(0.2)
            
            
    #Ask actual polygraph questions - i holds index (starting from 1) q holds question
    for i, q in enumerate(polygraph.questions, 1):
        #Retrieve initial base values from heartbeat and gsr sensors
        gsr_reading = {"base": polygraph.retrieve_values()[0]}
        hb_reading = {"base": polygraph.retrieve_values()[1]}
        # Ask Question    
        print(q)
        #Wait for a switch to be pressed
        while True:
            #Answer is YES or NO
            if polygraph.detect_switch() == 'y' or polygraph.detect_switch() == 'n':
                #print response
                if polygraph.detect_switch()== 'y':
                    print("You answered YES")
                else:
                    print("You answered NO") 
                #Retrieve values from sensors right after answer given
                gsr_reading['value'] = polygraph.retrieve_values()[0]
                hb_reading['value'] = polygraph.retrieve_values()[1]
                #Construct key for class dictionary
                attr_name = 'q' + str(i)
                #Assign values to class
                polygraph.dict_results[attr_name] = {}
                polygraph.dict_results[attr_name]['gsr'] = gsr_reading
                polygraph.dict_results[attr_name]['hb'] = hb_reading
                #Compare results and determine if truth or lie
                polygraph.compare_results(polygraph.dict_results[attr_name], attr_name)
                #Turn either green or red light on
                polygraph.light_on(attr_name)
                #Sleep is necessary to give time for user to release button
                time.sleep(0.2)
                break
            
    #End message
    print("The test is over, thank you for participating.")
    #Stop monitoring and clean pins
    polygraph.poly_stop()
    #Send report via email
    polygraph.send_report()
    print("Please take a look at the graph to see the results.")
    #Show line graph
    polygraph.line_graph()    
    
def main():
    """
    Main function
    """
    #Preliminary Questions
    prelim_questions()
    #Following two threads will run in parallel
    #Start continuous monitoring
    Thread(target=polygraph.start_monitoring).start()
    #Start polygraph questions
    Thread(target=polygraph_questions).start()
        

#Start program
main()
        