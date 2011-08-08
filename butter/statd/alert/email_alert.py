'''
The email alert mechanism
'''
# Import python libs
import smtplib
import email.mime.text

def alert(host, tag, data):
    '''
    Send out an email message with information about the specified alert.
    '''
    if not __opts__.has_key['email.addrs']:
        return
    msg = email.mime.text.MIMEText(
            '{0}: {1} - {2}'.format(host, tag, str(data))
            )
    msg['Subject'] = 'Alert from {0}: {1}'.format(host, tag)
    msg['From'] = host
    smtp = smtplib.SMTP('localhost')
    smtp.sendmail(host, __opts__['email.addrs'], msg)
    smtp.quit()

