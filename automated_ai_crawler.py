import networkx as nx
import gravis as gv
import openai
import re
import tiktoken
import random
from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from urllib.request import urljoin
from urllib.request import urlparse
from selenium.webdriver.support import expected_conditions as EC
from networkx.drawing.nx_agraph import write_dot, graphviz_layout
from node import Node as node
from selenium.common.exceptions import StaleElementReferenceException as SE, ElementClickInterceptedException, TimeoutException, NoSuchElementException,ElementNotInteractableException, ElementNotVisibleException
from selenium.webdriver.support.wait import WebDriverWait 
from button import Button as button
from bs4 import BeautifulSoup
import time



openai.api_key = "insert your API KEY here"
#set colori
color_button = 'green'
color_states = 'blue'
color_link = 'orange'
color_ext_link = 'red'
# Set for storing unique states
states = {}
all_link = list()
# Set for storing urls with same domain
links_intern = set()
links_button_intern = set()
# Set for storing urls with different domain
links_extern = set()
# Set for storing broken urls 
links_broken = set()

chrome_options = Options()
chrome_options.add_argument("--headless")


color_map = []
button_number = 0

Count = 0 
temp_driver = webdriver.Chrome (options=chrome_options)

alert = gv.convert.image_to_data_url("/home/sbam/Desktop/progetto_sicurezza/alert.png")
def increment():
    global Count
    Count += 1 

def find_button (driver, node): # metodo per la ricerca dei bottoni
    input_list = []
    global button_number
    url = node.get_domain()
    body_soup = str(driver.find_element(By.TAG_NAME,'body').get_attribute("outerHTML"))
    body_html= BeautifulSoup(body_soup, features="lxml")
    for tag in body_html.find_all("script"): body_html.script.decompose()
    body = body_html.decode()
    try :
        input_elements = driver.find_elements(By.TAG_NAME, 'button')
        input_list  = driver.find_elements(By.TAG_NAME, 'input')
        
        for e in input_list:
             type = e.get_attribute("type")
             
             if type == "submit" or type == "button":               
                location = e.location
                x= location.get('x')
                y= location.get('y')
                button_number += 1
                new_button = button(url, hash(url + body ),x, y, type)             
                node.add_generic_button(new_button)
                 
        for e in input_elements:                    
            
            location = e.location 
            x= location.get('x')
            y= location.get('y')
            button_number += 1    
            new_button = button(url, hash( url + body),x, y, type)            
            
            node.add_generic_button(new_button)      
    except:
         print("errore")
         node.set_buttons([])        
    
    return node 

def test_status(driver, url):
    status = 400
    for request in driver.requests:
        if request.response and request.url == url:
            status = request.response.status_code
    return status

def test_button(button):
    
    driver_for_button =  webdriver.Chrome (options=chrome_options)
    url = button.getUrl()  
    driver_for_button.get(url)
    found = False
    
    try :
        input_elements = driver_for_button.find_elements(By.TAG_NAME, 'button')
        input_list  = driver_for_button.find_elements(By.TAG_NAME, 'input')
                
        if input_list != []:
         for e in input_list :
            if found == False:
             type = e.get_attribute("type")
             
             if type == "submit" or type == "button":
                
                location = e.location
                x= location.get('x')
                y= location.get('y')
                if x == button.getX() and y == button.getY():
                    #trovato il button nella pagina
                    #provo a cliccarlo
                    found = True   
                    old_id = button.getId()
                    temp_driver = driver_for_button
                    e.click()  
                    driver_for_button.refresh
                    newUrl = driver_for_button.current_url
                    body_soup = str(driver_for_button.find_element(By.TAG_NAME,'body').get_attribute("outerHTML"))
                    body_html= BeautifulSoup(body_soup, features="lxml")
                    for tag in body_html.find_all("script"): body_html.script.decompose()
                    new_body = body_html.decode()
                    new_id = hash(newUrl + new_body)
                    driver_for_button = temp_driver
                    if new_id != old_id:
                        button.setNewState(newUrl, new_body) 
                        print("new page " + driver_for_button.current_url )
                    else:
                      pass
        

         if input_elements != [] and found == False:        
            for e in input_elements:
             if found == False:                    
                location = e.location
                x= location.get('x')
                y= location.get('y')
                if x == button.getX() and y == button.getY():
                     #trovato il button nella pagina
                     #provo a cliccarlo
                    found = True
                    
                    temp_driver = driver_for_button
                    old_id = button.getId()
                    e.click()  
                    driver_for_button.refresh
                    newUrl = driver_for_button.current_url
                    body_soup = str(driver_for_button.find_element(By.TAG_NAME,'body').get_attribute("outerHTML"))
                    body_html= BeautifulSoup(body_soup, features="lxml")
                    for tag in body_html.find_all("script"): body_html.script.decompose()
                    new_body = body_html.decode()
                    driver_for_button = temp_driver
                    new_id = hash(newUrl + new_body)
                    if new_id != old_id:
                        button.setNewState(newUrl, new_body) 
                        print("new page " + driver_for_button.current_url )
                    else:
                        print("no new page " + driver_for_button.current_url) 
                        
    except:
       print("Button at page "+ url+ " not found")
    driver_for_button.quit()    
    return button

# Method for crawling a url at next level
def level_crawler(driver,url,body,tree, color,response):

    driver.get(url)

    temp_urls = set()
    id_node = hash(url + body)
    states[id_node] = url
    if "may" in response or "potentially" in response or "maybe" in response:
          print("done it")
          tree.add_node(id_node, click = url + "\n" + response ,image = alert, size = '50',color = color, hover = url, label = "S"+str(Count), label_color = color)
    else:
       tree.add_node(id_node, click = url + "\n" + response ,color = color, size = '20' ,hover = url, label = "S"+str(Count), label_color = color)
    
    print(url + "  " + str(Count) + " " + color)
    increment()

    current_url_domain = urlparse(url).netloc
    try:
            driver.switch_to.alert.dismiss()
    except EC.NoAlertPresentException:
            pass
    
    new_node = find_button (driver, node(id_node, url))
    
    for button in new_node.get_all_buttons():
      
      
      upgraded_button = test_button(button)
      new_state_from_button = upgraded_button.getNewState()
      if new_state_from_button != {} :
         new_link = list(new_state_from_button.keys()).pop(0)
         new_body = list(new_state_from_button.values()).pop(0)
         state_from_button = hash(new_link + new_body)               
         if state_from_button in states.keys() and new_link not in temp_urls:
        #azione
            id_action = hash(  id_node + state_from_button + random.randint(1, 100000))
            tree.add_node(id_action, click = new_link, color = color_button, hover = "click on button: " + new_link)
            tree.add_edge(id_node,id_action)                                          

        #   #se è uno stato già esplorato aggiungo solo l'edge
            tree.add_edge(id_action,state_from_button)
            temp_urls.add(new_link)            
            
         elif  state_from_button not in states.keys() and new_link not in temp_urls: 
            if  new_link in links_button_intern and  list(states.values()).count(new_link) >= 2:
                #se è uno stato apparentemente nuovo (nuovo hash) ma il link l'ho già visitato almeno 2 volte, allora mi 
                #ritrovo in un link in cui cambia solo il body
                temp_urls.add(new_link)
                all_link.append(new_link)

            elif (state_from_button not in states.keys() and list(states.values()).count(new_link) < 2 ):
                #azione
                id_action = hash(id_node +state_from_button + random.randint(1, 100000))
                tree.add_node(id_action, click = url,color = color_button, hover = "click on button: " + url, label_color = color_button)
                tree.add_edge(id_node,id_action)
             
                #stato
                new_node.add_link_button(new_link, new_body )
                links_button_intern.add(new_link)
                tree.add_edge(id_action,state_from_button)
                print("Intern from button - {} ".format(new_link))
   
    for anchor in driver.find_elements(By.TAG_NAME, 'a'):
        # Access requests via the `requests` attribute
        
        href = anchor.get_attribute("href")
        if(href != "" or href != None):
            href = urljoin(url, href)
            href_parsed = urlparse(href)
            href = href_parsed.scheme
            href += "://"
            href += href_parsed.netloc
            href += href_parsed.path
            final_parsed_href = urlparse(href)
            is_valid = bool(final_parsed_href.scheme) and bool(
                final_parsed_href.netloc)
           
            if is_valid:
                if current_url_domain not in href :
                    if test_status(driver, url) < 400:
                        print("Extern - {} ".format(href))
                        links_extern.add(href)
                        temp_driver.get(href)
                        body_soup = str(temp_driver.find_element(By.TAG_NAME,'body').get_attribute("outerHTML"))
                        body_html= BeautifulSoup(body_soup, features="lxml")
                        for tag in body_html.find_all("script"): body_html.script.decompose()
                        body_ext = body_html.decode()
                        id_node_ext = hash(href +body_ext)

                        #azione
                        id_action = hash(id_node +id_node_ext )
                        tree.add_node(id_action, click = href, color = color_ext_link, hover = "click on external link: " + href)
                        tree.add_edge(id_node,id_action)
             
                        #stato
                        tree.add_node(id_node_ext, click = href, lable = "Ext" + str( len(links_extern) + 1 ),color = color_states ,label = "S_E."+str(Count), label_color = 'blue')
                        tree.add_edge(id_action,id_node_ext)
                    else :
                        links_broken.add(href)
                        print("Broken - {} ".format(href) )

                #if current_url_domain in href and href not in links_intern:
                else : #current_url_domain in href     
                    if test_status(driver, url) < 400:                                    
                        temp_driver.get(href)
                        body_soup = str(temp_driver.find_element(By.TAG_NAME,'body').get_attribute("outerHTML"))
                        body_html= BeautifulSoup(body_soup, features="lxml")
                        for tag in body_html.find_all("script"): body_html.script.decompose()
                        body_int = body_html.decode()    
                        id_node_int = hash(href + body_int )
                        if  id_node_int in states.keys() and href not in temp_urls: 

                            #azione
                            id_action = hash(  id_node + id_node_int + random.randint(1, 100000))
                            #tree.add_node(id_action, click = href, color = color, hover = "click on internal link: " + href, label = "S_I"+str(Count), label_color = color)
                            tree.add_node(id_action, click = href, color = color_link, hover = "click on internal link: " + href)
                            tree.add_edge(id_node,id_action)                                          

                            #se è uno stato già esplorato aggiungo solo l'edge
                            tree.add_edge(id_action,id_node_int)
                            temp_urls.add(href)
                        
                        elif  id_node_int not in states.keys() and href not in temp_urls: 
                         if  href in links_intern and all_link.count(href) >= 2:

                            #se è uno stato apparentemente nuovo (nuovo hash) ma il link l'ho già visitato almeno 2 volte, allora mi 
                            #ritrovo in un link in cui cambia solo il body
                                temp_urls.add(href)
                                all_link.append(href)

                         elif (not id_node_int in states.keys() and list(states.values()).count(href) < 3 ):

                            #se è un nuovo stato lo aggiungo anche alle liste da esplorare
                            links_intern.add(href)
                            temp_urls.add(href)
                            new_node.add_link(href, body_int)
                            print("Intern - {} ".format(href))

                            #azione
                            id_action = hash(id_node + id_node_int + random.randint(1, 100000) )
                            tree.add_node(id_action, click = href, color = color_link, hover = "click on internal link: " + href)
                            tree.add_edge(id_node,id_action)                                          

                            #stato
                            tree.add_edge(id_action,id_node_int)
                            all_link.append(href)                        
                    else :
                        links_broken.add(href)
                        print("Broken - {} ".format(href))
    return new_node
  
   
def main():
      

    url = "http://php.testsparker.com/" #edit the URL for your scope or create an input handling parameter
  
    driver = webdriver.Chrome (options=chrome_options)
    driver.get(url)
    body_soup = str(driver.find_element(By.TAG_NAME,'body').get_attribute("outerHTML"))
    body_html= BeautifulSoup(body_soup, features="lxml")
    for tag in body_html.find_all("script"): body_html.script.decompose()
    body = body_html.decode()   
    queue = {(url,body) :'orange'}
    #Creazione grafico
    tree = nx.DiGraph()
    color_map.append('blue')
    links_intern.add(url)
    while len(queue) >0:
             
            popped = queue.popitem()
            if popped.__getitem__(1) == 'orange':
                color = 'orange'
            else :
                color = 'green'
            url = popped.__getitem__(0).__getitem__(0)
            body = popped.__getitem__(0).__getitem__(1)
            encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")   
            token_count = len(encoding.encode(body))
            if token_count < 4000:
                message = [{"role":"user", "content":"Is it possible that the following html code will require the user to enter or manipulate sensitive data? \
                            Does it contain an adequate privacy policy or a link to a privacy policy? \
                            In addition, does it require explicit consent from users before collecting data? \
                            Are there measures to protect personal data?  " + body }]
                try:
                                completion = openai.ChatCompletion.create(
                                model = "gpt-3.5-turbo",
                                max_tokens = 150,
                                messages =  message )
                                response = completion.choices[0].message.content
                except:
                                response = ("ChatGPT can't give an answer on this website")

            else:
                token_block = {}
                block = list()
                n = 1000
                for token in re.split(' |=|-|,', body) :      
                        block.append(token)     
                token_block = [block[i: i+n] for i in range(0, len(block),n)    ]   
                
                response = ""
                refurbed = ""
                body_splitted = list()
                for item in token_block:
                    for i in item:
                        refurbed = refurbed + " " + i
                    body_splitted.append(refurbed)
                    refurbed = ""
                
                
                message = "I am going to give you an html code splitted in different sections because is too long\
                                try to asnwer considering that is a part of the entire code. \
                                Could the following html code require to enter or manipulate sensitive data? \
                                Does it contain an adequate privacy policy or a link to a privacy policy? \
                                In addition, does it require explicit consent from users before collecting data? \
                                Are there measures to protect personal data? \
                                Does it include any cookie banner and eventually the possibility to choose which cookies to accept?\
                                Answer the question with short and precise answers: "
                for item in body_splitted:    
                    try:
                        completion = openai.ChatCompletion.create(
                        model = "gpt-3.5-turbo",
                        max_tokens = 130,
                        messages = [{"role":"user", "content": message + item }])
                        resp = completion.choices[0].message.content
                        response = response + "\n\n" +resp
                        time.sleep(10)
                    except:
                        response = ("ChatGPT can't give an answer on this website")

            new_node = level_crawler(driver,url,body,tree, color,response)
            for i in new_node.get_link_buttons():
                queue[i] = 'green'
            for j in new_node.get_links():
                queue [j] = 'orange'                      
    gv.d3(
        tree,
     show_node_label=True, node_label_data_source='label',node_hover_neighborhood=True,
     show_edge_label=True, edge_label_data_source='label', edge_curvature=0.2,
     graph_height=250, zoom_factor=1.0,
    ).display()

    driver.quit()   
    temp_driver.quit()
if __name__ == '__main__':
    main()



