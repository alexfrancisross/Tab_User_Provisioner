import tableauserverclient as TSC
from datetime import datetime
import logging
from enum import Enum
import sys
import os
import snowflake.connector
import smtplib
from email import encoders
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate
import yaml
from yaml.loader import SafeLoader
from cryptoyaml import generate_key, CryptoYAML
CONFIG='settings.yaml'
CONFIG_ENCRYPTED = 'settings.yaml.aes'
KEY = '.\key' #encryption key should be set by 'CRYPTOYAML_SECRET' environment variable otherwise will try and read from local key file

# class syntax
class UpdateOperation(Enum):
    ADD = 'ADD'
    REMOVE = 'REMOVE'

#returns a list of users to provision (based on Snowflake tables)
def get_users_from_snowflake(table):
    user_list = []
    conn = snowflake.connector.connect(
        user=settings['SNOWFLAKE']['USER'],
        password=settings['SNOWFLAKE']['PASSWORD'],
        account=settings['SNOWFLAKE']['ACCOUNT'],
        warehouse=settings['SNOWFLAKE']['WAREHOUSE'],
        database=settings['SNOWFLAKE']['DATABASE'],
        schema=settings['SNOWFLAKE']['SCHEMA']
    )
    try:
        curs = conn.cursor()
        SQL = 'SELECT "Email Address" FROM "'+ table + '"'
        curs.execute(SQL)
    except Exception as e:
        logging.error('Error getting users from Snowflake using SQL: ' + SQL + str(e))

    try:
        emails = curs.fetchall()
        for email in emails:
            user_list.append(TSC.UserItem(email[0], 'Unlicensed'))
    except Exception as e:
        logging.error('Error creating user items list from Snowflake results: ' + str(e))

    logging.info('get_users_from_snowflake() completed with ' + str(len(user_list)) + ' user records')
    return user_list

def provision_users(user_list,auth_setting):
    error_flag=0
    with server.auth.sign_in(tableau_auth):

        # add the new user to the site
        for user in user_list:
            user.auth_setting=auth_setting
            try:
                newU = server.users.add(user)
                logging.info('added new user ' + newU.name + ' with role ' + newU.site_role)
            except Exception as e:
                logging.error('Error adding user: ' + user.name + ' ' + str(e))
                error_flag = 1
                continue
    return error_flag

def remove_users(user_list):
    error_flag=0
    with server.auth.sign_in(tableau_auth):
        for user in user_list:
            # add user to Group
            # get user to update using their username
            try:
                req_option = TSC.RequestOptions()
                req_option.filter.add(TSC.Filter(TSC.RequestOptions.Field.Name,
                                                 TSC.RequestOptions.Operator.Equals,
                                                 user.name))
                updateU = server.users.get(req_option)[0][0]

                server.users.remove(updateU.id)
                logging.info('removed user ' + updateU.name + ' with role ' + updateU.site_role)
            except Exception as e:
                logging.error('Error removing user: ' + user.name + ' ' + str(e))
                error_flag = 1
                continue
    return error_flag

def update_user_group_members(user_list, update_operation, glsi_group_name):
    error_flag = 0
    with server.auth.sign_in(tableau_auth):
        # get
        req_option = TSC.RequestOptions()
        req_option.filter.add(TSC.Filter(TSC.RequestOptions.Field.Name,
                                         TSC.RequestOptions.Operator.Equals,
                                         glsi_group_name))

        try:
            group = server.groups.get(req_option)[0][0]
        except Exception as e:
            logging.error('Error getting group: ' + glsi_group_name + ' ' + str(e))

        for user in user_list:
            # add user to Group
            # get user to update using their username
            try:
                req_option = TSC.RequestOptions()
                req_option.filter.add(TSC.Filter(TSC.RequestOptions.Field.Name,
                                                 TSC.RequestOptions.Operator.Equals,
                                                 user.name))
                updateU = server.users.get(req_option)[0][0]

                if update_operation == UpdateOperation.ADD:
                    server.groups.add_user(group,updateU.id)
                    logging.info('added user ' + updateU.name + ' to Group ' + group.name)

                if update_operation == UpdateOperation.REMOVE:
                    server.groups.remove_user(group, updateU.id)
                    logging.info('removed user ' + updateU.name + ' from Group ' + group.name)

            except Exception as e:
                    logging.error('Error with operation ' + str(update_operation.value) + ' user: ' + user.name + ' group: ' + group.name + str(e))
                    error_flag=1
                    continue
    return error_flag

def set_users_siteRole(user_list,siteRole):
    error_flag=0
    with server.auth.sign_in(tableau_auth):

        for user in user_list:
            # get user to remove using their username
            try:
                #get user to update using their username
                req_option = TSC.RequestOptions()
                req_option.filter.add(TSC.Filter(TSC.RequestOptions.Field.Name,
                                                 TSC.RequestOptions.Operator.Equals,
                                                 user.name))
                updateU = server.users.get(req_option)[0][0]

                # modify user info
                updateU.site_role = siteRole

                updateU = server.users.update(updateU)
                logging.info('updated user ' + updateU.name + ' with role ' + updateU.site_role)
            except Exception as e:
                logging.error('Error updating site role for user ' + user.name + ' with role ' + siteRole + str(e))
                error_flag=1
                continue
    return error_flag

def initialise_logging(logdir,log_retention):
    arr = os.listdir(logdir)
    for filename in arr:
        try:
            logdate=datetime.strptime((filename[:10]), '%d-%m-%Y')
            if (datetime.today() - logdate).days > log_retention:
                os.remove(logdir + filename)
        except Exception as e:
            logging.error('Error removing logfile: ' + filename + str(e))
            continue

    logger = logging.getLogger()
    logger.setLevel(settings['APP']['LOGGING_LEVEL'])
    formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s',
                                  '%d-%m-%Y %H:%M:%S')
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.DEBUG)
    stdout_handler.setFormatter(formatter)
    logfile = str(settings['APP']['LOGDIR'] + datetime.now().strftime("%d-%m-%Y-%H.%M.%S")) + '.log'
    file_handler = logging.FileHandler(logfile)
    file_handler.setLevel(settings['APP']['LOGGING_LEVEL'])
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(stdout_handler)

    return logfile

def send_email(user, pwd, from_email, recipient, subject, body, file_to_attach):
# create the message
    msg = MIMEMultipart()
    msg["From"] = from_email
    msg["Subject"] = subject
    msg["Date"] = formatdate(localtime=True)
    filename = os.path.basename(file_to_attach)
    header = 'Content-Disposition', 'attachment; filename="%s"' % filename
    if body:
        msg.attach( MIMEText(body) )
    msg["To"] = ', '.join(recipient)
    attachment = MIMEBase('application', "octet-stream")
    try:
        with open(file_to_attach, "rb") as fh:
            data = fh.read()
        attachment.set_payload( data )
        encoders.encode_base64(attachment)
        attachment.add_header(*header)
        msg.attach(attachment)
    except IOError:
        msg = "Error opening attachment file %s" % file_to_attach
        print(msg)
        sys.exit(1)
    try:
        server = smtplib.SMTP(settings['EMAIL']['EMAIL_HOST'], settings['EMAIL']['EMAIL_PORT'])
        server.ehlo()
        server.starttls()
        server.login(user, pwd)
        server.sendmail(from_email, recipient, msg.as_string())
        server.quit()
        print('successfully sent email with error log file')
    except Exception as e:
        print("failed to send email with error log file" + str(e))

def main():
    user_list_to_provision = get_users_from_snowflake(settings['SNOWFLAKE']['JOINERS_TABLE'])
    user_list_to_unlicense = get_users_from_snowflake(settings['SNOWFLAKE']['LEAVERS_TABLE'])
    error_flag = 0
    if (settings['TASKS']['PROVISION_USERS'] == True):
        ret = provision_users(user_list_to_provision,settings['TABLEAU']['AUTH_SETTING'])
        if (ret!=0):
            error_flag=1
    if(settings['TASKS']['ADD_USER_GROUP_MEMBERS'] == True):
        ret = update_user_group_members(user_list_to_provision, UpdateOperation.ADD, settings['TABLEAU']['GLSI_GROUP_NAME'])
        if (ret!=0):
            error_flag=1
    if(settings['TASKS']['SET_USERS_SITEROLE_AS_VIEWER'] == True):
        ret = set_users_siteRole(user_list_to_provision, TSC.UserItem.Roles.Viewer)
        if (ret!=0):
            error_flag=1
    if(settings['TASKS']['REMOVE_USER_GROUP_MEMBERS'] == True):
        ret = update_user_group_members(user_list_to_unlicense, UpdateOperation.REMOVE, settings['TABLEAU']['GLSI_GROUP_NAME'])
        if (ret!=0):
            error_flag=1
    if(settings['TASKS']['SET_USERS_SITEROLE_AS_UNLICENSED'] == True):
        ret = set_users_siteRole(user_list_to_unlicense, TSC.UserItem.Roles.Unlicensed)
        if (ret!=0):
            error_flag=1
    if(settings['TASKS']['ADD_UNLICENSED_USER_GROUP_MEMBERS'] == True):
        ret = update_user_group_members(user_list_to_unlicense, UpdateOperation.ADD, settings['TABLEAU']['GLSI_GROUP_NAME'])
        if (ret!=0):
            error_flag=1
    if(settings['TASKS']['REMOVE_USERS'] == True):
        ret = remove_users(user_list_to_unlicense)
        if (ret!=0):
            error_flag=1
    return error_flag

def read_yaml():
    #if encrypted yaml file is present then read it
    try:
        if os.getenv('CRYPTOYAML_SECRET'):
            key = os.getenv('CRYPTOYAML_SECRET')
        else:
            key = KEY
        if (os.path.exists(CONFIG_ENCRYPTED)):
            read = CryptoYAML(CONFIG_ENCRYPTED, keyfile=key)
            return read.data

        #else read clear text yaml file
        else:
            with open(CONFIG) as f:
                data = yaml.load(f, Loader=SafeLoader)
            return data
    except Exception as e:
        print("failed to read yaml file " + str(e))

#MAIN PROGRAM
settings = read_yaml()

if settings: # if seeting read correctly
    tableau_auth = TSC.PersonalAccessTokenAuth(settings['TABLEAU']['TABLEAU_USER'],
                                              settings['TABLEAU']['TABLEAU_PAT'],
                                              settings['TABLEAU']['TABLEAU_SITE'])
    server= TSC.Server(settings['TABLEAU']['TABLEAU_SERVER'])
    server.version = settings['TABLEAU']['TABLEAU_SERVER_VERSION']
    logfile = initialise_logging(settings['APP']['LOGDIR'], settings['APP']['LOG_RETENTION'])

    ret=main()

    if (ret==1):
        send_email(settings['EMAIL']['EMAIL_HOST_USER'], settings['EMAIL']['EMAIL_HOST_PASSWORD'], settings['EMAIL']['EMAIL_FROM'], settings['EMAIL']['EMAIL_TO'], settings['EMAIL']['EMAIL_SUBJECT'], settings['EMAIL']['EMAIL_BODY'], logfile)

