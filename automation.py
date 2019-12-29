from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, WebDriverException
import time
import re
import pandas as pd
import json
import pymongo
import datetime
import math
from random import randint

def catch_message_pop_up(driver):
    try:
        close_butt = driver.find_element_by_xpath("//aside[@id='msg-overlay']//button[@class='msg-overlay-bubble-header__control js-msg-close']")
        close_butt.click()
    except:
        pass
        
#check if you can send a request to the person
def check_if_can_send_request(driver):
    try:
        driver.find_element_by_css_selector('.pv-s-profile-actions.pv-s-profile-actions--connect.button-primary-large.mr2.mt2.pv-s-profile-actions--pending')
        return False
    except NoSuchElementException:
        pass
    try:
        driver.find_element_by_css_selector('.pv-s-profile-actions.pv-s-profile-actions--connect.button-primary-large.mr2.mt2')
        return True
    except NoSuchElementException:
        pass

    try:
        driver.find_element_by_css_selector('.pv-s-profile-actions__overflow-toggle.pv-top-card-section__inline-overflow-button.button-secondary-large-muted.mt2').click()
        driver.find_element_by_css_selector('.pv-s-profile-actions.pv-s-profile-actions--connect.pv-s-profile-actions__overflow-button.full-width.text-align-left')
        driver.find_element_by_css_selector('.pv-s-profile-actions__overflow-toggle.pv-top-card-section__inline-overflow-button.button-secondary-large-muted.mt2').click()
        return True
    except (NoSuchElementException, WebDriverException) as e:
        if e == WebDriverException:
            catch_message_pop_up(driver)
            check_if_can_send_request(driver)
        else:
            return False

def get_connection(driver):
    try:
        pending = driver.find_element_by_class_name('pv-s-profile-actions--pending')
        return True
    except:
        try:
            connection_type=driver.find_element_by_xpath('//span[@class="dist-value"]')
            print('DID IGET HERE')
            if connection_type.text == "1st":
                return True
        except:
            return False    
        
def send_connection_request(driver, contact, contacts, collection):
    #connect
    driver.execute_script("window.scrollTo(0, 0);")

    print('pass')
    print('/sales/people/' in driver.current_url)
    if '/sales/people/' in driver.current_url:
        try:
            elm = driver.find_element_by_class_name("profile-topcard-actions")
            elm.find_elements_by_tag_name("artdeco-dropdown")[1].click()
            time.sleep(1)
            if elm.find_elements_by_tag_name("li")[2].text == "Copy LinkedIn.com URL":
                print("Copy LinkedIn.com URL")
                elm.find_elements_by_tag_name("li")[1].click()
            else:
                elm.find_elements_by_tag_name("li")[2].click()
            driver.switch_to_window(driver.window_handles[-1])
            contacts.update_one({'_id': contact['_id']}, {
                "$set": { 
                    'linkedinUrl': driver.current_url,
                    'linkedInUsername': driver.current_url.split('/')[4]
                }
            }, upsert=False)
        except:
            print('try again')

    else:
        try:
            try:
                try:
                    driver.find_element_by_css_selector('.pv-top-card-section__inline-overflow-button').click()
                    driver.find_element_by_css_selector('.pv-s-profile-actions.pv-s-profile-actions--connect').click()
                except:
                    driver.find_element_by_css_selector('.pv-s-profile-actions__overflow').click()
                    if driver.find_element_by_css_selector('.pv-s-profile-actions.pv-s-profile-actions--connect').text.split('\n')[0] == "Pending":
                        print('PENDING')
                        contacts.update_one({'_id': contact['_id']}, {
                                    "$set": { 
                                        "requestSent": True,
                                        'requestSentDate' : datetime.datetime.now()
                                    }
                        }, upsert=False)
                    else:
                        driver.find_element_by_css_selector('.pv-s-profile-actions.pv-s-profile-actions--connect').click() 
            except:
                if driver.find_element_by_css_selector('.pv-s-profile-actions.pv-s-profile-actions--connect').text.split('\n')[0] == "Pending":
                    print('PENDING')
                    contacts.update_one({'_id': contact['_id']}, {
                                "$set": { 
                                    "requestSent": True,
                                    'requestSentDate' : datetime.datetime.now()
                                }
                    }, upsert=False)
                else:

                    driver.find_element_by_css_selector('.pv-s-profile-actions.pv-s-profile-actions--connect').click() 

        except (NoSuchElementException, WebDriverException) as e:
            if e == WebDriverException:
                catch_message_pop_up(driver)
                print('failing')
                send_connection_request(driver, contact, contacts, collection)
            else:
                pass
            
        try:
            driver.find_element_by_css_selector('.artdeco-button--secondary.artdeco-button--3.mr1').click()
        except WebDriverException:
            catch_message_pop_up(driver)
            pass
        
        #make a custom message
        try:
            email = driver.find_element_by_id('email')
            email.send_keys(contact['email'])
        except:
            print('no email warning')

        time.sleep(1)
        # send request with message
        try:
            note = driver.find_element_by_id("custom-message")
            note.send_keys(contact["championText"])
            if note.get_attribute('value') == contact["championText"]:
                driver.find_element_by_css_selector('.artdeco-button.artdeco-button--3.ml1').click()
                contacts.update_one({'_id': contact['_id']}, {
                    "$set": { "requestSent": True,
                            'requestSentDate' : datetime.datetime.now(),
                            'linkedinUrl': driver.current_url,
                            'linkedInUsername': driver.current_url.split('/')[4]
                            }
                }, upsert=False)

                driver.find_element_by_css_selector('.artdeco-button.artdeco-button--3.ml1').click()
                contacts.update_one({'_id': contact['_id']}, {
                    "$set": { "requestSent": True,
                            'requestSentDate' : datetime.datetime.now(),
                            'linkedinUrl': driver.current_url,
                            'linkedInUsername': driver.current_url.split('/')[4]
                            }
                }, upsert=False)
            else:
                pass
        except WebDriverException as e:
            catch_message_pop_up(driver)
            pass

def start_connection_requests(owner, password, db, sending_limit, inbox_limit):
    options = webdriver.ChromeOptions()

    # set the window size
    options.add_argument('window-size=1200x600')

    # initialize the driver
    driver = webdriver.Chrome(chrome_options=options, executable_path="/usr/local/bin/chromedriver")

    # https://www.linkedin.com/uas/login
    driver.get('https://www.linkedin.com/uas/login')

    try:
        username_ele = driver.find_element_by_id("session_key-login") 
    except NoSuchElementException:
        username_ele = driver.find_element_by_id("username")
        password_ele = driver.find_element_by_id("password")
        button_ele = driver.find_element_by_class_name("btn__primary--large")
    else:
        password_ele = driver.find_element_by_id("session_password-login") 
        button_ele = driver.find_element_by_name("signin")
    username_ele.send_keys(owner) 
    password_ele.send_keys(password) 
    button_ele.click()
    print("Logged In")
    
    
    contacts = db['Contacts']
    count = 0

    for contact in contacts.find({"requestSent": False, 'owner': owner, 'badLinkedinUrl': False}):
        # stop sending requests if we are over the limit
        if count == sending_limit:
        	break
        
        # if contact["Connection"] != "1st":
        print(contact['linkedinUrl'])
        driver.get(contact['linkedinUrl'])
        time.sleep(2)
        
        if driver.current_url != "https://www.linkedin.com/in/unavailable/":

            if get_connection(driver):
                contacts.update_one({'_id': contact['_id']}, 
                                    { 
                                        "$set": { 
                                        'connection' : True,
                                        "connectionDate": datetime.datetime.now(),
                                        "sequenceOver": True,
                                        "requestSent": True
                                        }}, 
                                    upsert=False)
            else:
                count = count + 1
                print(count)
                print(contact['linkedinUrl'])
                time.sleep(1)

                print('send request')

                try:
                    if driver.find_element_by_css_selector(".pv-s-profile-actions--connect").text == "Pending":
                        contacts.update_one({'_id': contact['_id']}, 
                                            { 
                                                "$set": { 
                                                'connection' : True,
                                                "connectionDate": datetime.datetime.now(),
                                                "sequenceOver": True,
                                                "requestSent": True
                                                }}, 
                                            upsert=False)
                    else:
                       send_connection_request(driver, contact, contacts, owner) 
                except:
                    send_connection_request(driver, contact, contacts, owner)

        else:
            print("A link has gone bad")
            contacts.update_one({'_id': contact['_id']}, 
                                { "$set": { 
                                    'badLinkedinUrl' : True
                                           }}, 
                                upsert=False)
        

    print('now checking inbox')

    time.sleep(2)
    driver.get("https://www.linkedin.com/")
    # click into messages
    driver.find_element_by_id('messaging-tab-icon').click()

#     looks for replies
    reply_looker = []

    for reply in contacts.find({ "replied": False, "sequenceOver":False, "owner": owner }):
        reply_looker.append(reply)

    df = pd.DataFrame(reply_looker)

    if len(df)>0:
        usernames_reply = df.linkedInUsername.tolist()
    else:
        usernames_reply = []
    
    print("User NAME replies")
    print(usernames_reply)
    
#     looks for new 'connectionn accepted'
    items = []
    for item in contacts.find({ "requestSent":True, "owner": owner}):
        items.append(item)

    df = pd.DataFrame(items)

    if len(df)>0:
        usernames = df.linkedInUsername.tolist()
    else:
        usernames = []

    print("There are {} possible new connections".format(len(usernames)))
    print("There are {} possible repliers".format(len(usernames_reply)))

    sales_nav_hap = False
    job_recruiter_hap = False
    job_post_hap = False
    time.sleep(3)

    try:
        driver.find_element_by_class_name('msg-form__send-toggle').click()
        card = driver.find_element_by_class_name("msg-form__hovercard")
        for elm in card.find_elements_by_class_name('t-bold'):
            elm.click()
    except:
        print('do not send connection requests')

    count = 1
    while count <= inbox_limit:
        print(count)
        try:
            job_recruiter = driver.find_element_by_xpath("//li[@class='msg-premium-mailboxes__mailbox msg-premium-mailboxes__mailbox--recruiter_messages']")
            if job_recruiter_hap == False:
                count +=1
            job_recruiter_hap = True
        except:
            pass
        try:
            job_post = driver.find_element_by_xpath("//li[@class='msg-premium-mailboxes__mailbox msg-premium-mailboxes__mailbox--job_post_messages']")
            if job_post_hap == False:
                count+=1
            job_post_hap = True
        except:
            pass
        try:
            sales_nav = driver.find_element_by_xpath("//li[@class='msg-premium-mailboxes__mailbox msg-premium-mailboxes__mailbox--sales_navigator_messages']")
            if sales_nav_hap == False:
                count+=1
            sales_nav_hap = True
        except:
            pass

        recent = driver.find_element_by_xpath("//ul[@class='msg-conversations-container__conversations-list list-style-none ember-view']/li[%s]" % count )
        driver.execute_script("arguments[0].scrollIntoView();", recent)
        time.sleep(1)
        try:
            recent.click()
        except:
            time.sleep(2)
            driver.execute_script("arguments[0].scrollIntoView();", recent)
        username = ''
        try:
            link = driver.find_element_by_class_name('msg-thread__link-to-profile')
            username = link.get_attribute('href').split('/')[4]
        except:
            username = 'sp'
        print('coolUsername')
        print(username)
        if username in usernames:
            print(username)
            contacts.update_one({ "linkedInUsername": username }, {
                "$set": {
                        "connection": True,
                        "connectionDate": datetime.datetime.now(),
                        "threadUrl": driver.current_url
                    }
            }, upsert = False)
        
        if (username in usernames_reply or username in usernames):
            target_datetime = ""
            with_weekday = False
            print("messages from ", username)
            messages = []

            weekdays = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY", "TODAY"]

            time.sleep(2)

            msg_names = driver.find_elements_by_class_name("msg-s-message-group__name")
            print(msg_names)
            msg_texts = driver.find_elements_by_class_name("msg-s-event-listitem__body")
            print(msg_texts)
            for i, name in enumerate(msg_names):
                messages.append({
                    "name": name.text,
                    "text": msg_texts[i].text
                })

            replied = False

            print(messages)

            my_name = messages[0]['name']

            for message in messages:
                if message['name'] != my_name:
                    replied = True

            print("Replied: ", replied)
            contacts.update_one({ "linkedInUsername": username }, {
                "$set": {
                    'messages': messages,
                    'replied': replied,
                    'sequenceOver': replied,
                    "threadUrl": driver.current_url
                }
            }, upsert=False) 
            
        count += 1

    documents = []
    for doc in contacts.find({"sequenceOver": False, "connection": True, "owner": owner, "threadUrl": {"$exists":True} }):
        documents.append(doc)


    print("There are {} that have connected but haven't replied.".format(len(documents)))

    for doc in documents:
        print(doc["_id"])
        print(doc['threadUrl'])

        driver.get(doc['threadUrl'])

        if doc['firstFollowUpDate'] == "":
            if doc["connectionDate"] == "":
                time_between_cr_and_now = datetime.datetime.now() - doc["requestSentDate"]
                doc['connectionDate'] = doc["requestSentDate"]
            else: 
                time_between_cr_and_now = datetime.datetime.now() - doc["connectionDate"]
            if doc['firstFollowUpSent'] is False and time_between_cr_and_now.days >= 0 and doc['replied'] is False and 'messages' in doc and len(doc['messages']) < 2:
                print('SECOND MESSAGE')
                try:
                    driver.find_element_by_class_name("msg-form__contenteditable").send_keys(doc['firstFollowUpText'])
                    contacts.update_one({'_id': doc['_id']}, {
                        "$set": {
                            'firstFollowUpDate': datetime.datetime.now(),
                            'firstFollowUpSent': True
                        }
                    }, upsert=False)
                    driver.find_element_by_class_name("msg-form__send-button").click()

                except:
                    print('No more message thread')

        elif doc['secondFollowUpDate'] == "":
                time_between_third_and_now = datetime.datetime.now() - doc['firstFollowUpDate']
                print(time_between_third_and_now.days)
                if doc['secondFollowUpSent'] is False and time_between_third_and_now.days > 1 and doc['replied'] is False and 'messages' in doc and len(doc['messages']) >= 2:
                    print("THIRD MESSAGE")
                    try:
                        driver.find_element_by_class_name("msg-form__contenteditable").send_keys(doc['secondFollowUpText'])
                        contacts.update_one({'_id': doc['_id']}, {
                            "$set": {
                                'secondFollowUpDate': datetime.datetime.now(),
                                'secondFollowUpSent': True
                            }
                        }, upsert=False)
                        driver.find_element_by_class_name("msg-form__send-button").click()
                    except:
                        print('No More Message Thread')

        else:
            print('no follow ups to send')
            contacts.update_one({'_id': doc['_id']}, {
                "$set": {
                    "sequenceOver": True
                }
            }, upsert=False)