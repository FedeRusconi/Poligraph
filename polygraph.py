#Used for raspberry pi pins
import RPi.GPIO as GPIO
import Adafruit_MCP3008
#Time
import time
#For graph
import matplotlib.pyplot as plt
import numpy as np
#For emails
import smtplib

class Polygraph:
    """
    Class representing Polygraph test
    """
    
    #Set static attributes
    #Switches
    y_switch_pin = 23
    n_switch_pin = 24
    #Green light
    g_light_pin = 15
    #Red light
    r_light_pin = 14
    #Analog Digital Converter
    CLK = 11
    MISO = 9
    MOSI = 10
    CS = 8
    #Power to heartbeat and GSR
    sensors_pin = 18
    #Polygraph's questions
    questions = ["Has anyone in your household been diagnosed with COVID-19?",
                 "Is anyone in your household unwell and have symptoms related to COVID-19? This includes fever, coughing, sore throat or sneezing.",
                 "Is anyone in your household self-isolating, for example, because they have travelled recently?"]
    #Variable used for continuous monitoring
    monitor_on = True
    #Fault Tolerance
    fault_tolerance = 50
    #Storing credentials for gmail
    gmail_account = 'eng103.polygraph@gmail.com'
    gmail_pwd = 'pwd_12345'
    
    def __init__(self, subject_name, dest_email):
        """
        Constructor method
        :param subject_name: Name of subject undertaking polygraph test
        :param dest_email: Email of subject undertaking polygraph test
        """
        self.user_name = subject_name
        self.user_email = dest_email
        #Initialize empty lists for storing results
        self.heartbeat_list = []
        self.gsr_list = []
        self.dict_results = {}
    
        
    def pins_setup(self):
        """
        Set up Raspberry pi pins for sensors/actuators
        """
        GPIO.setmode(GPIO.BCM)
        #Set up pins for switches
        GPIO.setup(self.y_switch_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.n_switch_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        #Set up pins for lights
        GPIO.setup(self.g_light_pin, GPIO.OUT)
        GPIO.setup(self.r_light_pin, GPIO.OUT)
        #Set up ADC
        self.mcp = Adafruit_MCP3008.MCP3008(clk=self.CLK, cs=self.CS, miso=self.MISO, mosi=self.MOSI)
        #Set up power to sensors pin
        GPIO.setup(self.sensors_pin, GPIO.OUT)
        
        
    def poly_stop(self):
        """ Stop continuous monitoring and clean pins """
        #Stop monitoring
        self.monitor_on = False
        GPIO.output(self.sensors_pin, False)
        #Turn both lights off
        GPIO.output(self.g_light_pin, False)
        GPIO.output(self.r_light_pin, False)
        
        GPIO.cleanup
        
    
    def detect_switch(self):
        """
        Detect when a switch is pressed
        :return: "y" if YES button is pressed and "n" if NO button is pressed
        """
        #Store state of switches (False --> switch is pressed)
        y_switch_state = GPIO.input(self.y_switch_pin)
        n_switch_state = GPIO.input(self.n_switch_pin)
        #"YES" switch pressed
        if(y_switch_state == False):
            return "y"            
        #"NO" switch pressed
        if(n_switch_state == False):
            return "n"
        
    
    def start_monitoring(self):
        """
        Start sensors and keep monitoring values
        Channel 0 from ADC is GSR
        Channel 1 from ADC is heartbeat
        """
        GPIO.output(self.sensors_pin, True)
        while self.monitor_on == True:
            # Read values from sensors and append to list.
            self.gsr_list.append(self.mcp.read_adc(0))
            self.heartbeat_list.append(self.mcp.read_adc(1))
            #Wait before restarting sequence
            time.sleep(0.5)
            
    
    def retrieve_values(self):
        """
        Retrieve single values from gsr and heartbeat sensors
        :return: Tuple made of the single values from gsr and heartbeat sensors
        """
        #Read values
        gsr_value = self.mcp.read_adc(0)
        hb_value = self.mcp.read_adc(1)
        #Return values as a tuple
        tuple_values = (gsr_value, hb_value)
        
        return tuple_values
    
    
    def calculate_test_mean(self):
        """ Calculate mean of difference of values for test questions """
        #Mean difference gsr 
        values_gsr = self.qt1_gsr['value'] + self.qt2_gsr['value'] + self.qt3_gsr['value']
        bases_gsr = self.qt1_gsr['base'] + self.qt2_gsr['base'] + self.qt3_gsr['base']
        #Calculate mean and add tolerance for gsr and store in class
        self.mean_gsr = abs(values_gsr - bases_gsr) / 3 + self.fault_tolerance
        #Mean difference heartbeat
        values_hb = self.qt1_hb['value'] + self.qt2_hb['value'] + self.qt3_hb['value']
        bases_hb = self.qt1_hb['base'] + self.qt2_hb['base'] + self.qt3_hb['base']
        #Calculate mean and add tolerance for gsr and store in class
        self.mean_hb = abs(values_hb - bases_hb) / 3 + self.fault_tolerance
        
        
    def compare_results(self, actual, q_name):
        """
        Compare results with test results and determine if truth or lie
        :param actual: actual question's before and after values for the two sensors, type dictionary
        "param q_name: Attribute name (e.g. q1, q2, etc.), type string
        """
        #Find differences between values before and after question is asked
        gsr_diff = abs(actual['gsr']['value'] - actual['gsr']['base'])
        hb_diff = abs(actual['hb']['value'] - actual['hb']['base'])
        #If either one of the differences is higher than the test mean difference
        if gsr_diff > self.mean_gsr or hb_diff > self.mean_hb:
            #Anwer is a lie
            self.dict_results[q_name]['result'] = 'Lie'
            #Store average of two sensors' values for later comparisons
            self.lie_value = (actual['gsr']['value'] + actual['hb']['value']) / 2 - self.fault_tolerance
        #If both differences are less than test values
        else:
            #If a lie value exists
            if hasattr(self, "lie_value"):
                #Take the mean of actual values from two sensors
                actual_mean = (actual['gsr']['value'] + actual['hb']['value']) / 2
                #If actual meanis equal or higher than a previous lie
                if actual_mean >= self.lie_value:
                    #Answer is a lie
                    self.dict_results[q_name]['result'] = 'Lie'
                else:
                    #Answer is a truth
                    self.dict_results[q_name]['result'] = 'Truth'
            #If a lie value does not exist
            else:
                #Answer is a truth
                self.dict_results[q_name]['result'] = 'Truth'
                
                
    def light_on(self, key):
        """
        Turn either green or red light on
        :param key: name of key from question (e.g. q1, q2, etc.)
        """
        #Turn both lights off
        GPIO.output(self.g_light_pin, False)
        GPIO.output(self.r_light_pin, False)
        #If result of question is truth
        if self.dict_results[key]['result'] == 'Truth':
            #Turn green light on
            GPIO.output(self.g_light_pin, True)
        else:
            #Turn red light on
            GPIO.output(self.r_light_pin, True)
            
            
    def line_graph(self):
        """ Draw a two-line graph """
        
        #Define an array from 0 to number of values/2 with a 0.5 step for x-axis
        n_values = len(self.heartbeat_list)
        x = np.linspace(0, n_values/2, n_values)
        #Generate numpy arrays for graph y-axis
        y1 = np.array(self.heartbeat_list)
        y2 = np.array(self.gsr_list)
        #Set figure
        plt.figure(figsize=(8, 5))
        #Set title and labels
        plt.xlabel("Seconds")
        plt.title("Polygraph Results")
        #Set two lines
        plt.plot(x, y1, color='red', label='Heartbeat')
        plt.plot(x, y2, color='blue', label='GSR')        
        plt.legend()
        #Show graph
        plt.show()
        

    def send_report(self):
        """ Send test report to provided email """
        #Set up mail server
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.ehlo()
        #Login to mail server
        server.login(self.gmail_account, self.gmail_pwd)
        
        #Compose email
        subject = 'ENG103 - Polygraph Results'
        body = "Dear %s,\nThank you for completing our polygraph test.\nPlease see the test's results below:\n"%(self.user_name)
        
        #Add each question with result to body of email
        for i, q in enumerate(self.questions, 1):
            #Construct key for class dictionary
            attr_name = 'q' + str(i)
            
            body = body + '\nQ' + str(i) + ': ' + q + '\nResult: ' + self.dict_results[attr_name]['result'] + '\n'
            
        #Create structure of email (from,to,subject,body)
        email_text = 'From:%s\nTo:%s\nSubject:%s\n%s'%(self.gmail_account, self.user_email, subject, body)
        
        #Send email
        try:
            server.sendmail(self.gmail_account, self.user_email, email_text)
            server.close()
            print("Email sent to", self.user_email, "correctly")
        except:
            print("Something went wrong. Email not sent")